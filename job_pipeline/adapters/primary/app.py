"""Legacy Streamlit path, delegated to the canonical application source."""
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
runpy.run_path(str(root / 'pipeline/adapters/primary/app.py'), run_name='__main__')
