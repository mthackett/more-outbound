"""Synthetic fixture invariants and trailing-period trend math."""
from datetime import date, timezone
import json
from pathlib import Path
import re
import unittest

from pipeline.domain.demo_dates import DemoReference, local_date
from pipeline.domain.instance_loader import load_demo_config
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage
from pipeline.domain.outreach_metrics import trailing_periods, weekly_series, first_milestone_dates

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / 'pipeline' / 'examples' / 'fixtures'
REF = DemoReference(date(2026, 10, 21), timezone.utc)
WORKSPACES = [
    ('demo_sales_rep.json', 'demo_prospects.json', 'Sarah Jenkins'),
    ('demo_b2b_services.json', 'demo_b2b_services.json', 'Alex Rivera'),
]


def load(config_name, fixture_name):
    cfg = load_demo_config(ROOT / 'config' / config_name)
    seed = json.loads((FIXTURES / fixture_name).read_text(encoding='utf-8'))
    return cfg, seed, MemoryRecordStorage(cfg, seed, reference=REF)


class TestDemoFixtures(unittest.TestCase):
    def test_pii_conventions(self):
        for config_name, fixture_name, _ in WORKSPACES:
            _, seed, _ = load(config_name, fixture_name)
            for row in seed:
                f = row['fields']
                self.assertRegex(f['phone'], r'^\(\d{3}\) 555-01\d\d$', row['id'])
                self.assertRegex(f['email'], r'^[a-z.-]+@[a-z0-9]+\.example\.com$', row['id'])
                if f.get('website'):
                    self.assertRegex(f['website'], r'^https://[a-z0-9]+\.example\.com$', row['id'])
            phones = [r['fields']['phone'] for r in seed]
            self.assertEqual(len(phones), len(set(phones)), fixture_name)

    def test_single_owner_and_thirteen_weeks_of_history(self):
        for config_name, fixture_name, owner in WORKSPACES:
            _, seed, _ = load(config_name, fixture_name)
            self.assertEqual({r['fields']['opportunity_owner'] for r in seed}, {owner})
            offsets = [int(re.match(r'today([+-]\d+)', r['created_at']).group(1)) for r in seed]
            self.assertGreaterEqual(min(offsets), -91)
            self.assertLessEqual(min(offsets), -84, 'history should span about 13 weeks')

    def test_history_never_happens_in_the_future(self):
        for config_name, fixture_name, _ in WORKSPACES:
            _, seed, _ = load(config_name, fixture_name)
            for row in seed:
                stamps = [row['created_at']] + [e['entered_at'] for e in row['stage_history']] \
                    + [a['occurred_at'] for a in row['activities']]
                for stamp in stamps:
                    self.assertLess(int(re.match(r'today([+-]\d+)', stamp).group(1)), 0, row['id'])

    def test_b2b_activities_do_not_invent_milestones(self):
        # Milestone activity kinds would count toward B2B funnel steps they never reached.
        _, seed, _ = load('demo_b2b_services.json', 'demo_b2b_services.json')
        kinds = {a['kind'] for r in seed for a in r['activities']}
        self.assertFalse(kinds & {'contacted', 'replied', 'meeting', 'opportunity'})

    def test_won_engagements_carry_delivery_plan(self):
        _, _, store = load('demo_b2b_services.json', 'demo_b2b_services.json')
        won = [r for r in store.list_records() if r.stage_id == 'contract_awarded']
        self.assertTrue(won)
        for r in won:
            self.assertLess(r.fields['engagement_start'], r.fields['engagement_end'])
            self.assertGreater(r.fields['monthly_hours'], 0)

    def test_month_over_month_growth_in_both_workspaces(self):
        for config_name, fixture_name, _ in WORKSPACES:
            cfg, _, store = load(config_name, fixture_name)
            periods = trailing_periods(store.list_records(), cfg, REF.date, lambda v: local_date(v, REF))
            newest, prior, oldest = periods
            self.assertGreater(newest['new'], oldest['new'], fixture_name)
            self.assertGreaterEqual(newest['opportunity'], prior['opportunity'], fixture_name)
            self.assertGreater(newest['won_value'], oldest['won_value'], fixture_name)


