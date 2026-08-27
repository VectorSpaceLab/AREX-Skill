---
name: "basic-ts"
description: "Routes BasicTS time-series training, dataset, model, and pipeline
  workflows through focused sub-skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BasicTS

BasicTS is a time-series analysis toolkit and benchmark library. Use this root skill as the router for the package's main user-facing workflows.

## Install and inspect

A simple public install path is:

```bash
pip install basicts
```

For local development against a checkout, editable install is also fine:

```bash
pip install -e .
```

Minimal import check:

```bash
python -I -c "import basicts; print(basicts.__version__)"
```

For a friendlier inspection summary, run `scripts/check_basic_ts_install.py`.

## Route map

| User request | Read first |
| --- | --- |
| Train, evaluate, resume, or quick-start a BasicTS run | `sub-skills/training-evaluation/SKILL.md` |
| Inspect a built-in model, author a custom model, or check `forward` contracts | `sub-skills/model-development/SKILL.md` |
| Validate a dataset folder, raw conversion, or tiny fixture layout | `sub-skills/data-preparation/SKILL.md` |
| Customize callbacks, metrics, scalers, taskflows, or config behavior | `sub-skills/pipeline-extension/SKILL.md` |

## When to read the bundled references

- Read `references/repo-provenance.md` when you need to check whether this skill still matches the current BasicTS checkout.
- Read `references/troubleshooting.md` when imports, datasets, configs, callbacks, or checkpoints fail in a cross-cutting way.
- Read `references/repo-routing-metadata.json` when you need router placement details for import or selection logic.

## What this root skill does not cover

- It does not replace the repository's source code.
- It does not include the optional web/server surface as a first-class route.
- It does not include release or packaging-maintainer workflows.

## Root guidance

1. Start with the route map above.
2. Pick the narrowest sub-skill that matches the user's request.
3. Use the root troubleshooting reference only for cross-cutting installation, import, dataset-path, or checkpoint issues.
4. Check provenance before treating the skill as current for a different checkout.

## Quick signals

- `BasicTSLauncher` and checkpoint questions → `training-evaluation`
- `forward`, model output keys, or auxiliary loss → `model-development`
- `train_data.npy`, `train_inputs.npy`, `shape.npy`, or raw dataset conversion → `data-preparation`
- callbacks, metrics, scalers, taskflow, or config shortcuts → `pipeline-extension`

## How to use the install check script

Run `scripts/check_basic_ts_install.py` when you want a read-only summary of the installed package, launcher signature, and core import surface.
