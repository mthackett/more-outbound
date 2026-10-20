from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from pipeline.domain.instance_loader import load_demo_config
from pipeline.domain.outreach_metrics import calculate_metrics, historical_cohorts, conversion_funnel
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage


class TestOutreachDemo(unittest.TestCase):
    def setUp(self):
        self.cfg = load_demo_config()
        self.seed = json.loads((Path(__file__).resolve().parents[2] / 'examples/fixtures/demo_prospects.json').read_text())

    def test_fixture_exact_historical_counts_and_rates(self):
        store = MemoryRecordStorage(self.cfg, self.seed)
        records = store.list_records()
        self.assertEqual(len(records), 40)
        c, _ = historical_cohorts(records, self.cfg)
        self.assertEqual({key: len(value) for key, value in c.items()},
                         {'total': 40, 'contacted': 30, 'replied': 17, 'meeting': 10, 'opportunity': 4})
        metrics = calculate_metrics(records, self.cfg)
        self.assertAlmostEqual(metrics['meeting_booking_rate']['value'], 100 * 10/30)
        self.assertAlmostEqual(metrics['reply_rate']['value'], 100 * 17/30)
        self.assertAlmostEqual(metrics['reply_to_meeting_rate']['value'], 100 * 10/17)
        self.assertEqual(metrics['active']['value'], 32)
        self.assertEqual(metrics['pipeline_value']['value'], 1128000)
        self.assertEqual([r['Count'] for r in conversion_funnel(records, self.cfg)], [40, 30, 17, 10, 4])

    def test_missing_malformed_duplicate_and_canceled_evidence(self):
        records = [
            {'id': 'one', 'stage_id': 'opportunity_created', 'stage_history': [{'stage_id': 'contacted'}, {'stage_id': 'meeting_booked'}]},
            {'id': 'one', 'activities': [{'kind': 'replied'}, {'kind': 'meeting'}]},
            {'id': 'two', 'stage_id': 'disqualified', 'stage_history': 'bad json', 'activities': [{'kind': 'meeting_canceled'}]},
            {'id': 'three', 'stage_id': 'replied', 'stage_history': {'bad': True}, 'activities': ['bad', None]},
            {'stage_id': 'contacted'},
        ]
        c, _ = historical_cohorts(records, self.cfg)
        self.assertEqual(len(c['total']), 3)
        self.assertEqual(c['meeting'], {'one'})
        self.assertEqual(c['contacted'], {'one'})
        metrics = calculate_metrics(records, self.cfg)
        self.assertEqual(metrics['meeting_booking_rate']['value'], 100)
        self.assertEqual(metrics['reply_to_meeting_rate']['value'], 50)
        empty = calculate_metrics([], self.cfg)
        self.assertIsNone(empty['reply_rate']['value'])
        self.assertEqual(empty['total']['value'], 0)

    def test_isolation_reset_copy_boundaries_and_atomic_updates(self):
        a, b = MemoryRecordStorage(self.cfg, self.seed), MemoryRecordStorage(self.cfg, self.seed)
        original = [r.model_dump() for r in b.list_records()]
        def edit(store, title):
            store.update('demo-001', {'company': title}, 'meeting_booked')
            store.add_activity('demo-001', 'contacted', 'Synthetic contact')
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda pair: edit(*pair), [(a, 'Session A'), (b, 'Session B')]))
        self.assertEqual(a.list_records()[0].fields['company'], 'Session A')
        self.assertEqual(b.list_records()[0].fields['company'], 'Session B')
        a.reset()
        self.assertEqual([r.model_dump() for r in a.list_records()], original)
        self.assertEqual(b.list_records()[0].fields['company'], 'Session B')
        exposed = a.list_records()[0]
        exposed.fields['company'] = 'External mutation'
        self.assertNotEqual(a.list_records()[0].fields['company'], 'External mutation')
        with self.assertRaises(ValueError):
            a.update('demo-001', {'acv': -1}, 'replied')
        self.assertEqual(a.list_records()[0].stage_id, 'identified')
        with self.assertRaises(ValueError):
            a.update('demo-001', {}, 'unknown')

    def test_progression_retains_booking_and_notes_do_not_invent_reply(self):
        store = MemoryRecordStorage(self.cfg)
        record = store.create({'company': 'Fictional', 'contact': 'Demo'}, 'contacted')
        store.update(record.id, {}, 'meeting_booked')
        store.update(record.id, {}, 'opportunity_created')
        store.add_activity(record.id, 'meeting_canceled', 'Scheduling change')
        store.add_activity(record.id, 'note', 'The word replied is not a reply event')
        metrics = calculate_metrics(store.list_records(), self.cfg)
        self.assertEqual(metrics['meeting_booking_rate']['value'], 100)
        self.assertEqual(metrics['reply_rate']['value'], 0)
        self.assertIsNone(metrics['reply_to_meeting_rate']['value'])

    def test_two_streamlit_sessions_and_displayed_fixture_metrics(self):
        app_path = Path(__file__).resolve().parents[2] / 'adapters/primary/app.py'
        with patch.dict(os.environ, {'PIPELINE_MODE': 'demo', 'DEMO_MODE': 'false'}):
            a = AppTest.from_file(str(app_path), default_timeout=20).run()
            b = AppTest.from_file(str(app_path), default_timeout=20).run()
            self.assertFalse(a.exception)
            self.assertFalse(b.exception)
            displayed = {m.label: m.value for m in a.metric}
            self.assertEqual([displayed[k] for k in ('Meeting Booking Rate', 'Reply Rate', 'Reply-to-Meeting Rate')],
                             ['33.3%', '56.7%', '58.8%'])
            a.session_state['_demo_store'].update('demo-001', {'company': 'Session A'}, 'contacted')
            a.run()
            b.run()
            self.assertNotEqual(b.session_state['_demo_store'].list_records()[0].fields['company'], 'Session A')
            a.session_state['_demo_store'].reset()
            a.run()
            self.assertEqual(a.session_state['_demo_store'].list_records()[0].fields['company'], self.seed[0]['fields']['company'])
