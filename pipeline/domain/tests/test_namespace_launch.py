import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from pipeline.launch import launch_command


class TestNamespaceLaunch(unittest.TestCase):
    def test_legacy_leaf_modules_share_identity(self):
        for name in ('domain.models', 'domain.services', 'domain.story_bank', 'logger', 'version'):
            legacy = importlib.import_module('job_pipeline.' + name)
            canonical = importlib.import_module('pipeline.' + name)
            self.assertIs(legacy, canonical)
        from job_pipeline.domain.models import JobPosting as legacy_job
        from pipeline.domain.models import JobPosting
        self.assertIs(legacy_job, JobPosting)

    def test_reverse_import_order_in_fresh_process(self):
        code = "import job_pipeline.domain.models as old; import pipeline.domain.models as new; assert old is new; assert old.JobPosting is new.JobPosting"
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_legacy_cli_and_batch_imports_are_canonical(self):
        from job_pipeline.adapters.primary.cli_runner import evaluate_single_job as old_cli
        from pipeline.adapters.primary.cli_runner import evaluate_single_job
        from job_pipeline.adapters.primary.sheets_batch import run_batch_pipeline as old_batch
        from pipeline.adapters.primary.sheets_batch import run_batch_pipeline
        self.assertIs(old_cli, evaluate_single_job)
        self.assertIs(old_batch, run_batch_pipeline)

    def test_legacy_streamlit_entry_launches_public_safely(self):
        root = Path(__file__).resolve().parents[3]
        with patch.dict(os.environ, {'PIPELINE_MODE': 'demo', 'DEMO_MODE': 'true'}):
            app = AppTest.from_file(str(root / 'job_pipeline/adapters/primary/app.py'), default_timeout=20).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state['_demo_store'].list_records()), 40)

    def test_launch_modes_use_same_source_and_override_conflicting_environment(self):
        with patch.dict(os.environ, {'PIPELINE_MODE': 'private', 'DEMO_MODE': 'false'}):
            public, env = launch_command('demo', 8510, '127.0.0.1')
        private, private_env = launch_command('private', 8511, '127.0.0.1')
        self.assertEqual(public[4], private[4])
        self.assertIn('pipeline', public[4])
        self.assertEqual(env['PIPELINE_MODE'], 'demo')
        self.assertEqual(env['DEMO_MODE'], 'true')
        self.assertEqual(private_env['PIPELINE_MODE'], 'private')

    def test_private_seed_fallback_does_not_move_or_rewrite(self):
        import pipeline.domain.story_bank as module
        from pipeline.domain.story_bank import StoryBankService
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            canonical_module = root / 'pipeline/domain/story_bank.py'
            seed_path = canonical_module.with_name('canonical_stories.json')
            legacy_path = root / 'job_pipeline/domain/canonical_stories.json'
            legacy_path.parent.mkdir(parents=True)
            legacy_path.write_text('[]', encoding='utf-8')
            with patch.object(module, '__file__', str(canonical_module)), \
                 patch.object(StoryBankService, 'CANONICAL_SEEDS_PATH', str(seed_path)):
                self.assertEqual(StoryBankService.get_default_seeds(), [])
            self.assertEqual(legacy_path.read_text(), '[]')
            self.assertFalse(seed_path.exists())
