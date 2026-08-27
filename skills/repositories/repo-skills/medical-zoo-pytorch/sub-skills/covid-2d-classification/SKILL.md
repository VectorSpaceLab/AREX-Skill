---
name: covid-2d-classification
description: "Route the 2D COVID chest X-ray and CT classification branch."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# covid-2d-classification

Use this sub-skill for the 2D COVID classification branch only:

- COVIDx chest X-ray classification
- CovidCT chest CT classification
- `COVIDNet` / `CNN` model selection
- `train_covid` training and validation loops
- `MetricTracker`, `accuracy`, and manifest parsing

Do not use this sub-skill for 3D segmentation or 3D COVID segmentation.
Route those tasks to the segmentation-oriented or data-preparation sub-skill instead.

## Start here

1. Read [`references/workflows.md`](./references/workflows.md) for the end-to-end route.
2. Read [`references/data-layout.md`](./references/data-layout.md) before touching manifests.
3. Read [`references/api-reference.md`](./references/api-reference.md) for public class and function contracts.
4. Read [`references/troubleshooting.md`](./references/troubleshooting.md) if imports or sample runs fail.
5. Run [`scripts/smoke_covid_imports.py`](./scripts/smoke_covid_imports.py) for a safe synthetic import check.

## What this branch expects

- 2D RGB inputs only.
- `COVIDx` for 3-class chest X-ray work.
- `COVID_CT` for 2-class chest CT work.
- A local MedicalZooPytorch installation, or an equivalent environment where `lib.*` imports resolve.
- No dependence on the original repository checkout at runtime.

## Important caveats

- `COVIDxDataset` currently has a `__getitem__` / `load_image` keyword mismatch in source.
- `CovidNet` currently uses `pepx` instead of `PEPX` in the constructor.
- `CNN` uses torchvision backbones with `pretrained=True`; do not let smoke checks fetch weights.
- `MetricTracker` averages batch metrics by iteration count, not sample count.

## Public entry points

- Dataset loaders: `lib.medloaders.COVIDxdataset.COVIDxDataset`, `lib.medloaders.covid_ct_dataset.CovidCTDataset`
- Model factory: `lib.medzoo.create_model`
- Training loop: `lib.train.train_covid.train`, `lib.train.train_covid.validation`
- Metrics: `lib.utils.covid_utils.accuracy`, `lib.utils.covid_utils.MetricTracker`
- Helper parser: `lib.utils.covid_utils.read_txt`
