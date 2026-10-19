# More Outbound

More Outbound is a configuration-driven pipeline intelligence demo and a preserved private job-application workspace, sharing one Python/Streamlit codebase.

The public demo contains 40 fictional B2B accounts. Add prospects, change stages, record activities, explore account intelligence, and reset your session. Historical conversion metrics update immediately. There are no accounts, API credentials, enrichment calls, or outbound messages.

## Launch

Python 3.12 is the tested runtime. From the repository root:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-demo.txt
.venv/Scripts/python.exe -m pipeline.launch --mode demo
```

Open http://localhost:8501. Optional public config: `$env:PIPELINE_INSTANCE_CONFIG='config/demo.json'`. Missing/invalid configuration shows a safe error. Public mode does not load private settings, credentials, stories, quicklinks, or provider adapters, even when provider environment variables exist.

For the existing private instance:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pipeline.launch --mode private
```

Keep your existing `.env`, `pipeline_config.json`, credentials, tokens, `stories.json`, quicklinks and Google resources. Do not replace these with examples. `PIPELINE_CONFIG_PATH` still selects legacy private settings. `start.ps1` defaults to private; `./start.ps1 -Mode demo` launches public. A private synthetic preview uses `$env:PRIVATE_OFFLINE='true'` before the private command; remove that environment variable to reconnect. This preview is for the private workflow and can load local private preferences; it is not the public deployment.

## Configuration and metrics

`config/demo.json` defines versioned identity/branding, ordered stages, active/terminal states, milestone IDs, typed fields, navigation, feature flags, action labels, integration capabilities, storage, dashboard modules and metrics. `config/private.json.example` illustrates private branding without changing user preferences. Public config uses a strict read-only loader; private settings retain their existing compatibility loader.

Fields support text, long text, currency and ISO dates, required validation, visibility/editability, intake/card/table placement and finite formatters. Supported field keys: company, contact, title, acv, industry, source, next_action, next_action_date, notes. Public storage must be memory; all integrations and private resume/screening/report features must be disabled. Custom stage IDs can use `seed: empty`; the B2B seed requires its configured stage IDs. Unknown fields/metrics, duplicate IDs and incompatible features fail validation. JSON never executes formulas.

| Metric | Definition | Seed result |
|---|---|---|
| Meeting Booking Rate | Contacted records that ever booked / contacted records | 10 / 30 = 33.3% |
| Reply Rate | Contacted records that ever replied / contacted records | 17 / 30 = 56.7% |
| Reply-to-Meeting Rate | Replying records that ever booked / replying records | 10 / 17 = 58.8% |
| Active Pipeline ACV | ACV of records currently in configured active, nonterminal stages | $1,128,000 |

Each stable ID counts once. Recorded stage/activity achievements survive later stage changes, disqualification and meeting cancellation. Cancellation alone does not imply a booking. Missing/malformed history is ignored, and intermediate stages are never inferred. Zero denominators display an em dash. The funnel counts records achieving every preceding milestone: 40 ? 30 ? 17 ? 10 ? 4. Pipeline metrics describe the entire session, independently of the list filters.

## Architecture and private compatibility

Canonical code lives in `pipeline/`: domain models/services, ports, primary UI/CLI drivers and secondary adapters. Public `PipelineRecord` is independent of `JobPosting`; lossless legacy snapshots retain full private payloads. Existing Sheets mappings, recovery identity/source/completion checks, compensation precedence, screening, resume references and career intelligence remain intact. No production schema migration is needed. Private workflow screens remain specialized; this release is not a generic CRM builder.

Public account intelligence is in `intel.json.example`. Private `StoryBankService` and its legacy JSON format remain supported. An ignored canonical-story seed under `job_pipeline/domain/` stays in place and is read through a compatibility fallback.

The old Streamlit path, single-job/batch/OAuth command entry points, and legacy models/services/story-bank/logger/version imports have narrow wrappers. Canonical and legacy leaf imports share module/class identity. Arbitrary undocumented nested legacy imports are not guaranteed. New code must use `pipeline.*`.

Private commands remain available:

```powershell
.venv/Scripts/python.exe -m pipeline.adapters.primary.cli_runner --jd jd.txt
.venv/Scripts/python.exe -m pipeline.adapters.primary.sheets_batch
.venv/Scripts/python.exe -m pipeline.setup_oauth
```

These are private operations and can perform real I/O when configured. Run automated checks through the isolated runner instead:

```powershell
.venv/Scripts/python.exe tools/run_tests.py
```

The runner uses disposable source copies, synthetic fixtures, no dotenv loading, stripped provider environment and blocked external sockets. Loopback is allowed for Streamlit tests. Runtime dependencies for public use are Streamlit and Pydantic; the full requirements add Google/OpenAI/document/clipboard support. Pytest is unnecessary. No new package-distribution build is introduced; launch from a source checkout.

## Hosting and limitations

See [Demo deployment](docs/demo-deployment.md). Procfile and Railway explicitly launch demo mode. Public edits are session-local, disappear when that session expires or the server restarts, and never update private Sheets/Drive. Reset affects only that session. Do not enter sensitive data into a public demonstration. Hosting-provider deployment and authenticated Google verification require separate operational checks; this release does not add private-instance authentication.
