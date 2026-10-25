from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from pydantic import ValidationError
from pipeline.domain.instance_loader import load_demo_config, InstanceConfigError, DEFAULT_DEMO_CONFIG
from pipeline.domain.models import JobPosting, ScreeningQA, PipelineInstanceConfig
from pipeline.domain.records import PipelineRecord, LegacyJobSnapshot, LegacySheetSnapshot, validate_fields, format_field


class TestInstanceRecords(unittest.TestCase):
    def test_demo_schema_and_formatter(self):
        cfg = load_demo_config()
        self.assertEqual(cfg.mode, 'demo')
        values = validate_fields(cfg, {'company': 'Fictional Account', 'contact': 'Avery Example', 'acv': 12000})
        record = PipelineRecord(stage_id=cfg.initial_stage, fields=values)
        self.assertNotIn('selected_resume_name', record.model_dump())
        self.assertEqual(format_field(next(f for f in cfg.fields if f.key == 'acv'), values['acv']), '$12,000')
        for bad in ({'company': ' ', 'contact': 'A'}, {'company': 'A', 'contact': 'B', 'acv': float('nan')},
                    {'company': 'A', 'contact': 'B', 'unexpected_extra': 'x'}):
            with self.assertRaises(ValueError):
                validate_fields(cfg, bad)

    def test_schema_rejects_unsafe_and_incoherent_configuration(self):
        raw = load_demo_config().model_dump()
        variants = []
        for key, value in [('storage', 'google'), ('initial_stage', 'unknown'), ('metrics', ['arbitrary_expression']),
                           ('schema_version', 9), ('logo_path', 'custom.png')]:
            variants.append({**raw, key: value})
        variants += [{**raw, 'integrations': {'google_workspace': True}},
                     {**raw, 'stages': raw['stages'] + [raw['stages'][0]]},
                     {**raw, 'fields': [{**raw['fields'][0], 'key': 'salary'}]},
                     {**raw, 'navigation': []}, {**raw, 'features': {'resume_matching': True}}]
        for value in variants:
            with self.subTest(value=list(value.keys())), self.assertRaises(ValidationError):
                PipelineInstanceConfig.model_validate(value)

    def test_loader_never_falls_back_or_rewrites(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'config.json'
            with self.assertRaises(InstanceConfigError):
                load_demo_config(path)
            self.assertFalse(path.exists())
            for content in ('invalid json', '{}', '{"instance_config":{"mode":"legacy"}}'):
                path.write_text(content)
                with self.assertRaises(InstanceConfigError):
                    load_demo_config(path)
                self.assertEqual(path.read_text(), content)

    def test_legacy_model_roundtrip_preserves_every_field(self):
        job = JobPosting(
            opportunity_id='legacy-synthetic-01', company_name='Fictional Co', job_title='Operations Lead',
            status='Hiring Manager', raw_description='Synthetic raw source', source_url='https://example.invalid/role',
            opportunity_source='Inbound', contact_name='Taylor Example', date_created='2026-01-01',
            stage_history=[{'stage': 'Applied', 'entered_at': '2026-01-01', 'source': 'legacy'},
                           {'stage': 'Hiring Manager', 'entered_at': '2026-01-07'}],
            salary_expectation='$125,000', notes='[2026-01-08] Original note',
            employment_arrangement='Contract', worker_classification='1099', pay_basis='Hourly',
            expected_hours_per_week=32, expected_hours_per_week_is_assumed=False,
            contract_length_months=6, contract_length_raw='6 months', contract_value_min=80000,
            selected_resume_name='Synthetic Revenue Operations Resume', drive_folder_link='https://example.invalid/folder',
            drive_jd_link='https://example.invalid/source', drive_screening_doc_link='https://example.invalid/qa',
            role_intelligence_status='Generated', role_intelligence_link='https://example.invalid/intel',
            telemetry_findings=[{'rule_id': 'synthetic', 'category': 'warning'}],
            screening_qa=[ScreeningQA(qa_id='legacy-qa', question='Describe a workflow.',
                                      answer='Synthetic original answer.', archetype='PROCESS_GOVERNANCE',
                                      competency_signals=['Operations'], created_at='2026-01-01 09:00:00')],
        )
        before = job.model_dump(mode='json')
        snapshot = LegacyJobSnapshot(job)
        view = snapshot.as_record()
        self.assertEqual(view.id, job.opportunity_id)
        view.fields['notes'] = 'Edited projection cannot alter original source'
        self.assertEqual(snapshot.restore().model_dump(mode='json'), before)
        self.assertEqual(job.model_dump(mode='json'), before)


    def test_sheet_snapshot_preserves_unknown_columns_and_history_encoding(self):
        row = {'Opportunity ID': 'legacy-id', 'Stage History': '[{"stage":"Applied"}]',
               'Selected Resume': 'Synthetic Resume', 'Screening QA': [{'qa_id': 'qa1', 'answer': 'original'}],
               'Notes': '[2026-01-01] Keep exactly', 'Future Column': {'keep': True},
               'Target Pay Range': '$100,000–$120,000'}
        snapshot = LegacySheetSnapshot(row)
        restored = snapshot.restore()
        self.assertEqual(restored, row)
        restored['Future Column']['keep'] = False
        self.assertTrue(snapshot.restore()['Future Column']['keep'])
