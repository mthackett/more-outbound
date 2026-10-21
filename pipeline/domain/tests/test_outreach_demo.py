from concurrent.futures import ThreadPoolExecutor
import datetime
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
            self.assertEqual([displayed[k] for k in ('Booking Rate', 'Reply Rate', 'Reply-to-Meeting')],
                             ['33.3%', '56.7%', '58.8%'])
            a.session_state['_demo_store'].update('demo-001', {'company': 'Session A'}, 'contacted')
            a.run()
            b.run()
            self.assertNotEqual(b.session_state['_demo_store'].list_records()[0].fields['company'], 'Session A')
            a.session_state['_demo_store'].reset()
            a.run()
            self.assertEqual(a.session_state['_demo_store'].list_records()[0].fields['company'], self.seed[0]['fields']['company'])

    def test_action_lifecycle_complete_reschedule_schedule_and_activity(self):
        store = MemoryRecordStorage(self.cfg, self.seed)
        records = store.list_records()
        rec = next(r for r in records if r.fields.get('next_action_date') == store.reference.date.isoformat())
        self.assertIsNotNone(rec.current_action)
        self.assertEqual(rec.current_action.status, 'open')

        # Test completing action
        updated = store.complete_action(rec.id, note='Completed initial discovery call')
        self.assertIsNone(updated.current_action)
        self.assertIsNotNone(updated.latest_action)
        self.assertEqual(updated.latest_action.status, 'completed')
        self.assertIsNotNone(updated.latest_action.completed_at)
        self.assertIsNone(updated.fields.get('next_action_date'))
        self.assertIn('Completed action:', updated.activities[-1].text)
        self.assertIn('Completed initial discovery call', updated.activities[-1].text)

        # Test scheduling next action
        future_date = (store.reference.date + datetime.timedelta(days=4)).isoformat()
        scheduled = store.schedule_action(rec.id, 'Send security audit pack', future_date)
        self.assertIsNotNone(scheduled.current_action)
        self.assertEqual(scheduled.current_action.status, 'open')
        self.assertEqual(scheduled.current_action.description, 'Send security audit pack')
        self.assertEqual(scheduled.current_action.due_date, future_date)
        self.assertEqual(scheduled.fields['next_action_date'], future_date)
        self.assertIn('Scheduled next action for', scheduled.activities[-1].text)

        # Test rescheduling action
        resched_date = (store.reference.date + datetime.timedelta(days=7)).isoformat()
        rescheduled = store.reschedule_action(rec.id, resched_date, reason='Prospect delayed meeting')
        self.assertEqual(rescheduled.current_action.due_date, resched_date)
        self.assertEqual(rescheduled.fields['next_action_date'], resched_date)
        self.assertIn('Rescheduled action to', rescheduled.activities[-1].text)
        self.assertIn('Prospect delayed meeting', rescheduled.activities[-1].text)

        # Test activity logging without completing action
        store.add_activity(rec.id, 'call', 'Brief check-in call', complete_action=False)
        rec_check = store.list_records()
        current_rec = next(r for r in rec_check if r.id == rec.id)
        self.assertIsNotNone(current_rec.current_action)
        self.assertEqual(current_rec.current_action.status, 'open')
        self.assertEqual(current_rec.activities[-1].text, 'Brief check-in call')

        # Test activity logging with explicit complete_action=True
        store.add_activity(rec.id, 'email', 'Follow-up email with final pricing', complete_action=True)
        rec_check2 = store.list_records()
        current_rec2 = next(r for r in rec_check2 if r.id == rec.id)
        self.assertIsNone(current_rec2.current_action)
        self.assertIsNotNone(current_rec2.latest_action)
        self.assertEqual(current_rec2.latest_action.status, 'completed')
        self.assertIsNone(current_rec2.fields.get('next_action_date'))
        self.assertIn('Completed action:', current_rec2.activities[-1].text)

    def test_workload_rebalance_and_daily_priorities(self):
        store = MemoryRecordStorage(self.cfg, self.seed)
        records = store.list_records()
        ref_today = store.reference.date.isoformat()
        active_stage_ids = {s.id for s in self.cfg.stages if s.active}

        due_today = [r for r in records if r.stage_id in active_stage_ids and r.current_action and r.current_action.status == 'open' and r.current_action.due_date == ref_today]
        overdue = [r for r in records if r.stage_id in active_stage_ids and r.current_action and r.current_action.status == 'open' and r.current_action.due_date and r.current_action.due_date < ref_today]
        awaiting_reply = [r for r in records if r.stage_id == 'replied']
        future_sched = [r for r in records if r.stage_id in active_stage_ids and r.current_action and r.current_action.status == 'open' and r.current_action.due_date and r.current_action.due_date > ref_today]
        no_action = [r for r in records if not (r.current_action and r.current_action.status == 'open')]

        # Verify rebalance distribution targets:
        # 5-7 due today, 2-3 overdue, 5-8 awaiting reply, 12-16 future scheduled
        self.assertTrue(5 <= len(due_today) <= 7, f"Due today count {len(due_today)} not in 5-7")
        self.assertTrue(2 <= len(overdue) <= 3, f"Overdue count {len(overdue)} not in 2-3")
        self.assertTrue(5 <= len(awaiting_reply) <= 8, f"Awaiting reply count {len(awaiting_reply)} not in 5-8")
        self.assertTrue(12 <= len(future_sched) <= 16, f"Future scheduled count {len(future_sched)} not in 12-16")
        self.assertEqual(len(due_today) + len(overdue) + len(future_sched) + len(no_action), 40)

        # Stage change preserves outstanding action
        target = due_today[0]
        initial_action_desc = target.current_action.description
        initial_action_due = target.current_action.due_date
        store.update(target.id, {}, 'contacted')
        updated = next(r for r in store.list_records() if r.id == target.id)
        self.assertEqual(updated.stage_id, 'contacted')
        self.assertIsNotNone(updated.current_action)
        self.assertEqual(updated.current_action.description, initial_action_desc)
        self.assertEqual(updated.current_action.due_date, initial_action_due)
        self.assertEqual(updated.current_action.status, 'open')
