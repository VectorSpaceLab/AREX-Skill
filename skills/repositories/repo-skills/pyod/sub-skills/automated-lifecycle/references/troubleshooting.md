# Automated Lifecycle Troubleshooting

Use this matrix when ADEngine, CLI, MCP, or the agentic session workflow fails.
For detector-family details route to `classic-detectors`; for optional modality
backends route to `specialized-modalities`.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `pyod: command not found` | Console script is not on `PATH` for the active Python environment. | Run `python -m pyod.cli --help` from the environment that has PyOD installed. If that fails, install or activate the correct environment. |
| `pyod info` says `MCP extra: NOT INSTALLED` | Core PyOD is installed without the optional `mcp` extra. | Use direct `ADEngine` APIs, or install the MCP extra with a correctly quoted extras spec such as `pip install 'pyod[mcp]'`. |
| `pyod mcp serve` exits nonzero with an install hint | The optional `mcp` package is missing. | Install `pyod[mcp]`, then rerun. Do not treat this as an ADEngine failure; core detection still works. |
| Importing `pyod.mcp_server` exits the process | Very old or incompatible PyOD behavior. Current PyOD should be import-safe without `mcp`. | Upgrade PyOD. Until then, avoid importing the server module in probes and use direct ADEngine APIs. |
| `pyod install skill --project` ran but Codex/Claude did not activate `od-expert` | The agent session has not reloaded, or the command ran outside the intended project root. | Run `pyod info` from the project directory, confirm `./skills/od-expert/SKILL.md`, and restart the agent session. |
| `pyod install skill` helped Claude Code but not Codex | Codex reads project-local `./skills/`, not Claude's user-global skill directory. | Run `pyod install skill --project` in the project directory and restart Codex. |
| `plan_detection` returns `note="no_valid_plan"` and empty `detector_name` | All matching and fallback detectors were excluded, or profile fields do not match any rule. | Remove exclusions, provide a more complete profile, or use `engine.get_kb_for_routing` plus `engine.make_plan` to choose valid shipped detectors manually. |
| `build_detector` raises `ValueError: Unknown detector` | Detector name is misspelled, wrong case, or not in the PyOD knowledge base. | Use `engine.list_detectors(status="shipped")` and exact case-sensitive names. |
| `build_detector` raises for a planned detector | The knowledge base knows about an unshipped planned detector. | Choose a shipped detector or route to a different modality/workflow. |
| Results vary across identical runs | Stochastic detector internals and no fixed seed. | Construct `ADEngine(random_state=<int>)`. For deep detectors, also seed the framework stack and verify deterministic settings. |
| `engine.run(state)` raises phase error | Session methods were called out of order. | Use `start -> plan -> run -> analyze -> report/iterate`. `recover` iteration is the only iterate action accepted immediately after `run` when failures occurred. |
| `engine.iterate(state, ...)` raises before analysis | Most iteration actions require an analyzed state. | Call `engine.analyze(state)` first. For detector failures right after `run`, use `engine.iterate(state, {"action":"recover"})`. |
| All detectors fail inside `engine.run(state)` | Bad data shape, nonnumeric values, NaNs, missing optional dependency for selected modality, or unsuitable detector selection. | Inspect each error entry in `state.results`; validate finite 2D numeric arrays for tabular work; install required modality extras only when needed; or reroute to a supported detector family. |
| Some detectors fail but consensus exists | ADEngine continues with successful detectors. | Either analyze with caveats or run `engine.iterate(state, {"action":"recover"})` to substitute failed detectors, then rerun. |
| Quality verdict is `low` or agreement is poor | Detectors rank samples differently; data may be near-noise, poorly scaled, or an inappropriate modality. | Report uncertainty. Inspect `state.consensus["disagreements"]`, scale features for distance-based detectors, adjust detector set, or ask for labels/domain review. |
| Too many anomalies | Contamination is too high for the user's review capacity or domain prior. | Use `engine.iterate(state, {"action":"adjust_contamination", "value": <lower_fraction>})`, rerun, analyze, and report the changed assumption. |
| Too few or no anomalies | Contamination is too low, detector is insensitive, or data has weak signal. | Use `suggest_next_step(..., feedback="missed anomalies")`, raise contamination, or try an alternative detector. |
| Feature explanations are missing | `explain_findings` was called without original `X`, or feature contribution computation is not applicable. | Pass the same feature matrix as `X`; pass `feature_names` for human-readable labels. |
| `engine.report(state)` raises `No successful detectors` | State is analyzed but every detector failed. | Recover or replan; do not generate a report that implies successful anomaly detection. |
| MCP `plan_detection` returns `Invalid JSON` | Client sent Python repr, malformed JSON, or a JSON list/string instead of an object. | Serialize with `json.dumps(profile_dict)` and `json.dumps(constraints_dict)`. Use double quotes and object payloads. |
| MCP `build_detector` returns `Invalid parameter name` | A plan contains unsafe parameter keys that are not Python identifiers or are Python keywords. | Sanitize plan params; only use real detector constructor keyword names. |
| MCP `run_detection` returns `Failed to load training data` | Bad path, unsupported extension, malformed file, or CSV/NPZ shape surprise. | Prefer `.npy` feature matrices for automated handoffs. For CSV, remember the first row is skipped and the last column is dropped when multiple columns exist. |
| MCP `analyze_results` or `explain_findings` returns `Invalid result JSON` | The result payload was edited, not from `run_detection`, or score/label arrays contain nonnumeric values. | Re-run `run_detection` and pass the returned JSON string unchanged. |
| User reveals labels after an unsupervised ADEngine run | ADEngine lifecycle is unsupervised; labels change the problem. | Preserve the unsupervised report if requested, but recommend supervised validation or detector paths such as XGBOD in the appropriate detector guidance. |
| High-stakes context such as medical, fraud, legal, or safety | Label-free anomaly scores are decision support only. | Ask for validation data or domain review. Report assumptions, detector agreement, threshold/contamination, and caveats prominently. |
| Optional text/image/audio/graph route fails with import errors | The core install does not include those extras. | Route to `specialized-modalities` for exact extras and CPU/GPU/backend guidance. Do not install broad `all` extras unless the user explicitly needs them. |

## Pre-report checklist for agents

Before returning results to a user:

1. State the data type, sample/feature shape, and any override used.
2. State detectors used, contamination/threshold assumption, and whether
   `random_state` was fixed.
3. Report anomaly ratio as a fraction or percent, not only raw scores.
4. Include detector agreement and quality verdict as diagnostics, not proof.
5. Explain top rows with feature contributions when possible.
6. Include caveats for scaling, missing labels, optional backend limitations, and
   high-stakes use.
7. If `next_action` asks for confirmation or iteration, do not silently report as
   final.
