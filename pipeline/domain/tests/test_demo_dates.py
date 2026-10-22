"""Comprehensive test suite for relative demo dates, timezone anchors, materialization,
and markdown escaping.
"""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

from pipeline.domain.demo_dates import (
    DemoReference,
    is_relative,
    resolve_date,
    resolve_datetime,
    resolve_timezone,
    session_reference,
    materialize_seed,
    local_date,
    parse_instant,
)
from pipeline.adapters.primary.public_ui import escape_markdown
from pipeline.domain.instance_loader import load_demo_config
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage

APP = Path(__file__).resolve().parents[2] / 'adapters/primary/app.py'


class TestDemoDates(unittest.TestCase):
    def test_relative_token_recognition(self):
        self.assertTrue(is_relative("today+0"))
        self.assertTrue(is_relative("today-3"))
        self.assertTrue(is_relative("today+14"))
        self.assertTrue(is_relative("today-10T09:30"))
        self.assertTrue(is_relative("today+1T23:59"))
        self.assertFalse(is_relative("today"))
        self.assertFalse(is_relative("2026-10-21"))
        self.assertFalse(is_relative("today+"))
        self.assertFalse(is_relative(None))
        self.assertFalse(is_relative(123))

    def test_month_end_year_end_and_leap_year_rollover(self):
        # Month-end rollover
        jan31 = DemoReference(date(2026, 1, 31), timezone.utc)
        self.assertEqual(resolve_date("today+1", jan31), "2026-02-01")
        self.assertEqual(resolve_date("today-1", jan31), "2026-01-30")

        # Year-end rollover
        dec31 = DemoReference(date(2025, 12, 31), timezone.utc)
        self.assertEqual(resolve_date("today+1", dec31), "2026-01-01")
        self.assertEqual(resolve_date("today-1", dec31), "2025-12-30")

        # Leap year 2024
        leap_feb28 = DemoReference(date(2024, 2, 28), timezone.utc)
        self.assertEqual(resolve_date("today+1", leap_feb28), "2024-02-29")
        self.assertEqual(resolve_date("today+2", leap_feb28), "2024-03-01")

        # Non-leap year 2025
        non_leap_feb28 = DemoReference(date(2025, 2, 28), timezone.utc)
        self.assertEqual(resolve_date("today+1", non_leap_feb28), "2025-03-01")

    def test_datetime_token_resolution_and_ordering(self):
        ref = DemoReference(date(2026, 10, 21), timezone.utc)
        t1 = resolve_datetime("today-2T14:30", ref)
        t2 = resolve_datetime("today-1T09:00", ref)
        t3 = resolve_datetime("today+0T16:45", ref)
        self.assertEqual(t1, "2026-10-19T14:30:00+00:00")
        self.assertEqual(t2, "2026-10-20T09:00:00+00:00")
        self.assertEqual(t3, "2026-10-21T16:45:00+00:00")
        self.assertTrue(t1 < t2 < t3)

    def test_invalid_tokens_and_out_of_range_offsets(self):
        ref = DemoReference(date(2026, 10, 21), timezone.utc)
        with self.assertRaises(ValueError):
            resolve_date("today-2T14:30", ref)  # Date token cannot have clock
        with self.assertRaises(ValueError):
            resolve_datetime("today-2", ref)  # Datetime token requires clock
        with self.assertRaises(ValueError):
            resolve_date("today+99999", ref)  # Out of range offset

    def test_timezone_resolution(self):
        # IANA timezone
        tz, label = resolve_timezone("America/New_York")
        self.assertEqual(label, "America/New_York")

        # JS timezone offset in minutes (e.g. 420 minutes behind UTC -> UTC-7)
        tz_offset, label_offset = resolve_timezone(None, 420)
        self.assertIn("UTC-", label_offset)

        # Fallback to UTC
        tz_default, label_default = resolve_timezone(None, None)
        self.assertEqual(label_default, "UTC")
        self.assertEqual(tz_default, timezone.utc)

    def test_materialize_seed_purity_and_preservation(self):
        ref = DemoReference(date(2026, 10, 21), timezone.utc)
        raw_seed = [
            {
                "id": "test-1",
                "stage_id": "contacted",
                "created_at": "today-5T10:00",
                "stage_history": [
                    {"stage_id": "identified", "entered_at": "today-5T10:00"},
                    {"stage_id": "contacted", "entered_at": "today-2T15:00"},
                ],
                "activities": [
                    {"kind": "contacted", "text": "Outreach sent", "occurred_at": "today-2T15:00"}
                ],
                "fields": {
                    "company": "Test Co",
                    "next_action_date": "today+1",
                }
            }
        ]
        materialized = materialize_seed(raw_seed, ref, ["next_action_date"])
        # Original remains unmodified with relative tokens
        self.assertEqual(raw_seed[0]["created_at"], "today-5T10:00")
        self.assertEqual(raw_seed[0]["fields"]["next_action_date"], "today+1")

        # Materialized has ISO dates
        self.assertEqual(materialized[0]["created_at"], "2026-10-16T10:00:00+00:00")
        self.assertEqual(materialized[0]["fields"]["next_action_date"], "2026-10-22")

    def test_memory_record_storage_reset_restores_relative_seed(self):
        cfg = load_demo_config()
        ref = DemoReference(date(2026, 10, 21), timezone.utc)
        raw_seed = [
            {
                "id": "demo-001",
                "stage_id": "identified",
                "created_at": "today-5T10:00",
                "stage_history": [{"stage_id": "identified", "entered_at": "today-5T10:00"}],
                "activities": [],
                "fields": {
                    "company": "Initial Name",
                    "contact": "Avery Example",
                    "next_action_date": "today+2",
                }
            }
        ]
        storage = MemoryRecordStorage(cfg, raw_seed, reference=ref)
        records = storage.list_records()
        self.assertEqual(records[0].fields["company"], "Initial Name")
        self.assertEqual(records[0].fields["next_action_date"], "2026-10-23")

        # Update company and date
        storage.update("demo-001", {"company": "Modified Name", "next_action_date": "2026-11-01"}, "qualified")
        updated = storage.list_records()
        self.assertEqual(updated[0].fields["company"], "Modified Name")
        self.assertEqual(updated[0].fields["next_action_date"], "2026-11-01")

        # Reset restores relative seed
        storage.reset()
        restored = storage.list_records()
        self.assertEqual(restored[0].fields["company"], "Initial Name")
        self.assertEqual(restored[0].fields["next_action_date"], "2026-10-23")
        self.assertEqual(restored[0].stage_id, "identified")

    def test_markdown_escaping_prevents_katex_clashes(self):
        # Plain text remains unchanged
        self.assertEqual(escape_markdown("Lumina HealthTech"), "Lumina HealthTech")

        # Dollar sign is escaped
        self.assertEqual(escape_markdown("$200M AUM expansion"), "\\$200M AUM expansion")

        # Pre-escaped dollar sign is not double-escaped
        self.assertEqual(escape_markdown("\\$200M AUM expansion"), "\\$200M AUM expansion")

        # Multiple dollar signs
        escaped = escape_markdown("$100 to $200")
        self.assertEqual(escaped, "\\$100 to \\$200")

    def test_reset_demo_data_button_removed_from_sidebar(self):
        with patch.dict("os.environ", {"PIPELINE_MODE": "demo", "DEMO_MODE": "false"}):
            app = AppTest.from_file(str(APP), default_timeout=20).run()
            self.assertFalse(app.exception)
            self.assertFalse(any(b.key == "btn_reset_demo_data" for b in app.button))

    def test_storage_reset_restores_seed(self):
        with patch.dict("os.environ", {"PIPELINE_MODE": "demo", "DEMO_MODE": "false"}):
            app = AppTest.from_file(str(APP), default_timeout=20).run()
            store = app.session_state["_demo_store"]
            store.update("demo-001", {"company": "Mutated Name"}, "contacted")
            store.reset()
            rec = next(r for r in store.list_records() if r.id == "demo-001")
            self.assertEqual(rec.fields["company"], "Lumina HealthTech")

    def test_shortened_kpi_titles_in_both_configs_and_views(self):
        with patch.dict("os.environ", {"PIPELINE_MODE": "demo", "DEMO_MODE": "false"}):
            app = AppTest.from_file(str(APP), default_timeout=20).run()
            self.assertFalse(app.exception)

            # 1. Sales Rep pipeline view
            sales_labels = [m.label for m in app.metric]
            self.assertEqual(sales_labels, ["Booking Rate", "Reply Rate", "Reply-to-Meeting", "Prospects", "Active Prospects", "Pipeline ACV"])
            self.assertEqual(app.metric[5].value, "$1.02M")
            for label in sales_labels:
                self.assertLessEqual(len(label), 16, f"KPI label too long: {label}")

            # 2. Sales Rep analytics view
            app.radio(key="public_navigation").set_value("analytics").run()
            self.assertFalse(app.exception)
            sales_analytics_labels = [m.label for m in app.metric]
            self.assertEqual(sales_analytics_labels, ["Booking Rate", "Reply Rate", "Reply-to-Meeting", "Prospects", "Active Prospects", "Pipeline ACV"])
            self.assertEqual(app.metric[5].value, "$1.02M")

            # 3. Switch to B2B Services workspace
            app.selectbox(key="demo_workspace_selector").set_value("b2b_services").run()
            self.assertFalse(app.exception)
            b2b_labels = [m.label for m in app.metric]
            self.assertEqual(b2b_labels, ["Win Rate", "Negotiation Rate", "Opportunities", "Active", "Pipeline Value", "Avg Deal Size"])
            self.assertEqual(app.metric[4].value, "$279,500")
            for label in b2b_labels:
                self.assertLessEqual(len(label), 16, f"B2B KPI label too long: {label}")

            # 4. B2B Services pipeline view
            app.radio(key="public_navigation").set_value("pipeline").run()
            self.assertFalse(app.exception)
            b2b_pipeline_labels = [m.label for m in app.metric]
            self.assertEqual(b2b_pipeline_labels, ["Win Rate", "Negotiation Rate", "Opportunities", "Active", "Pipeline Value", "Avg Deal Size"])
            self.assertEqual(app.metric[4].value, "$279,500")

    def test_analytics_populated_across_reruns_and_workspace_switches(self):
        # Regression: per-run module reloads made stored records fail an isinstance
        # check in the metrics code, so analytics rendered all zeros.
        with patch.dict("os.environ", {"PIPELINE_MODE": "demo", "DEMO_MODE": "false"}):
            app = AppTest.from_file(str(APP), default_timeout=20).run()
            app.radio(key="public_navigation").set_value("analytics").run()
            expected = {"sales_rep": ("92", "$1.02M"), "b2b_services": ("33", "$279,500")}
            for ws in ["sales_rep", "b2b_services", "sales_rep", "b2b_services", "sales_rep"]:
                app.selectbox(key="demo_workspace_selector").set_value(ws).run()
                app.run()
                self.assertFalse(app.exception)
                values = [m.value for m in app.metric]
                total, acv = expected[ws]
                self.assertIn(total, values, f"{ws}: {values}")
                self.assertIn(acv, values, f"{ws}: {values}")

    def test_metrics_accept_records_from_reloaded_record_class(self):
        from pydantic import BaseModel
        from pipeline.domain.outreach_metrics import historical_cohorts

        class ForeignRecord(BaseModel):  # stands in for a PipelineRecord from a reloaded module
            id: str
            stage_id: str
            stage_history: list = []
            activities: list = []
            fields: dict = {}

        from pipeline.domain.instance_loader import load_demo_config
        cfg = load_demo_config(Path(__file__).resolve().parents[3] / "config" / "demo_sales_rep.json")
        cohorts, _ = historical_cohorts([ForeignRecord(id="x", stage_id="replied")], cfg)
        self.assertEqual(cohorts["total"], {"x"})
        self.assertEqual(cohorts["replied"], {"x"})

    def test_format_metric_currency_scaling(self):
        from pipeline.adapters.primary.public_ui import format_metric_currency
        self.assertEqual(format_metric_currency(1_780_000), "$1.78M")
        self.assertEqual(format_metric_currency(1_128_000), "$1.13M")
        self.assertEqual(format_metric_currency(1_000_000), "$1M")
        self.assertEqual(format_metric_currency(1_500_000), "$1.5M")
        self.assertEqual(format_metric_currency(20_000_000), "$20M")
        self.assertEqual(format_metric_currency(1_250_000_000), "$1.25B")
        self.assertEqual(format_metric_currency(500_000), "$500,000")
        self.assertEqual(format_metric_currency(12_500), "$12,500")
        self.assertEqual(format_metric_currency(0), "$0")
        self.assertEqual(format_metric_currency(-1_780_000), "-$1.78M")
        self.assertEqual(format_metric_currency(None), "—")

    def test_workspace_toggle_resilience_and_page_type_safety(self):
        with patch.dict("os.environ", {"PIPELINE_MODE": "demo", "DEMO_MODE": "false"}):
            app = AppTest.from_file(str(APP), default_timeout=20).run()
            self.assertFalse(app.exception)

            # Inject a string into page session state to verify type safety ('2' > 4 in Python would raise TypeError)
            app.session_state["public_0_sales_rep_page"] = "2"
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["public_0_sales_rep_page"], 2)

            # Set page 8 in Sales Rep (10 pages)
            app.selectbox(key="public_0_sales_rep_page").set_value(8).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["public_0_sales_rep_page"], 8)

            # Toggle to B2B Services (only 4 pages): its widgets are scoped separately and start on page 1
            app.selectbox(key="demo_workspace_selector").set_value("b2b_services").run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["public_0_b2b_services_page"], 1)

            # Toggle back to Sales Rep: its own page selection is preserved
            app.selectbox(key="demo_workspace_selector").set_value("sales_rep").run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["public_0_sales_rep_page"], 8)

            # Toggle back to B2B Services
            app.selectbox(key="demo_workspace_selector").set_value("b2b_services").run()
            self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()

