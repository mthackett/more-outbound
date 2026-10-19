"""Compatibility for the previously documented batch command."""
import os
import sys
from pipeline.adapters.primary.sheets_batch import run_batch_pipeline

if __name__ == '__main__':
    run_batch_pipeline(demo_mode='--demo' in sys.argv or os.environ.get('DEMO_MODE', 'false').lower() == 'true')
