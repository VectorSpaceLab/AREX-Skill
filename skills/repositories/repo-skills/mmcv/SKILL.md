---
name: mmcv
description: "Use MMCV 2.2.0 for computer-vision media utilities, transform
  pipelines, CNN builders, and compiled ops installation or troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMCV Repo Skill

Use this repo skill when a task names MMCV, OpenMMLab computer-vision utilities, `mmcv`, `mmcv-lite`, `mmcv.transforms`, `mmcv.cnn`, `mmcv.ops`, image/video/flow helpers, transform pipelines, CNN layer builders, or MMCV install/build failures.

## Start Here

1. Identify whether the task is a pure Python utility workflow, a PyTorch model-building workflow, or a compiled ops/build workflow.
2. If the task involves package selection, `_ext`, CUDA, native kernels, or `mmcv.ops`, route to `sub-skills/ops-and-builds/` before writing code.
3. If the task is media preprocessing or visualization, route to `sub-skills/media-processing/`.
4. If the task is a dict-style data pipeline or registry transform, route to `sub-skills/data-transforms/`.
5. If the task is a PyTorch CNN layer/module builder, route to `sub-skills/cnn-model-building/`.
6. Check `references/repo-provenance.md` before deciding whether this skill is current for a repository checkout.

## Install And Import Baseline

MMCV 2.x has two package variants:

- `mmcv-lite` imports as `mmcv` and covers Python/Numpy/MMEngine/PyTorch utility surfaces that do not need compiled `mmcv._ext` ops.
- `mmcv` is the full package variant for compiled ops. Use it when code imports `mmcv.ops` or needs native CPU/CUDA/backend kernels.
- Do not install both variants in the same environment. If switching, uninstall the other variant first.

Minimal import check for lite-safe workflows:

```bash
python - <<'PY'
import mmcv
print(mmcv.__version__)
PY
```

For full ops workflows, use `sub-skills/ops-and-builds/scripts/check_mmcv_install.py` with `--require-ops`.

## Sub-Skill Routes

| Route | Use When | Start With |
| --- | --- | --- |
| `sub-skills/media-processing/` | Image IO, color conversions, resize/crop/pad/rotate/flip, normalization, video reader/editing helpers, optical flow, visualization, array quantization. | `sub-skills/media-processing/SKILL.md` |
| `sub-skills/data-transforms/` | `mmcv.transforms`, `Compose`, `LoadImageFromFile`, `Resize`, `Pad`, `Normalize`, custom `BaseTransform`, transform wrappers, dict-key/shape failures. | `sub-skills/data-transforms/SKILL.md` |
| `sub-skills/cnn-model-building/` | `mmcv.cnn` builders, `ConvModule`, depthwise separable modules, wrappers, plugin layers, fusion, model complexity, CPU-safe PyTorch blocks. | `sub-skills/cnn-model-building/SKILL.md` |
| `sub-skills/ops-and-builds/` | `mmcv` vs `mmcv-lite`, MIM/pip/source builds, CUDA/PyTorch compatibility, `mmcv.ops`, `_ext` import failures, native extension diagnostics. | `sub-skills/ops-and-builds/SKILL.md` |

## Shared References And Scripts

- `references/troubleshooting.md` covers cross-cutting package, import, routing, optional dependency, and version issues.
- `references/repo-provenance.md` records the source snapshot used to generate this skill and when to refresh it.
- `references/repo-routing-metadata.json` is structured metadata used by the managed `repo-skills-router` import process.
- `scripts/check_mmcv_environment.py` runs every bundled helper that is safe for the currently installed package variant and summarizes the result.

## Routing Pitfalls

- `import mmcv` succeeding does not prove `mmcv.ops` is available.
- Most media and transform workflows are lite-safe, but video editing may need external codec support and tensor formatting may need PyTorch.
- `mmcv.cnn` is PyTorch-dependent, but many builders do not require compiled MMCV ops.
- Size arguments often use width-height order, while NumPy metadata usually reports height-width shape.
- Headless agents should prefer file outputs or returned arrays instead of GUI display helpers.
