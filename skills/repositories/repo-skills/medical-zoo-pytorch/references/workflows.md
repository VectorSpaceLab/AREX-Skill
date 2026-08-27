# Workflows

Use this page as the top-level route map for MedicalZooPytorch. It is the quick
index; the detailed API, data-layout, troubleshooting, and smoke scripts live in
the owning sub-skills.

## Main routes

| User request | Read next | Owns |
| --- | --- | --- |
| 3D segmentation model choice, training, checkpoints, TensorBoard, inference, or visualization | [sub-skills/segmentation-workflows/SKILL.md](../sub-skills/segmentation-workflows/SKILL.md) | `lib.medzoo`, `lib.train`, `lib.visual3D_temp` |
| Dataset folder layout, manifests, preprocessing, subvolume generation, normalization, resampling, or augmentation | [sub-skills/data-loading-preprocessing/SKILL.md](../sub-skills/data-loading-preprocessing/SKILL.md) | `lib.medloaders`, `lib.augment3D`, medical-image helpers |
| Loss selection, Dice/CE/weighted/contrastive/angular losses, or shape contracts | [sub-skills/losses-and-metrics/SKILL.md](../sub-skills/losses-and-metrics/SKILL.md) | `lib.losses3D` |
| COVID chest X-ray or CT classification, manifests, COVIDNet, CNN, or COVID metric tracking | [sub-skills/covid-2d-classification/SKILL.md](../sub-skills/covid-2d-classification/SKILL.md) | `lib.medloaders`, `lib.medzoo`, `lib.train.train_covid`, `lib.utils.covid_utils` |

## How the pieces fit together

1. Start with the data route if you need dataset folders, manifests, or image
   preprocessing.
2. Move to the segmentation or COVID route to choose the model and training
   loop.
3. Choose the loss route when you need to match target shapes to criterion
   return values.
4. Use the segmentation route again for checkpointing, TensorBoard logging, and
   inference/visualization.

The common high-level API names are:

- `lib.medzoo.create_model(args)` for the model zoo
- `lib.medloaders.generate_datasets(args, path=...)` for dispatcher-based data loading
- `lib.losses3D.create_loss(name, ...)` and direct loss constructors for criteria
- `lib.train.Trainer` and `lib.train.train_covid.*` for training loops
- `lib.visual3D_temp.TensorboardWriter` and `lib.visual3D_temp.viz` for writer and inference helpers

## Safe startup sequence

1. Run [scripts/smoke_repo_imports.py](../scripts/smoke_repo_imports.py) to
   confirm the import surface and optional CUDA availability.
2. Open the owning sub-skill for the task you actually need.
3. Run that sub-skill's bundled smoke script before touching real data.
4. Use the native repo tests only when the required real datasets or checkpoints
   are available.

## When a task spans routes

- Data layout + segmentation: read the data-preprocessing route first, then the
  segmentation route.
- Data layout + losses: read the data route first, then the loss route.
- COVID manifests + training: read the COVID route first, then the data-layout
  notes in that same route if needed.
- Inference or checkpoint recovery: read the segmentation route plus the data
  route if the input volume or manifest format needs clarification.

## Bundled smoke scripts

- `scripts/smoke_repo_imports.py` checks the cross-cutting import surface and
  optional CUDA availability.
- `sub-skills/segmentation-workflows/scripts/smoke_model_factory.py` checks the
  model factory and tiny forward outputs.
- `sub-skills/segmentation-workflows/scripts/smoke_writer.py` checks the
  TensorBoard writer in a sandbox directory.
- `sub-skills/data-loading-preprocessing/scripts/smoke_preprocessing.py` checks
  NIfTI preprocessing helpers on tiny synthetic fixtures.
- `sub-skills/data-loading-preprocessing/scripts/smoke_dataloaders.py` checks
  synthetic dispatcher and manifest-backed loader behavior.
- `sub-skills/data-loading-preprocessing/scripts/smoke_augmentations.py` checks
  paired 3D augmentation operators.
- `sub-skills/losses-and-metrics/scripts/smoke_losses.py` checks loss contracts
  and unsupported-loss handling.
- `sub-skills/covid-2d-classification/scripts/smoke_covid_imports.py` checks the
  COVID branch on synthetic fixtures.
