import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pipeline.adapters.primary.runtime import public_mode, select_session, offline_adapters
from pipeline.adapters.primary.dashboard_data import dashboard_records
from pipeline.adapters.primary.analytics_dashboard_ui import safe_date_str, safe_stale_threshold


class TestDemoSafety(unittest.TestCase):
    def test_modes_fail_closed(self):
        self.assertTrue(public_mode({'DEMO_MODE': 'true'}))
        self.assertTrue(public_mode({'PIPELINE_MODE': 'demo'}))
        for env in ({'DEMO_MODE': 'typo'}, {'PIPELINE_MODE': 'typo'}, {'DEMO_MODE': 'true', 'PIPELINE_MODE': 'private'}):
            with self.assertRaises(ValueError):
                public_mode(env)

    def test_offline_adapters_are_session_owned(self):
        a, b = {}, {}
        first = offline_adapters(a)
        self.assertIs(first, offline_adapters(a))
        self.assertIsNot(first[0], offline_adapters(b)[0])
        first[0].saved_jobs.append({'sentinel': True})
        self.assertEqual(offline_adapters(b)[0].saved_jobs, [])
        self.assertEqual(first[4:], (None, None))
        select_session(a, 'another-instance')
        self.assertNotIn('_offline_adapters', a)

    def test_expected_storage_failure_and_disconnected_use_cache(self):
        cache = [{'Opportunity ID': 'synthetic'}]
        storage = Mock(is_connected=True)
        storage.fetch_all_opportunities.side_effect = TimeoutError('unavailable')
        rows, fallback = dashboard_records(storage, cache)
        self.assertTrue(fallback)
        self.assertEqual(rows, cache)
        self.assertIsNot(rows, cache)
        storage.is_connected = False
        self.assertEqual(dashboard_records(storage, cache), (cache, True))
        storage.is_connected = True
        storage.fetch_all_opportunities.side_effect = ValueError('duplicate canonical identity')
        with self.assertRaises(ValueError):
            dashboard_records(storage, cache)

    def test_date_and_numeric_guards(self):
        self.assertEqual(safe_date_str('2026-10-18T13:30:00Z'), '2026-10-18')
        for value in (None, 'invalid', '', {}):
            self.assertEqual(safe_date_str(value), 'Missing')
        for value, expected in ((0, 1), (120, 90), ('bad', 7), (None, 7), ('14', 14)):
            self.assertEqual(safe_stale_threshold(value), expected)

    def test_dashboard_mounts_with_empty_and_malformed_dates(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_string('''
from types import SimpleNamespace
from pipeline.adapters.primary.analytics_dashboard_ui import render_analytics_dashboard_view
render_analytics_dashboard_view([
    {'Opportunity ID': 'a', 'Status': 'Applied', 'Date Created': 'bad'},
    {'Opportunity ID': 'b', 'Status': 'Applied', 'Date Created': '2020-01-01'},
], SimpleNamespace(stale_threshold_days=120))
''').run(timeout=10)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.number_input[0].value, 90)

    def test_public_startup_never_loads_private_services(self):
        from streamlit.testing.v1 import AppTest
        app_path = Path(__file__).resolve().parents[2] / 'adapters/primary/app.py'
        with patch.dict(os.environ, {'DEMO_MODE': 'true', 'GOOGLE_SPREADSHEET_ID': 'forbidden-private-id'}), \
             patch('pipeline.domain.services.PipelineConfigService.load_config', side_effect=AssertionError('private config')), \
             patch('pipeline.adapters.secondary.google_sheets.GoogleSheetsAdapter.__init__', side_effect=AssertionError('live provider')):
            app = AppTest.from_file(str(app_path)).run()
            self.assertEqual(len(app.exception), 0)
            self.assertNotIn('forbidden-private-id', str(app))


if __name__ == '__main__':
    unittest.main()
