# More Outbound implementation handoff

Updated 2026-10-18. **Checkpoints 0–4 complete; checkpoint 5 not started.** Read `.Agents/instructions.md` as controlling specification, then both references and `.Agents/demo-release-progress.md`. Do not repeat the audit or restart implementation.

## Current state / recoverable boundary
- Branch `master`; last commit before implementation: `dfb9b96` (`chore: add local PowerShell launcher`). Working tree contains only this implementation's source/tests/examples changes; initial tree was clean. A checkpoint commit is being prepared. Read actual `git log -1` and `git status` on resume rather than assuming this pre-commit value is current.
- Git needs command-local `-c safe.directory=C:/Users/mthac/Projects/more-outbound` because sandbox ownership differs. No global Git changes. `.git` requires write approval in this environment. `.Agents/` is ignored; only the progress/handoff may be force-added deliberately, never the entire directory.
- Public demo works from the existing entry point with `$env:PIPELINE_MODE='demo'; $env:DEMO_MODE='false'; .venv/Scripts/python.exe -m streamlit run job_pipeline/adapters/primary/app.py`. `PIPELINE_INSTANCE_CONFIG` optionally selects a public config. Private launch uses `PIPELINE_MODE=private`, `DEMO_MODE=false`; `PRIVATE_OFFLINE=true` enables synthetic private regression preview. Existing private `PIPELINE_CONFIG_PATH` retains its meaning.

## Completed work
- CP0: read required documents in full; baseline from isolated tracked-file snapshot: 253 tests, 4 failures, 2 errors. Missing pytest and ignored private canonical-story dependency explained all failures after fixing the harness's loopback guard.
- CP1: dashboard date/threshold/transport-error guards; no swallowing identity errors. Session-owned offline adapters, no Gmail/Twilio there, launch-only mode selection. Public branch executes before private settings/provider imports. Converted six pytest-style tests to unittest and provided temporary synthetic career-story fixtures. Added safe test runner.
- CP2: typed/versioned `PipelineInstanceConfig` capabilities; strict read-only public loader, separate config examples; generic records plus explicit lossless legacy snapshots. JobPosting, Sheets persistence, IDs, compensation/recovery semantics preserved.
- CP3: config-driven public navigation/forms/fields/cards/table/stages/editing/notes/search/pagination/reset. New domain-neutral IntelligenceService with six synthetic account playbooks and explicit career compatibility. Removed tracked `stories.json.example`; legacy file loader remains tested with temporary synthetic JSON. No private stories changed.
- CP4: deterministic 40-account dataset; historical unique-ID KPI registry/funnel; session-local reset and config fingerprint invalidation. Exact fixture counts: 40 total / 30 contacted / 17 replied / 10 booked / 4 opportunities / 32 active / $1,128,000 active ACV. Rates 33.3%, 56.7%, 58.8%. Cancellation/disqualification retain booking history; malformed evidence ignored; no inferred intermediate milestones; zero denominator displays —.

## Architecture decisions / differences from audit
- Keep mature private workflow in the same application entry point; route public views early into `public_ui.py`, before loading private files/providers. This avoids rewriting the private application.
- Public config uses a separate read-only loader; never use permissive legacy settings fallback in public mode. Strict schema rejects unsafe adapters/integrations/private features and local branding-file references.
- Generic PipelineRecord is independent of JobPosting. Legacy snapshots preserve full payloads/unknown Sheet columns; generic projections are read-only. Private editing still uses original ports/serializers. No Sheet migration or private JSON normalization.
- No process-wide demo state. Per-session adapter + config fingerprint; switching config clears stale state. Public uses only fixed synthetic fixture/intelligence files and in-memory mutations.
- Namespace deliberately deferred until behavior stabilized. Avoid root `sys.modules['job_pipeline']=pipeline`: nested class/state duplication risk. If retaining compatibility, use narrowly tested leaf facades/CLI wrappers with canonical module identity.
- Standard unittest is sufficient; no pytest installation needed.

