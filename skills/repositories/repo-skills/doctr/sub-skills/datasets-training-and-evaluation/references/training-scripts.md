# Training, evaluation, and latency workflows

Use this reference to plan docTR training/evaluation work without depending on the original repository checkout. The source repository provides heavyweight reference scripts for detection, recognition, layout, table structure, and classification/orientation tasks; this generated skill distills their contracts, data requirements, option families, metrics, and safety checks. It does **not** bundle those heavyweight scripts because real runs can download datasets or pretrained weights, allocate GPU memory, write checkpoints, and run for a long time.

For any real training/evaluation run, either use an installed/project-specific entry point that implements the same contract or write a small project script against docTR's public dataset/model APIs. Do not assume a `references/...` source path exists unless the user is explicitly working inside a docTR source checkout.

## Workflow selection matrix

| Task | Training contract | Evaluation contract | Latency/benchmark contract | Main local data requirement | Main metrics |
| --- | --- | --- | --- | --- | --- |
| Text detection | Detection model name, local or built-in train/val datasets, rotation flags, output checkpoint directory | Detection model/checkpoint, dataset split, rotation/eval-straight flags, batch size | Random image tensors at detector input size | `DATASET_ROOT/images` + `DATASET_ROOT/labels.json` detection schema | Validation loss, recall, precision, mean IoU |
| Text recognition | Recognition model name, local/built-in/synthetic data, vocab, fonts, checkpoint directory | Recognition model/checkpoint, dataset split, vocab, batch size | Random word-crop tensors at recognizer input size | `DATASET_ROOT/images` + `DATASET_ROOT/labels.json` recognition schema; or synthetic `WordGenerator` fallback | Validation loss, exact/raw text match and tolerant text match summaries |
| Layout detection | Layout model name, local train/val roots, class labels, rotation flags | Layout model/checkpoint, dataset root, class mapping, rotation flags | Random page tensors at layout input size | `DATASET_ROOT/images` + `DATASET_ROOT/labels.json` layout schema | Validation loss, mAP@[.5:.95], AP@.5, AP@.75 |
| Table structure | Table model name, local train/val roots, cell/logic labels, IoU threshold | Table model/checkpoint, dataset root, IoU threshold | Random table-crop tensors at table model input size | `DATASET_ROOT/images` + `DATASET_ROOT/labels.json` table schema | Validation loss, cell recall, precision, F1, structure accuracy |
| Character classification | Classification architecture, vocab, synthetic generator settings | Same task-specific classifier metric loop | Random character tensors | Synthetic `CharacterGenerator` from `VOCABS` | Validation loss, accuracy |
| Page/crop orientation classification | Orientation type (`page` or `crop`), train/val image roots, transform policy | Same task-specific classifier metric loop | Random image tensors | Image folder under each split root | Validation loss, accuracy |

## Universal training workflow

1. Identify task, architecture, dataset source, and acceptance metric.
2. Validate local labels with the bundled validator from this sub-skill:

   ```bash
   python scripts/validate_doctr_labels.py --task detection --dataset-root TRAIN_ROOT
   python scripts/validate_doctr_labels.py --task recognition --dataset-root TRAIN_ROOT --warn-spaces
   python scripts/validate_doctr_labels.py --task layout --dataset-root TRAIN_ROOT --strict-doc-fields
   python scripts/validate_doctr_labels.py --task table --dataset-root TRAIN_ROOT
   ```

3. Instantiate one dataset sample and one DataLoader batch using the public APIs shown in [evaluation-and-training.md](evaluation-and-training.md).
4. If an external training script/entry point is available in the user's project, run its parser/help check first. If no entry point is available, write a small script against `doctr.datasets`, `doctr.transforms`, and the relevant `doctr.models` factory.
5. For a real run, start with a tiny bounded trial such as one epoch, low batch size, and a dedicated output directory.
6. Record architecture, vocab/class names, geometry flags, input size, batch size, learning rate, checkpoint path, metric summary, and unresolved warnings for the model-loading handoff.

## Detection training contract

Required choices:

- Architecture such as `db_resnet50`, `db_mobilenet_v3_large`, `linknet_resnet34`, `fast_tiny`, `fast_small`, or `fast_base`.
- Local train/validation roots **or** built-in dataset names, not both for the same split.
- Straight geometry (`use_polygons=False`) or rotated polygon geometry (`use_polygons=True`).
- Batch size, epoch count, device, optional DDP backend, and output checkpoint directory.

Rules:

