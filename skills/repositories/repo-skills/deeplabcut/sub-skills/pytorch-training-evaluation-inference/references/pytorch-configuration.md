# PyTorch configuration guide

A PyTorch DeepLabCut project is driven by `pytorch_config`. Treat it as the source of truth for model shape, training defaults, inference behavior, and top-down detector settings.

## Top-level fields to know

| Field | Purpose | Safe guidance |
| --- | --- | --- |
| `method` | Chooses `bu`, `td`, or `ctd`. | Keep it aligned with the model family you selected. |
| `net_type` | Selects the architecture variant. | Use the canonical model name for the chosen project type. |
| `device` | Chooses `auto`, `cpu`, `cuda`, or `mps`. | Use this for PyTorch device choice instead of TensorFlow-era GPU flags. |
| `metadata` | Stores bodyparts, individuals, paths, and project identity. | Do not hand-edit unless you know the project metadata is still valid. |
| `resume_training_from` | Optional resume checkpoint. | Use only when intentionally continuing from a saved checkpoint. |

## `model`

The `model` section defines the architecture layout.

- `backbone`: the encoder family and variant
- `heads`: the prediction heads used by the model
- `backbone_output_channels`: channel count handed from backbone to head
- `neck`: optional intermediate block
- `pose_model`: optional high-level pose model wrapper

Practical guidance:

- Use `available_models()` to confirm a valid `net_type` before editing the file.
- Bottom-up single-animal projects usually use a backbone plus a heatmap head.
- Multi-animal bottom-up projects need bodypart heads plus PAF-related structure.
- Top-down projects add a detector section and a pose head suitable for cropped individuals.
- Conditional top-down models also need a valid inference-condition setup.

## `data`

The `data` section controls image preprocessing and augmentation.

Important subkeys:

- `train`: training-time transforms and crop sampling
- `inference`: inference-time transforms
- `bbox_margin`: extra margin around training boxes
- `colormode`: keep consistent with the data pipeline, usually `RGB`
- `collate`: batch assembly behavior for variable-sized images

Practical guidance:

- Keep `normalize_images` enabled for training and inference.
- Use crop sampling or collate choices that match your image size variation.
- For top-down workflows, `top_down_crop` and related crop controls matter during inference.

## `runner`, `device`, and `gpus`

The `runner` section controls optimization and checkpoint cadence.

Important subkeys:

- `type`: the training runner
- `gpus`: optional GPU list
- `key_metric`: which metric chooses the best snapshot
- `key_metric_asc`: whether higher is better
- `eval_interval`: how often validation runs during training
- `optimizer`: optimizer settings
- `scheduler`: learning-rate schedule
- `snapshots.save_epochs`: checkpoint cadence
- `snapshots.max_snapshots`: how many snapshots to keep

Practical guidance:

- `device` is the main switch for PyTorch execution.
- `runner.gpus` is only relevant when you want explicit multi-GPU routing.
- Keep `runner.device` and the top-level `device` choice consistent.
- Use `snapshots.save_epochs` when you want a different save cadence without hand-editing the whole config.

## `train_settings`

This section controls the training loop itself.

Important subkeys:

- `batch_size`
- `dataloader_workers`
- `dataloader_pin_memory`
- `display_iters`
- `epochs`
- `seed`
- `weight_init`

Practical guidance:

- Increase `batch_size` only when memory allows it.
- `epochs` is the PyTorch training length; it is not TensorFlow-style iterations.
- `weight_init` is where SuperAnimal and other transfer-learning initialization data live.
- `pose_threshold` is a training-side memory-replay gate, not an analysis cutoff.

## `logger`

The `logger` section is optional.

- Use it when you want CSV logging or Weights & Biases logging.
- Keep run names readable so snapshot folders are easy to identify later.
- Do not rely on the logger to carry core config choices; those still belong in the main config.

## `inference`

The `inference` section controls analysis-time behavior.

Important subkeys:

- `multithreading`
- `compile`
- `autocast`
- `conditions`
- `snapshot`
- `eval`
- `output_dir`

Practical guidance:

- `conditions` is only meaningful for conditional top-down models.
- `snapshot` selects the pose snapshot used for analysis.
- `eval` controls evaluation-specific behavior.
- `output_dir` can centralize inference outputs when you do not want them next to the source files.

### Condition forms

`inference.conditions` can be one of these:

- a shuffle reference
- a shuffle plus a snapshot name or index
- a file path for precomputed conditions, when evaluation is the goal

For live image/video inference, use a model-based or shuffle-based condition provider. File-path conditions are for evaluation-only paths.

## `detector`

The `detector` section exists for top-down models.

Typical pieces:

- `model`
- `data`
- `runner`
- `train_settings`
- `inference`
- `resume_training_from`

Practical guidance:

- Use `available_detectors()` to confirm a valid detector name before editing the section.
- Top-down projects need a detector config and detector snapshots.
- Detector batch size, epochs, and save cadence can be adjusted independently from the pose branch.
- If the detector section is absent, that is usually expected for bottom-up projects but not for top-down projects.

## Safe override pattern

When you need a temporary change for one run, prefer a dotpath override instead of editing the whole file:

- `train_settings.batch_size`
- `train_settings.epochs`
- `runner.device`
- `runner.snapshots.save_epochs`
- `detector.train_settings.epochs`
- `detector.runner.snapshots.save_epochs`
- `inference.snapshot`
- `inference.conditions`

## Validation checklist

- `model` exists and matches the project type
- `data` has the expected train and inference sections
- `runner` has the snapshot and optimizer choices you expect
- `train_settings` has the correct batch size and epoch budget
- `inference` has a valid snapshot and condition choice
- `detector` is present when the project uses a top-down path