## Modified files/modules (pre-rename)
- Existing: `job_pipeline/adapters/primary/app.py`, `analytics_dashboard_ui.py`, `domain/models.py`; tests `test_job_signals`, `test_role_intelligence_deferred`, `test_story_bank`, `test_ui_responsiveness_and_search`, `test_v152_opportunity_card_flag`. Deleted tracked `stories.json.example` only.
- New primary modules: `runtime.py`, `dashboard_data.py`, `public_ui.py`.
- New domain modules: `instance_config.py`, `instance_loader.py`, `records.py`, `intelligence_service.py`, `outreach_metrics.py`.
- New adapter/port: `adapters/secondary/memory_records.py`, `ports/record_port.py`.
- New tests: `test_demo_safety.py`, `test_instance_records.py`, `test_public_ui.py`, `test_outreach_demo.py`.
- New assets/config/tool: `config/demo.json`, `config/private.json.example`, `intel.json.example`, `job_pipeline/examples/fixtures/demo_prospects.json`, `tools/run_tests.py`.
- Progress/handoff files are ignored by default. No namespace move, launcher/documentation edit, or private data change has begun.

## Verification / defects / limitations
- Latest full command: `.venv/Scripts/python.exe tools/run_tests.py`: **280 tests, all pass, 0 skips**, 20.342s. Temp log `more-outbound-tests-zuso_2pn/test-results.log`. Earlier checkpoint totals: 264, 269, 274. Details/corrections recorded in progress log.
- Runner copies tracked + nonignored untracked source to system temp, strips provider/config environment, disables dotenv, blocks external socket connections, allows loopback for Windows Streamlit AppTest. Tests do not run beside private data.
- Public AppTests create/edit/stage/note/reset, visit every destination, validate config-driven labels, absence of private controls/IDs, and no private file access, persistent writes, dotenv reads or live constructors. Two Streamlit sessions and concurrent adapters remain isolated. Legacy recovery/compensation/intake/screening tests pass offline.
- SHA-256 verification: **618 protected files unchanged**. Baseline hashes are only in system temp `more-outbound-protected-hashes.json`; do not publish their contents. Covers private JSON/env/credentials, ignored canonical stories and all existing output_reports files.
- Known remaining release work: neutral namespace; resume routing test coverage for four families (router currently lacks explicit marketing_operations/ai_automation mappings); launchers/deployment/docs; clean headless server/entry-point smoke verification. Hosting not deployed or authenticated. No live Google reads/writes authorized.
- Existing private CLI/batch recovery differences documented in architecture remain out of scope. Public UI is config-driven; private job schema/workflow remains specialized for compatibility. No OAuth/login, outreach sending, enrichment, background workers or migrations added.
- Only observed intermediate failures were resolved test harness/test assertion issues (see progress); no known failing current tests. Streamlit emits deprecated `use_container_width` notices inherited from legacy UI.

## Exact next actions
1. Finish checkpoint 4 commit: inspect explicit changed paths, `git diff --check`, stage only implementation source/tests/config/synthetic fixtures plus explicitly requested progress/handoff. Exclude all ignored private files. Commit if environment permits; otherwise document approval block. Update this document with commit result.
2. Start CP5 in isolation: rename tracked/nonignored application source to `pipeline/` using verified workspace-contained paths. **Do not move ignored `job_pipeline/domain/canonical_stories.json` or caches/private artifacts.** Provide private story loader fallback to that original path so existing data stays in place.
3. Update canonical imports, test mock patch strings, resource/test paths, safe runner discovery, `Procfile`, `railway.json`, `start.ps1`, docs and env example. Decide and test narrow compatibility for documented old CLI commands/imports; no blanket root alias.
4. Add/verify explicit resume routing for RevOps, GTM Engineering, Marketing Operations, AI Automation, plus empty/missing/ambiguous/fallback cases. Preserve original behavior for other families.
5. Document public/private launch commands, config surface/metric semantics, optional provider dependencies and hosting isolation. Public deploy command must explicitly select demo. Update runtime version requirements to tested compatible versions without unrelated upgrades.
6. Run full isolated suite, credentials-free public headless server health + AppTest actions, offline private/CLI/import smokes; compare protected hashes again, inspect final diff. Record limitations and exact counts. Update progress/handoff; make focused CP5 commit if permitted. Do not publish/deploy without user request.

## Ready-to-use continuation prompt
Continue the More Outbound demo release. Read `.Agents/instructions.md`, `.Agents/ARCHITECTURE.md`, `.Agents/Demo Release Audit.md`, `.Agents/demo-release-progress.md`, and `.Agents/implementation-handoff.md`. Check actual Git branch/log/status; verify CP4 with `.venv/Scripts/python.exe tools/run_tests.py` if needed. CP0–4 are implemented and tested; do not redo the audit. Finish any pending checkpoint commit, then resume the exact CP5 actions above. Preserve every private file and Google/recovery contract; only use synthetic/offline verification. Keep progress and handoff current and stop at a verified boundary if resources are constrained.