class TestTrendMath(unittest.TestCase):
    def setUp(self):
        self.cfg = load_demo_config(ROOT / 'config' / 'demo_sales_rep.json')
        self.to_date = lambda v: date.fromisoformat(str(v)[:10]) if v else None

    def record(self, rid, created, events=(), activities=()):
        return {'id': rid, 'stage_id': events[-1][0] if events else 'identified', 'created_at': created,
                'fields': {'acv': 10000},
                'stage_history': [{'stage_id': s, 'entered_at': d} for s, d in events],
                'activities': [{'kind': k, 'occurred_at': d} for k, d in activities]}

    def test_first_reach_counts_once_and_uses_earliest_evidence(self):
        rec = self.record('a', '2026-09-01T10:00', [('contacted', '2026-09-05T10:00'), ('replied', '2026-10-10T10:00')],
                          [('replied', '2026-10-02T09:00'), ('contacted', '2026-10-15T09:00')])
        dates = first_milestone_dates([rec], self.cfg, self.to_date)[0]
        self.assertEqual(dates['contacted'], date(2026, 9, 5))
        self.assertEqual(dates['replied'], date(2026, 10, 2))

    def test_trailing_periods_split_and_rates(self):
        records = [
            self.record('old', '2026-08-01T10:00', [('contacted', '2026-09-10T10:00')]),
            self.record('new1', '2026-10-01T10:00', [('contacted', '2026-10-02T10:00'), ('replied', '2026-10-05T10:00')]),
            self.record('new2', '2026-10-03T10:00', [('contacted', '2026-10-04T10:00'),
                                                     ('meeting_booked', '2026-10-12T10:00'),
                                                     ('opportunity_created', '2026-10-18T10:00')]),
        ]
        newest, prior, _ = trailing_periods(records, self.cfg, date(2026, 10, 21), self.to_date)
        self.assertEqual((newest['start'], newest['end']), (date(2026, 9, 22), date(2026, 10, 21)))
        self.assertEqual((newest['new'], newest['contacted'], newest['replied']), (2, 2, 1))
        self.assertEqual(newest['opportunity'], 1)
        self.assertEqual(newest['won_value'], 10000)
        self.assertAlmostEqual(newest['reply_rate'], 50.0)
        self.assertEqual((prior['contacted'], prior['replied']), (1, 0))
        self.assertEqual(prior['reply_rate'], 0.0)

    def test_empty_period_rates_are_none(self):
        newest = trailing_periods([], self.cfg, date(2026, 10, 21), self.to_date)[0]
        self.assertIsNone(newest['reply_rate'])
        self.assertEqual(newest['new'], 0)

    def test_weekly_series_is_oldest_first_and_ends_today(self):
        weeks = weekly_series([], self.cfg, date(2026, 10, 21), self.to_date, weeks=13)
        self.assertEqual(len(weeks), 13)
        self.assertEqual(weeks[-1]['end'], date(2026, 10, 21))
        self.assertLess(weeks[0]['start'], weeks[-1]['start'])


