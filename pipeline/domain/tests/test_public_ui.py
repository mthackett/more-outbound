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
        next(b for b in app.button if b.label in ('Add Note', 'Log Activity')).click().run()
        record = app.session_state['_demo_store'].list_records()[-1]
        self.assertEqual(record.stage_id, 'meeting_booked')
        self.assertEqual(record.activities[-1].text, 'Synthetic discovery booked.')
        for destination in ('analytics', 'intelligence'):
            app.radio(key='public_navigation').set_value(destination).run()
            self.assertFalse(app.exception)
        app.session_state['_demo_store'].reset()
        app.run()
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
            app.session_state['_demo_store'].reset()
            app.run()
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
        self.assertIn('(617) 555-0193', rendered)

    def test_safe_synthetic_domains_and_reserved_phone_numbers(self):
        fixtures_dir = Path(__file__).resolve().parents[2] / 'examples/fixtures'
        sales_records = json.loads((fixtures_dir / 'demo_prospects.json').read_text(encoding='utf-8'))
        b2b_records = json.loads((fixtures_dir / 'demo_b2b_services.json').read_text(encoding='utf-8'))

        import re
        phone_pattern = re.compile(r'^\(([2-9][0-9]{2})\) 555-01([0-9]{2})$')

        for rec in sales_records:
            fields = rec['fields']
            email = fields.get('email', '')
            website = fields.get('website', '')
            phone = fields.get('phone', '')

            if email:
                self.assertTrue(email.endswith('.example.com'), f'Unsafe email domain: {email}')
            if website:
                self.assertTrue('.example.com' in website, f'Unsafe website domain: {website}')
            if phone:
                m = phone_pattern.match(phone)
                self.assertIsNotNone(m, f'Phone not in reserved (NPA) 555-0100..0199 range: {phone}')
                last_two = int(m.group(2))
                self.assertTrue(0 <= last_two <= 99)

        for rec in b2b_records:
            fields = rec['fields']
            email = fields.get('email', '')
            if email:
                self.assertTrue(email.endswith('.example.com'), f'Unsafe B2B email domain: {email}')

    def test_phone_field_optional_creation_and_persistence(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(app.exception)
        app.radio(key='public_navigation').set_value('intake').run()

        # 1. Test creation with minimal required data (no phone)
        app.text_input(key='public_0_intake_company').set_value('Minimal Prospect LLC')
        app.text_input(key='public_0_intake_contact').set_value('Jordan Minimal')
        next(b for b in app.button if b.label == 'Add Prospect').click().run()
        self.assertFalse(app.exception)

        created_min = app.session_state['_demo_store'].list_records()[-1]
        self.assertEqual(created_min.fields['company'], 'Minimal Prospect LLC')
        self.assertEqual(created_min.fields.get('phone', ''), '')

        # 2. Test creation with valid reserved phone number
        app.text_input(key='public_0_intake_company').set_value('Phone Prospect Corp')
        app.text_input(key='public_0_intake_contact').set_value('Taylor Phone')
        app.text_input(key='public_0_intake_phone').set_value('(415) 555-0142')
        next(b for b in app.button if b.label == 'Add Prospect').click().run()
        self.assertFalse(app.exception)

        created_phone = app.session_state['_demo_store'].list_records()[-1]
        self.assertEqual(created_phone.fields['company'], 'Phone Prospect Corp')
        self.assertEqual(created_phone.fields['phone'], '(415) 555-0142')

    def test_analytics_percentage_formatting_and_visual_funnel(self):
        from pipeline.domain.outreach_metrics import conversion_funnel
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(app.exception)
        records = app.session_state['_demo_store'].list_records()
        cfg = app.session_state['_demo_store'].config

        funnel = conversion_funnel(records, cfg)
        self.assertEqual(len(funnel), 5)
        self.assertEqual([r['Count'] for r in funnel], [40, 30, 17, 10, 4])
        self.assertEqual(funnel[0]['Conversion from Previous'], '—')
        self.assertEqual(funnel[0]['Overall Conversion'], '100.0%')
        self.assertEqual(funnel[1]['Conversion from Previous'], '75.0%')
        self.assertEqual(funnel[1]['Overall Conversion'], '75.0%')
        self.assertEqual(funnel[2]['Conversion from Previous'], '56.7%')
        self.assertEqual(funnel[2]['Overall Conversion'], '42.5%')
        self.assertEqual(funnel[3]['Conversion from Previous'], '58.8%')
        self.assertEqual(funnel[3]['Overall Conversion'], '25.0%')
        self.assertEqual(funnel[4]['Conversion from Previous'], '40.0%')
        self.assertEqual(funnel[4]['Overall Conversion'], '10.0%')

        # Navigate to analytics and ensure visual funnel and table render cleanly
        app.radio(key='public_navigation').set_value('analytics').run()
        self.assertFalse(app.exception)
        all_md = " ".join(m.value for m in app.markdown)
        self.assertIn('Conversion Pipeline Funnel', all_md)
        self.assertTrue(any('Historical Conversion Funnel' in s.value for s in app.subheader))

    def test_sales_playbooks_navigation_and_content(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(app.exception)

        # Sales Rep workspace should show Sales Playbooks
        app.radio(key='public_navigation').set_value('intelligence').run()
        self.assertFalse(app.exception)
        rendered = str(app)
        self.assertIn('Sales Playbooks', rendered)
        self.assertIn('Manufacturing Handoffs', rendered)

        all_md = " ".join(m.value for m in app.markdown)
        self.assertIn('Context & Business Scenario', all_md)
        self.assertIn('Common Pain Points', all_md)
        self.assertIn('Signals to Investigate', all_md)
        self.assertIn('Discovery Questions', all_md)
        self.assertIn('Suggested Outreach Angles', all_md)
        self.assertIn('Potential Objections', all_md)
        self.assertIn('SYNTHETIC PLAYBOOK', all_md)

        # Verify discovery questions and outreach angles exist in copyable code blocks
        all_code = " ".join(c.value for c in app.code)
        self.assertIn('where does a signed order typically stall', all_code.lower())
        self.assertIn('frame the conversation around eliminating quote-to-fulfillment discrepancies', all_code.lower())
        self.assertTrue(len(app.code) >= 6)

        # Switch to B2B Services workspace
        app.selectbox(key='demo_workspace_selector').set_value('b2b_services').run()
        self.assertFalse(app.exception)
        app.radio(key='public_navigation').set_value('intelligence').run()
        self.assertFalse(app.exception)
        b2b_rendered = str(app)
        self.assertTrue('Client Intelligence' in b2b_rendered or 'Intelligence' in b2b_rendered)


