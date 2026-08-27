# PyOD Cross-Cutting Troubleshooting

Read this before diving into a sub-skill-specific troubleshooting page when a
PyOD task fails at installation, import, optional dependency, data validation,
CLI, or workflow routing.

| Symptom | Likely cause | Route / recovery |
|---|---|---|
| `ModuleNotFoundError` for `pyod` | PyOD is not installed in the selected Python | Install `pyod`, then run `python -c "import pyod; print(pyod.__version__)"` and `pyod info`. |
| Optional module missing (`torch`, `torch_geometric`, `xgboost`, `suod`, `combo`, `pythresh`, `mcp`, `sentence_transformers`, `openai`, `transformers`, `librosa`, `soundfile`) | Workflow requires a PyOD extra not installed by base PyOD | Install the exact extra only for the selected workflow; see `installation-and-extras.md`, `specialized-modalities`, or `model-operations`. |
| `pyod info` reports MCP extra not installed | Base install is healthy but `pyod[mcp]` is absent | Install `pyod[mcp]` only if an MCP server is required. Do not treat this as a base install failure. |
| Detector labels look implausible | Contamination/threshold mismatch or raw scores overinterpreted | Inspect raw scores and top ranks; tune contamination with labels/domain knowledge. Direct detectors route to `classic-detectors`; ADEngine reports route to `automated-lifecycle`. |
| Non-numeric or mixed data fails validation | Classic detectors expect numeric arrays | Encode tabular categoricals, use appropriate text/image/audio embedding routes, or use time-series/graph data structures. |
| GPU is present but PyOD does not use it | Core PyOD does not imply GPU runtime; torch classes may run CPU unless configured | Probe torch/CUDA explicitly and only claim accelerator support after runtime verification. |
| Model artifact loading refuses to run without `trusted=True` | PyOD persistence deliberately blocks untrusted pickle/joblib deserialization | Use `model-operations` and load only trusted artifacts. |
| Task asks to edit PyOD source or run repo tests | This is a maintainer workflow, not package usage | Route to `repo-maintenance` and choose focused tests by edited area. |

## Quick triage commands

```bash
python - <<'PY'
import importlib.util
import pyod
print("pyod", pyod.__version__)
for mod in ["torch", "torch_geometric", "xgboost", "suod", "combo", "pythresh", "mcp"]:
    print(mod, importlib.util.find_spec(mod) is not None)
PY
pyod info
```

Then choose the nearest sub-skill rather than installing broad extras or running
large examples by default.
