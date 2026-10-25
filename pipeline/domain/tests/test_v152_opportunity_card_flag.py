"""Focused test suite for More Outbound v1.5.2: Opportunity Card Job Signal Flag Indicator."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock


from pipeline.domain.models import JobPosting
from pipeline.domain.services import PipelineKPIService


class TestOpportunityCardFlagIndicator(unittest.TestCase):
    """
    Test suite verifying the Job Signal Flag indicator on Pipeline Tracker opportunity cards.
    Covers:
    - Domain flag detection logic from persisted Job Signals JSON
    - Single flag vs multiple flags
    - Exclusion of warnings and benefits
    - Missing, empty, and malformed signals
    """

    # -------------------------------------------------------------------------
    # Unit Tests for PipelineKPIService.has_job_signal_flags
    # -------------------------------------------------------------------------

    def test_single_flag_detected(self):
        """Opportunity with one Job Signal flag returns True."""
        signals_json = json.dumps({
            "version": 1,
            "flags": ["FLAG: [clearance-req]: Secret Clearance Required"],
            "warnings": [],
            "benefits": []
        })
        opp = {"Company Name": "Apex Defense", "Job Title": "Security Analyst", "Job Signals": signals_json}
        self.assertTrue(PipelineKPIService.has_job_signal_flags(opp))

    def test_multiple_flags_detected(self):
        """Opportunity with multiple Job Signal flags returns True."""
        signals_json = json.dumps({
            "version": 1,
            "flags": [
                "FLAG: [clearance-req]: Secret Clearance Required",
                "FLAG: [onsite-mandate]: 5 days onsite non-negotiable"
            ],
            "warnings": [],
            "benefits": []
        })
        opp = {"Company Name": "Lockheed", "Job Title": "Systems Eng", "Job Signals": signals_json}
        self.assertTrue(PipelineKPIService.has_job_signal_flags(opp))

    def test_warnings_only_do_not_trigger_flag(self):
        """Job Signals containing warnings but no flags must NOT trigger the indicator."""
        signals_json = json.dumps({
            "version": 1,
            "flags": [],
            "warnings": ["[heavy-travel]: 75% domestic travel", "[on-call]: 24/7 rotation"],
            "benefits": []
        })
        opp = {"Company Name": "Consulting Corp", "Job Title": "Field Consultant", "Job Signals": signals_json}
        self.assertFalse(PipelineKPIService.has_job_signal_flags(opp))

    def test_benefits_only_do_not_trigger_flag(self):
        """Job Signals containing benefits only must NOT trigger the indicator."""
        signals_json = json.dumps({
            "version": 1,
            "flags": [],
            "warnings": [],
            "benefits": ["BENEFIT: [401k-match]: 6% 401k match"]
        })
        opp = {"Company Name": "Generous Co", "Job Title": "Backend Eng", "Job Signals": signals_json}
        self.assertFalse(PipelineKPIService.has_job_signal_flags(opp))

    def test_warnings_and_benefits_together_do_not_trigger_flag(self):
        """Job Signals with both warnings and benefits (but 0 flags) must NOT trigger the indicator."""
        signals_json = json.dumps({
            "version": 1,
            "flags": [],
            "warnings": ["[on-call]: Off-hours pager duty"],
            "benefits": ["BENEFIT: [equity]: Generous stock options"]
        })
        opp = {"Company Name": "StartupX", "Job Title": "DevOps Lead", "Job Signals": signals_json}
        self.assertFalse(PipelineKPIService.has_job_signal_flags(opp))

    def test_empty_and_missing_signals(self):
        """Missing, None, or empty signal records return False."""
        self.assertFalse(PipelineKPIService.has_job_signal_flags({}))
        self.assertFalse(PipelineKPIService.has_job_signal_flags({"Job Signals": None}))
        self.assertFalse(PipelineKPIService.has_job_signal_flags({"Job Signals": ""}))
        self.assertFalse(PipelineKPIService.has_job_signal_flags(None))

    def test_populated_json_with_empty_flags_list(self):
        """Field is populated JSON, but flags collection is empty: returns False."""
        signals_json = json.dumps({"version": 1, "flags": [], "warnings": [], "benefits": []})
        opp = {"Company Name": "Clean Role Inc", "Job Title": "Product Manager", "Job Signals": signals_json}
        self.assertFalse(PipelineKPIService.has_job_signal_flags(opp))

    def test_malformed_signal_data_handled_gracefully(self):
        """Malformed or corrupt JSON string handles gracefully without raising and returns False."""
        corrupt_opp = {"Company Name": "Bad JSON Inc", "Job Title": "QA Analyst", "Job Signals": "not { valid: json"}
        self.assertFalse(PipelineKPIService.has_job_signal_flags(corrupt_opp))

        dict_missing_fields = {"Company Name": "Weird Dict", "Job Signals": json.dumps({"version": 2})}
        self.assertFalse(PipelineKPIService.has_job_signal_flags(dict_missing_fields))

    def test_legacy_fit_warning_resolution(self):
        """Legacy sheet records without 'Job Signals' JSON resolve flags from 'Fit Warning'."""
        legacy_with_flag = {
            "Company Name": "Legacy Corp",
            "Job Title": "Architect",
            "Job Signals": "",
            "Fit Warning": "FLAG: [clearance]: Top Secret Required; normal warning note"
        }
        self.assertTrue(PipelineKPIService.has_job_signal_flags(legacy_with_flag))

        legacy_warnings_only = {
            "Company Name": "Legacy Corp",
            "Job Title": "Architect",
            "Job Signals": "",
            "Fit Warning": "[oncall]: Weekend shifts required; [travel]: 40% travel"
        }
        self.assertFalse(PipelineKPIService.has_job_signal_flags(legacy_warnings_only))

    def test_job_posting_model_resolution(self):
        """JobPosting model instances evaluate correctly."""
        model_flagged = JobPosting(
            opportunity_id="opp-model-1",
            company_name="Apex Defense",
            job_title="Lead Eng",
            telemetry_flags=["FLAG: [clearance]: TS/SCI"]
        )
        self.assertTrue(PipelineKPIService.has_job_signal_flags(model_flagged))

        model_clean = JobPosting(
            opportunity_id="opp-model-2",
            company_name="Stripe",
            job_title="RevOps Analyst",
            telemetry_warnings=["[travel]: occasional travel"]
        )
        self.assertFalse(PipelineKPIService.has_job_signal_flags(model_clean))


if __name__ == "__main__":
    unittest.main()
