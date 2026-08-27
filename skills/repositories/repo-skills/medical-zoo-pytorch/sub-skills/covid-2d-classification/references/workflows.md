# COVID 2D classification workflows

This sub-skill covers the **2D** COVID branch only:

- chest X-ray classification from `COVIDxDataset`
- chest CT classification from `CovidCTDataset`
- `COVIDNet` / `CNN` model selection
- `train_covid` training and validation loops
- `MetricTracker`, `accuracy`, and confusion-matrix reporting

Do not route 3D segmentation tasks here.

## Route selection

- **COVIDx**: 3-class chest X-ray classification.
  - Use `COVIDxDataset` and `dataset_name='COVIDx'`.
  - Labels are `pneumonia`, `normal`, `COVID-19`.
- **COVID_CT**: binary chest CT classification.
  - Use `CovidCTDataset` and `dataset_name='COVID_CT'`.
  - Labels are `CT_COVID` and `CT_NonCOVID`.

## End-to-end flow

1. Make sure the package imports cleanly:
   - `lib.medloaders`
   - `lib.medzoo`
   - `lib.train.train_covid`
   - `lib.utils.covid_utils`
2. Prepare manifests and image folders using [`references/data-layout.md`](./data-layout.md).
3. Build the training arguments.
   - `dataset_name` must match the branch.
   - `classes` must match the label count.
   - `inChannels` should be `3` for RGB inputs.
   - `cuda` controls device placement in `train_covid`.
4. Call `lib.medloaders.generate_datasets(args, path=...)`.
5. Call `lib.medzoo.create_model(args)`.
6. Run `train(args, model, train_loader, optimizer, epoch, writer)`.
7. Run `validation(args, model, val_loader, epoch, writer)`.
8. Read the returned confusion matrix and the terminal summaries.

## Training contract

- `train_covid.train` and `train_covid.validation` both use `CrossEntropyLoss`.
- Targets must already be integer class indices, not one-hot vectors.
- `accuracy(output, target)` returns `(correct, total, acc)`.
- `validation` builds a `classes x classes` confusion matrix.

## Model choices

- `COVIDNET1` maps to `CovidNet('small', classes)`.
- `COVIDNET2` maps to `CovidNet('large', classes)`.
- `CNN` maps to a torchvision backbone wrapper.

## Current source-state caveats

These are source-level issues to know before you attempt a real run:

- `COVIDxDataset.__getitem__` passes an `augmentation=` keyword that its `load_image` method does not accept.
- `CovidNet` constructor references `pepx` instead of `PEPX`.
- `CNN` uses torchvision backbones with `pretrained=True`.
- `CovidNet`'s classifier head is hard-coded for 224x224-style inputs.
- `CovidCTDataset` ignores its `transform` argument and uses built-in train/val transforms.
- `MetricTracker` reports iteration averages, not sample-weighted averages.

See [`references/troubleshooting.md`](./troubleshooting.md) for symptoms and safe responses.

## Safe smoke path

Use [`scripts/smoke_covid_imports.py`](../scripts/smoke_covid_imports.py) for a synthetic check of imports, manifest parsing, `MetricTracker`, `accuracy`, and the train/validation loop.
