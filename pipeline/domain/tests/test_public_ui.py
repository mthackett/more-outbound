import json
import io
from contextlib import ExitStack
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from pipeline.domain.instance_loader import load_demo_config
from pipeline.domain.intelligence_service import IntelligenceService

APP = Path(__file__).resolve().parents[2] / 'adapters/primary/app.py'


class TestPublicUI(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'PIPELINE_MODE': 'demo', 'DEMO_MODE': 'false'})
        env.start()
        self.addCleanup(env.stop)

    def test_create_edit_notes_navigation_and_reset(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(app.exception)
        initial_count = len(app.session_state['_demo_store'].list_records())
        app.radio(key='public_navigation').set_value('intake').run()
        app.text_input(key='public_0_intake_company').set_value('Fictional Test Account')
        app.text_input(key='public_0_intake_contact').set_value('Avery Example')
        next(b for b in app.button if b.label == 'Add Prospect').click().run()
        self.assertFalse(app.exception)
        records = app.session_state['_demo_store'].list_records()
        self.assertEqual(len(records), initial_count + 1)
        record_id = records[-1].id
        app.radio(key='public_navigation').set_value('pipeline').run()
        app.text_input(key='public_0_search').set_value('Fictional Test Account').run()
        app.selectbox(key='public_0_stage_' + record_id).set_value('meeting_booked')
        next(b for b in app.button if b.label == 'Save Changes').click().run()
        self.assertFalse(app.exception)
        app.text_area(key='public_0_note_' + record_id).set_value('Synthetic discovery booked.')
        next(b for b in app.button if b.label == 'Add Note').click().run()
        record = app.session_state['_demo_store'].list_records()[-1]
        self.assertEqual(record.stage_id, 'meeting_booked')
        self.assertEqual(record.activities[-1].text, 'Synthetic discovery booked.')
        for destination in ('analytics', 'intelligence'):
            app.radio(key='public_navigation').set_value(destination).run()
            self.assertFalse(app.exception)
        app.button(key='public_reset').click().run()
        self.assertEqual(len(app.session_state['_demo_store'].list_records()), initial_count)

    def test_labels_features_and_fields_follow_configuration(self):
        cfg = load_demo_config().model_dump()
        cfg['labels']['create'] = 'Register Account'
        cfg['navigation'][1]['label'] = 'Register'
        cfg['fields'][0]['label'] = 'Organization'
        cfg['features']['activities'] = False
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'public.json'
            path.write_text(json.dumps({'instance_config': cfg}), encoding='utf-8')
            with patch.dict(os.environ, {'PIPELINE_INSTANCE_CONFIG': str(path)}):
                app = AppTest.from_file(str(APP)).run()
                app.radio(key='public_navigation').set_value('intake').run()
                self.assertIn('Organization *', [i.label for i in app.text_input])
                self.assertIn('Register Account', [b.label for b in app.button])
                self.assertFalse(app.exception)

    def test_invalid_config_stops_without_private_data_or_provider(self):
        with patch.dict(os.environ, {'PIPELINE_INSTANCE_CONFIG': 'missing-demo-config.json'}), \
             patch('pipeline.domain.services.PipelineConfigService.load_config', side_effect=AssertionError('private config')):
            app = AppTest.from_file(str(APP)).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.error), 1)
            self.assertNotIn('missing-demo-config.json', app.error[0].value)

    def test_public_ui_has_no_private_controls_or_cloud_ids(self):
        with patch.dict(os.environ, {'GOOGLE_SPREADSHEET_ID': 'private-sentinel', 'CANDIDATE_EMAIL': 'private@example.invalid'}):
            app = AppTest.from_file(str(APP)).run()
            for destination in ('pipeline', 'intake', 'analytics', 'intelligence'):
                app.radio(key='public_navigation').set_value(destination).run()
                rendered = str(app)
                for private in ('private-sentinel', 'private@example.invalid', 'Resume Performance', 'Salary', 'Job Post', 'Quick Cloud Links'):
                    self.assertNotIn(private, rendered)
                self.assertFalse(app.exception)

    def test_public_all_views_never_read_private_files_or_initialize_providers(self):
        original_open = io.open
        protected = {'.env', 'stories.json', 'quicklinks.json', 'pipeline_config.json',
                     'canonical_stories.json', 'credentials.json', 'token.json', 'client_secret.json'}
        def guarded_open(file, mode='r', *args, **kwargs):
            if isinstance(file, (str, os.PathLike)):
                self.assertNotIn(Path(file).name, protected)
            self.assertFalse(any(flag in mode for flag in ('w', 'a', '+', 'x')), 'Public app attempted a persistent write')
            return original_open(file, mode, *args, **kwargs)
        with ExitStack() as stack:
            for module, name in [('google_sheets', 'GoogleSheetsAdapter'), ('google_drive', 'GoogleDriveAdapter'),
                                 ('openai_adapter', 'OpenAIEngineAdapter'), ('twilio_adapter', 'TwilioMessagingAdapter'),
                                 ('gmail_adapter', 'GmailIngestionAdapter')]:
                stack.enter_context(patch(f'pipeline.adapters.secondary.{module}.{name}.__init__',
                                          side_effect=AssertionError('Live provider initialized')))
            stack.enter_context(patch('io.open', side_effect=guarded_open))
            stack.enter_context(patch('dotenv.load_dotenv', side_effect=AssertionError('private environment file')))
            app = AppTest.from_file(str(APP), default_timeout=20).run()
            for destination in ('pipeline', 'intake', 'analytics', 'intelligence'):
                app.radio(key='public_navigation').set_value(destination).run()
                self.assertFalse(app.exception)
            app.button(key='public_reset').click().run()
            self.assertFalse(app.exception)

    def test_intelligence_and_career_compatibility_are_explicit(self):
        items = IntelligenceService.load_intel(Path(__file__).resolve().parents[3] / 'intel.json.example')
        self.assertEqual(len(items), 6)
        self.assertEqual(IntelligenceService.get_cue_cards(items, 'manufacturing')[0].id, 'intel-01')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'career.json'
            payload = [{'story_id': 'legacy', 'story_number': 1, 'title': 'Synthetic career story',
                        'hook': 'Original', 'problem': 'Original', 'turning_point': 'Original',
                        'result': 'Original', 'learning': 'Original'}]
            path.write_text(json.dumps(payload))
            before = path.read_bytes()
            self.assertEqual(IntelligenceService.load_career_stories(path)[0].story_id, 'legacy')
            self.assertEqual(path.read_bytes(), before)

    def test_workspace_switching_and_preservation(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(app.exception)
        # Verify initial Sales Rep workspace
        sales_records = app.session_state['_demo_store'].list_records()
        self.assertEqual(len(sales_records), 40)
        first_id = sales_records[0].id
        self.assertEqual(sales_records[0].fields['company'], 'Lumina HealthTech')

        # Make an edit in Sales Rep
        app.selectbox(key=f'public_0_stage_{first_id}').set_value('meeting_booked')
        next(b for b in app.button if b.label == 'Save Changes').click().run()
        self.assertFalse(app.exception)
        rec = next(r for r in app.session_state['_demo_store'].list_records() if r.id == first_id)
        self.assertEqual(rec.stage_id, 'meeting_booked')

        # Switch to B2B Services workspace
        app.selectbox(key='demo_workspace_selector').set_value('b2b_services').run()
        self.assertFalse(app.exception)
        b2b_records = app.session_state['_demo_store'].list_records()
        self.assertEqual(len(b2b_records), 20)
        self.assertEqual(b2b_records[0].fields['company'], 'Acme Global Consulting')
        self.assertIn('Client Opportunities', [s.label for s in app.metric])

        # Switch back to Sales Rep workspace and verify preservation of edit
        app.selectbox(key='demo_workspace_selector').set_value('sales_rep').run()
        self.assertFalse(app.exception)
        preserved_records = app.session_state['_demo_store'].list_records()
        self.assertEqual(len(preserved_records), 40)
        rec_preserved = next(r for r in preserved_records if r.id == first_id)
        self.assertEqual(rec_preserved.stage_id, 'meeting_booked')

    def test_opportunity_card_and_workspace_rendering(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(app.exception)
        rendered = str(app)
        # Check for card elements: Opportunity brief, badges, next action
        self.assertIn('Lumina HealthTech', rendered)
        self.assertIn('High Fit', rendered)
        self.assertIn('Next:', rendered)
        self.assertIn('ACV', rendered)
        self.assertIn('Edit', rendered)

