# Demo deployment

Use a source checkout with Python 3.12. Install `requirements-demo.txt` for public-only hosting, or `requirements.txt` for the existing private integration dependencies. Public runtime does not import those optional providers. The tested environment is Streamlit 1.66.0 and Pydantic 2.14.1.

Public server command (Railway/Procfile already select this mode):

```sh
python -m pipeline.launch --mode demo --port=$PORT --address=0.0.0.0
```

For Streamlit Community Cloud, use `pipeline/adapters/primary/app.py` as the main file and set `PIPELINE_MODE=demo` in the process environment before startup. Do not configure a public host with private credentials or mount private settings/output directories. Explicit demo mode also bypasses these resources if they accidentally exist. Public config defaults to `config/demo.json`; `PIPELINE_INSTANCE_CONFIG` may point to another validated public JSON file. A missing/invalid config never selects live adapters.

Private hosting must explicitly use `python -m pipeline.launch --mode private --port=$PORT --address=0.0.0.0`, its own secrets/storage, and suitable access restrictions. No OAuth visitor login or multi-tenant private storage was added. CORS/XSRF protection is enabled; Streamlit usage telemetry is disabled. Verify reverse-proxy/websocket configuration on the intended host.

The public adapter is stored only in `st.session_state`, never a process cache. Every visitor receives a fresh deep copy of 40 fictional records. Reset restores only that session. Changing the instance config fingerprint clears cached adapters/data/widgets. Browser disconnection retention follows Streamlit settings; do not promise durable edits across expiry, restart or deployment. Account intelligence is read from the synthetic `intel.json.example` file. There is no email/SMS execution, enrichment, LLM call, or persistent application write in public mode.

Before publication: run `.venv/Scripts/python.exe tools/run_tests.py`; inspect both pages and reset in separate browser sessions; confirm the public process has the intended mode. Automated AppTest tests cover mutations, all navigation, private-data guards and isolation. The release progress log distinguishes completed local checks from unverified hosting/live Google behavior. The code has not been deployed by the implementation agent.