- Built-in single-class detection datasets documented by docTR include `CORD`, `FUNSD`, `IC03`, `IIIT5K`, `SVHN`, `SVT`, and `SynthText`; they are not suitable for multi-class/KIE-style detector training.
- Use rotated geometry consistently across dataset loader, model postprocessor assumptions, and metric update calls.
- The main outputs are checkpoint files and validation logs containing recall, precision, and mean IoU.

## Recognition training contract

Required choices:

- Recognition architecture such as `crnn_vgg16_bn`, `crnn_mobilenet_v3_small`, `sar_resnet31`, `master`, `vitstr_small`, `parseq`, or `viptr_tiny`.
- Local train/validation roots, built-in dataset names, or synthetic `WordGenerator` fallback.
- Vocab string or `VOCABS[...]` key that covers every target character.
- Optional font configuration for synthetic samples.

Rules:

- Validate all labels against the same vocab used to build/evaluate the model.
- If neither local nor built-in data is supplied, a reference implementation may use synthetic word images; make that fallback explicit because synthetic data can hide real-document distribution issues.
- Interpret tolerant metrics (`caseless`, `anyascii`, `unicase`) separately from exact/raw text accuracy.

## Layout training contract

Required choices:

- Layout architecture such as `lw_detr_s` or `lw_detr_m`.
- Local train/validation roots with image files and one `classes` entry per polygon.
- Class-name spelling and ordering policy.
- Straight or rotated geometry policy.

Rules:

- Local train and validation roots are required for layout training workflows.
- Derive class names from labels only after checking that every split uses consistent spelling.
- COCO-style object metrics (`mAP@[.5:.95]`, `AP@[.5]`, `AP@[.75]`) require prediction confidence scores and consistent class indices.

## Table structure training contract

Required choices:

- Table architecture, currently `tablecenternet`.
- Local train/validation roots where each annotation maps `cells` polygons to `logic` coordinates one-to-one.
- IoU threshold for matching predicted cells to ground truth.
- Straight or rotated geometry policy.

Rules:

- Structure accuracy is calculated only on matched cells; a model can have good cell F1 but poor row/column spans.
- Keep `cells` and `logic` lengths equal for every sample.
- Confirm that `logic` coordinates use `[col_start, col_end, row_start, row_end]` ordering.

## Classification and orientation contracts

Character classification:

- Uses synthetic `CharacterGenerator` data rather than local JSON labels.
- `VOCABS` controls classes and target indices.
- Main metrics are validation loss and accuracy.

Page/crop orientation classification:

- Requires a task type (`page` or `crop`) and train/validation image roots.
- The dataset initializes local images with zero-degree targets; transforms and task type define the orientation workflow.
- Confirm whether the trained classifier will replace page orientation, crop orientation, or both inside an OCR predictor.

## Evaluation contract

Evaluation-only requests need:

1. Dataset schema validation and sample loading.
2. Model architecture and checkpoint task family.
3. Matching vocab/classes and rotation flags.
4. Low batch size for the first trial.
5. Metric summary, checkpoint identifier, data split, and skipped/empty metric notes.

Do not evaluate a recognition checkpoint with a different vocab from the one used for training unless the task explicitly handles projection or whitelist changes. Do not evaluate detection/layout/table rotated models with straight-box metrics without recording the conversion.

## Latency/benchmark contract

Latency checks allocate random tensors and benchmark forward passes. Before running any benchmark, record:

- architecture and input size,
- batch size and warmup/iteration counts,
- CPU/GPU/backend and precision,
- PyTorch build and device model,
- whether preprocessing/postprocessing are included.

Add GPU benchmarking only when CUDA/MPS is available and the user intentionally wants a device benchmark. Do not present one host's latency as universal performance.

## DDP and GPU caveats

- Use `torchrun`-style multi-process launchers for multi-GPU training in user projects.
- Set `CUDA_VISIBLE_DEVICES` before the launcher to control participating GPUs.
- Process count should usually match the number of visible GPUs.
- `nccl` is the common CUDA backend; choose alternatives only for unsupported environments.
- Effective batch size is per-process batch size multiplied by process count.
- Avoid mixing DDP and CPU-only environments unless the exact script/backend combination has been tested.

## Output handoff

For a completed training/evaluation run, hand off:

- task family and architecture,
- dataset split sources and validation summary,
- vocab name or class names,
- rotation/polygon settings,
- input size, batch size, optimizer/LR, epoch count, AMP/DDP status,
- checkpoint path and best/last checkpoint rule,
- final validation metrics and any `None` metrics,
- whether the checkpoint is intended for detection, recognition, layout, table structure, character classification, page orientation, or crop orientation.

Route follow-up model loading or OCR/KIE predictor integration to [models-and-customization](../../models-and-customization/SKILL.md) or [core-ocr-and-kie](../../core-ocr-and-kie/SKILL.md).