class TestSidebarSummaries(unittest.TestCase):
    def test_activity_counts_last_seven_days_and_logging_moves_the_goal(self):
        from pipeline.domain.outreach_metrics import activity_counts
        # Newly logged activity carries the real clock, so use a live session reference here.
        cfg, seed, _ = load('demo_sales_rep.json', 'demo_prospects.json')
        store = MemoryRecordStorage(cfg, seed)
        ref = store.reference
        to_date = lambda v: local_date(v, ref)  # noqa: E731
        week = (date.fromordinal(ref.date.toordinal() - 6), ref.date)
        before = activity_counts(store.list_records(), *week, to_date)
        self.assertGreater(before['calls'], 0)
        self.assertGreater(before['emails'], 0)
        store.add_activity('demo-001', 'call', 'Synthetic call')
        after = activity_counts(store.list_records(), *week, to_date)
        self.assertEqual(after['calls'], before['calls'] + 1)

    def test_awaiting_decision_lists_open_proposals_oldest_first(self):
        from pipeline.domain.outreach_metrics import awaiting_decision
        cfg, _, store = load('demo_b2b_services.json', 'demo_b2b_services.json')
        rows = awaiting_decision(store.list_records(), cfg, REF.date, lambda v: local_date(v, REF))
        self.assertTrue(rows)
        self.assertTrue(all(r['record'].stage_id in ('proposal_sent', 'negotiation') for r in rows))
        days = [r['days'] for r in rows]
        self.assertEqual(days, sorted(days, reverse=True))

    def test_capacity_counts_won_engagements_overlapping_next_30_days(self):
        from pipeline.domain.outreach_metrics import capacity_summary
        cfg, _, store = load('demo_b2b_services.json', 'demo_b2b_services.json')
        summary = capacity_summary(store.list_records(), cfg, REF.date)
        self.assertEqual(summary['committed'], 105)
        self.assertEqual(summary['pending'], 65)
        self.assertTrue(all(u['start'] >= REF.date for u in summary['upcoming']))

    def test_widget_config_validation(self):
        from pipeline.domain.models import PipelineInstanceConfig
        raw = json.loads((ROOT / 'config' / 'demo_sales_rep.json').read_text(encoding='utf-8'))['instance_config']
        raw.pop('activity_targets')
        with self.assertRaises(ValueError):
            PipelineInstanceConfig.model_validate(raw)
        raw = json.loads((ROOT / 'config' / 'demo_b2b_services.json').read_text(encoding='utf-8'))['instance_config']
        raw.pop('delivery_capacity')
        with self.assertRaises(ValueError):
            PipelineInstanceConfig.model_validate(raw)

    def test_both_sidebars_render_with_synthetic_data_notice(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        app_path = ROOT / 'pipeline' / 'adapters' / 'primary' / 'app.py'
        with patch.dict('os.environ', {'PIPELINE_MODE': 'demo', 'DEMO_MODE': 'false'}):
            app = AppTest.from_file(str(app_path), default_timeout=30).run()
            self.assertFalse(app.exception)
            sidebar = ' '.join(m.value for m in app.sidebar.markdown)
            self.assertIn("Today's Call List", sidebar)
            self.assertIn('Weekly Goals', sidebar)
            self.assertIn('fictitious', sidebar)
            self.assertTrue(any(b.label == '📞' for b in app.sidebar.button))
            app.selectbox(key='demo_workspace_selector').set_value('b2b_services').run()
            self.assertFalse(app.exception)
            sidebar = ' '.join(m.value for m in app.sidebar.markdown)
            self.assertIn('Proposals Awaiting Decision', sidebar)
            self.assertIn('Delivery Capacity', sidebar)
            self.assertTrue(any('synthetic' in m.value for m in app.markdown))


class TestSidebarNavigation(unittest.TestCase):
    def test_clicking_a_sidebar_company_opens_it_in_the_pipeline(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        app_path = ROOT / 'pipeline' / 'adapters' / 'primary' / 'app.py'
        with patch.dict('os.environ', {'PIPELINE_MODE': 'demo', 'DEMO_MODE': 'false'}):
            app = AppTest.from_file(str(app_path), default_timeout=30).run()
            app.radio(key='public_navigation').set_value('analytics').run()
            link = next(b for b in app.sidebar.button if b.key and '_side_q_open_' in b.key)
            record_id = link.key.split('_side_q_open_')[1]
            link.click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['public_navigation'], 'pipeline')
            self.assertEqual(app.session_state['public_0_sales_rep_search'], link.label)
            self.assertEqual(app.session_state['public_0_sales_rep_focus'], record_id)
            # The focused record's card is rendered (and is the only match for its company)
            self.assertTrue(any(f'public_0_sales_rep_stage_form_{record_id}' == b.form_id for b in app.button))


if __name__ == '__main__':
    unittest.main()
