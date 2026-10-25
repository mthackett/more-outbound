"""Streamlit main entry point for More Outbound."""
import os
from pathlib import Path
import sys
import streamlit as st

# Ensure project root is in sys.path for Streamlit
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.adapters.primary.runtime import public_mode
from pipeline.domain.instance_loader import load_demo_config, InstanceConfigError
import pipeline.adapters.primary.public_ui as public_ui

try:
    is_public = public_mode(os.environ)
except ValueError:
    st.error("Invalid instance mode. Configure PIPELINE_MODE as demo.")
    st.stop()

if not is_public:
    st.error("Invalid instance mode. Configure PIPELINE_MODE as demo.")
    st.stop()

try:
    demo_config = load_demo_config(os.environ.get("PIPELINE_INSTANCE_CONFIG"))
except InstanceConfigError as exc:
    st.error(str(exc))
    st.stop()

st.set_page_config(page_title=demo_config.page_title, layout="wide")
public_ui.render_public(demo_config)
