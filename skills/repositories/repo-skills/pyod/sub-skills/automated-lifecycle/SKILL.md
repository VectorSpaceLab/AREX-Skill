---
name: automated-lifecycle
description: "Operate PyOD's ADEngine lifecycle, agentic investigation sessions,
  CLI activation commands, and MCP JSON tools as self-contained PyOD package
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# PyOD Automated Lifecycle

Use this sub-skill when a task asks an agent to automate anomaly detection with
PyOD instead of hand-picking a single detector: profile data, choose a detector
or detector set, run detection, analyze/explain results, iterate on feedback,
generate reports, install PyOD's packaged `od-expert` activation skill, or expose
PyOD through MCP-compatible tools.

## Route here for

- `ADEngine` lifecycle APIs: `profile_data`, `plan_detection`,
  `build_detector`, `detect`, `run_detection`, `analyze_results`,
  `explain_findings`, `suggest_next_step`, `generate_report`, and the session
  methods `start`, `plan`, `run`, `analyze`, `iterate`, `report`,
  `investigate`.
- Agent state handling: `InvestigationState`, `state.next_action`, multi-detector
  consensus, quality diagnostics, iteration, and report handoff.
- CLI activation surfaces: `pyod info`, `pyod install skill`,
  `pyod install skill --project`, `pyod install skill --list`, and
  `pyod mcp serve`.
- MCP wrappers: the ten registered tools, JSON payload shapes, JSON error
  returns, and missing-`mcp` behavior.
- Safe smoke verification of a local PyOD install without starting a server.

## Route elsewhere

- Low-level detector APIs, detector-family trade-offs, `BaseDetector` attributes,
  and synthetic tabular examples -> `classic-detectors`.
- Time-series, graph, embedding, text/image/audio, torch, PyG, and other modality
  backends -> `specialized-modalities`.
- Persistence, thresholding, score combination, SUOD/XGBOD operational extras ->
  `model-operations`.
- Packaged skill source regeneration, test maintenance, and repository internals
  -> `repo-maintenance`.

## Load these bundled files

| File | When to use it |
|---|---|
| [references/adengine-api.md](references/adengine-api.md) | Need exact ADEngine method contracts, input/output shapes, deterministic `random_state` behavior, result dictionaries, report formats, or knowledge-query helpers. |
| [references/agentic-workflows.md](references/agentic-workflows.md) | Need to drive the stepwise session workflow, interpret `InvestigationState` fields and `next_action`, recover detector failures, or run an od-expert-style agent investigation. |
| [references/cli-and-mcp.md](references/cli-and-mcp.md) | Need PyOD CLI commands, od-expert install modes, MCP server availability, MCP tool list, file loading rules, JSON payload examples, or JSON error handling. |
| [references/troubleshooting.md](references/troubleshooting.md) | Need symptom-to-recovery guidance for CLI/MCP install issues, malformed JSON, missing optional extras, phase-order errors, noisy results, nondeterminism, or agent activation problems. |
| [scripts/adengine_smoke.py](scripts/adengine_smoke.py) | Run a safe deterministic ADEngine smoke test. Optional flags probe CLI and MCP availability without starting an MCP server. |

## Minimal operating pattern

```python
from pyod.utils.ad_engine import ADEngine

engine = ADEngine(random_state=42)  # deterministic shallow-detector routing/run
state = engine.start(X, data_type="tabular")
state = engine.plan(state, constraints={"max_detectors": 2})
state = engine.run(state)
state = engine.analyze(state)

if state.next_action["action"] == "report_to_user":
    report = engine.report(state, format="text")
else:
    # Ask or iterate based on state.next_action before reporting.
    follow_up = state.next_action
```

Treat ADEngine quality metrics as descriptive, label-free diagnostics. They help
triage agreement and cutoff stability; they do not prove anomaly correctness.
For high-stakes domains or available labels, add domain/label validation and
route supervised detector work to the appropriate PyOD detector guidance.
