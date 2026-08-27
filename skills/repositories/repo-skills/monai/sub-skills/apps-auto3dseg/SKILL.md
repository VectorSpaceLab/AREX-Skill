---
name: apps-auto3dseg
description: "Use high-level MONAI application workflows, especially Auto3DSeg
  orchestration, DataAnalyzer statistics, BundleGen, EnsembleRunner, HPO
  generators, nnU-Net bridging, and built-in app dataset helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MONAI Apps and Auto3DSeg

Use this sub-skill when a task asks for high-level MONAI application helpers instead of hand-written model, transform, training-loop, or bundle mechanics.

## Route Here For

- Planning an Auto3DSeg run with `monai.apps.auto3dseg.AutoRunner`, including safe configuration review before analysis, algorithm generation, training, HPO, or ensemble inference.
- Running or troubleshooting `DataAnalyzer`, `BundleGen`, `EnsembleRunner`, `NNIGen`, `OptunaGen`, `nnUNetV2Runner`, or the `python -m monai.apps.auto3dseg` / `python -m monai.apps.nnunet` CLIs.
- Choosing built-in app dataset helpers such as `MedNISTDataset`, `DecathlonDataset`, `TciaDataset`, and `CrossValidation` while documenting download/cache behavior.
- Handing Auto3DSeg-generated bundles to the Bundle route, or deciding whether a request belongs to raw data/transforms, primitive modeling/inference, or custom training loops.

## Do Not Use For

- General MONAI Bundle config syntax or `python -m monai.bundle` execution; use `../bundle-config/SKILL.md` for generated bundle internals and CLI overrides.
- Raw datalist loading, transforms, metadata, image readers, and caching primitives; use `../data-transforms/SKILL.md`.
- Network/loss/metric/inferer selection and prediction primitives; use `../modeling-inference/SKILL.md`.
- Custom Ignite or PyTorch training/evaluation loops; use `../training-evaluation/SKILL.md`.

## References and Scripts

- Read `references/workflows.md` when designing an Auto3DSeg, DataAnalyzer, BundleGen, ensemble, HPO, nnU-Net, or app-dataset workflow and deciding what is safe to inspect versus expensive to execute.
- Read `references/api-reference.md` when you need concise constructor signatures, required input schemas, output artifacts, and CLI routing notes.
- Read `references/troubleshooting.md` when diagnosing YAML/datalist errors, image-label layout mismatches, optional dependency failures, multi-GPU assumptions, generated bundle handoff, or dataset downloads.
- Run `scripts/auto3dseg_smoke.py` when you need a no-training, no-download import/CLI/config inspection check for the installed MONAI Auto3DSeg surfaces.

## Safe Operating Rules

1. Treat `AutoRunner.run()`, `DataAnalyzer.get_all_case_stats()`, `BundleGen.generate()`, `EnsembleRunner.run()`, HPO trials, nnU-Net conversion/training, and dataset `download=True` as potentially expensive or side-effecting.
2. Prefer config review, import/signature inspection, CLI help, and tiny synthetic file plans before launching analysis, downloads, GPU jobs, multi-fold training, or HPO.
3. Confirm that optional packages are installed before claiming support for NNI, Optuna, nnU-Net, TensorBoard tracking, image readers beyond core formats, or TCIA/medical image downloads.
4. When Auto3DSeg produces bundle folders, route edits to `../bundle-config/SKILL.md`; when it needs datalist or image layout fixes, route to `../data-transforms/SKILL.md`.
