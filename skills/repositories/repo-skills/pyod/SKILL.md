---
name: pyod
description: "Operate PyOD anomaly-detection workflows across classic detectors,
  ADEngine automation, specialized modalities, model operations, and source
  maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# PyOD Repo Skill

Use this skill when a task involves PyOD, Python outlier/anomaly detection,
`pyod.models`, `ADEngine`, PyOD's agentic `od-expert` skill, PyOD MCP tools,
model persistence, thresholding, optional detector extras, or maintaining the
PyOD source repository.

PyOD is a Python anomaly-detection library with a classic `fit`/`predict` API,
ADEngine lifecycle orchestration, and optional routes for time series, graph,
text/image/audio embeddings, neural detectors, agent skills, and MCP.

## Install and quick check

```bash
pip install pyod
pyod info
python - <<'PY'
import pyod
from pyod.models.iforest import IForest
print(pyod.__version__, IForest)
PY
```

Read [references/installation-and-extras.md](references/installation-and-extras.md)
when choosing optional extras. Use [scripts/check_pyod_install.py](scripts/check_pyod_install.py)
for a read-only import/optional-module smoke check.

## Route by task

| Task intent | Read |
|---|---|
| Fit one or more classic tabular detectors, inspect `decision_scores_`, tune contamination, generate synthetic fixtures, evaluate scores with labels | [sub-skills/classic-detectors/SKILL.md](sub-skills/classic-detectors/SKILL.md) |
| Let PyOD choose detectors, run ADEngine profile/plan/run/analyze/report, drive an agentic anomaly investigation, use `pyod info`, install `od-expert`, or expose PyOD MCP tools | [sub-skills/automated-lifecycle/SKILL.md](sub-skills/automated-lifecycle/SKILL.md) |
| Work with time series, graph anomaly detection, text/image/audio embeddings, multimodal inputs, torch-backed neural detectors, PyG, or backend/credential decisions | [sub-skills/specialized-modalities/SKILL.md](sub-skills/specialized-modalities/SKILL.md) |
| Save/load models, recover legacy joblib artifacts, validate trusted loaded models, use thresholding or score-combination helpers, or operate SUOD/XGBOD/pythresh/combination extras | [sub-skills/model-operations/SKILL.md](sub-skills/model-operations/SKILL.md) |
| Edit PyOD source, package metadata, tests, docs, CLI, MCP import safety, packaged `od-expert` skill, or KB-derived skill sections | [sub-skills/repo-maintenance/SKILL.md](sub-skills/repo-maintenance/SKILL.md) |

## Cross-cutting references

- [references/troubleshooting.md](references/troubleshooting.md) — start here for
  install/import, optional extras, data validation, GPU-claim, persistence, or
  routing failures.
- [references/repo-provenance.md](references/repo-provenance.md) — read before
  deciding whether this skill is current for a PyOD checkout.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  — structured metadata used by DisCo's managed repo-skills router.

## Operating guardrails

- PyOD's unsupervised detector labels are thresholded anomaly decisions, not
  proof of ground truth. Report contamination assumptions and validate with
  labels or domain review when available.
- Higher PyOD anomaly scores normally mean more abnormal. Compare ranks or
  percentiles across detectors rather than raw magnitudes.
- Do not install `pyod[all]` by default. Install the smallest optional extra set
  required by the selected workflow.
- Do not claim CUDA/GPU/accelerator support unless the current runtime has been
  explicitly probed. Core PyOD and many smoke checks are CPU-friendly.
- Treat pickle/joblib model artifacts as executable code; load only trusted
  artifacts and use the `model-operations` trust guidance.
- For source-repo maintenance, use focused tests by edited area and avoid
  publishing, credential, or release commands without explicit maintainer
  approval.
