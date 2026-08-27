# Training and Validation Troubleshooting

Use this matrix after building a dry-run command or when explaining a failed
training/validation attempt. Route full config-schema questions to
`data-and-configs` and model/loss/scheduler registry questions to
`model-zoo-and-apis`.

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| Training fails when the loader starts, or validation reports missing images/splits | `data.path`, dataset-specific paths, `train_split`, or `val_split` do not exist on the run machine | Do not retry blindly. Validate the config and dataset layout with `data-and-configs`, rewrite machine-specific paths, then rebuild the command. |
| Dry-run builder warns that the config contains an absolute or machine-specific path | Example configs and legacy experiment configs often embed paths from another machine | Treat the config as a template only. Create a local copy with portable dataset roots before running. |
| Validation immediately fails because the checkpoint file is missing | `--model_path` points at a file that is not present, or resume/checkpoint paths were resolved from a different working directory | Use `scripts/build_validate_command.py --config ... --model_path ...` to catch this before a run. Remember that script paths are resolved from the command working directory unless absolute. |
| Training resume says no checkpoint was found and starts from scratch | `training.resume` is absent, null, or points at a non-existing file | This is source behavior, not a hard parser error. Stop if the user expected resume; otherwise document that the run starts fresh. |
| `yaml.load()` raises a Loader-related error on modern PyYAML | The training and validation entrypoints use legacy `yaml.load(fp)` with no Loader | Prefer adapting the entrypoints to `yaml.safe_load(fp)` in a local patch, or use a compatible PyYAML version in a legacy reproduction environment. The bundled command builders already use safe loading for static warnings. |
| Importing the model package fails before CLI help with a generated protobuf descriptor error | Some model imports depend on generated `caffe_pb2` code that is incompatible with newer protobuf runtimes | Use a compatible protobuf version or the pure-Python protobuf implementation workaround in the execution environment. Confirm imports before running expensive workflows. |
| `tensorboardX` is missing | Training imports `SummaryWriter` at module import time | Install the runtime dependency before using `train.py`. Validation does not need TensorBoardX, but importing training help does. |
| CPU run is unexpectedly slow | Full segmentation training/validation is dataset-bound and model-heavy; CPU is only a partial substitute for real experiments | Use CPU only for parser/config/API smoke checks or tiny debugging. Obtain user approval before long CPU runs; use CUDA when a real run requires it. |
| CUDA is available but results or speed are not reproducible | The workflow selects CUDA automatically, wraps training in `DataParallel`, and does not set deterministic cuDNN flags or DataLoader worker seeds | For reproducibility-focused work, add deterministic backend settings and worker seeding in a local experiment patch; record the patch. |
| `DataParallel` checkpoint fails to load in validation due to key prefixes | Training saves `model.state_dict()` from a `DataParallel` model, producing `module.` prefixes | Validation uses `convert_state_dict` to strip a uniform `module.` prefix. If loading still fails, check for architecture/class-count mismatches or mixed prefix styles. |
| Raw checkpoint state dict fails with `model_state` missing | Validation expects a dictionary containing `model_state`, not a bare state dict | Wrap trusted raw states into the expected checkpoint dictionary or write a small local adapter. Preserve the original file. |
| `size mismatch` or missing/unexpected keys on checkpoint load | Config model architecture, constructor options, or dataset class count differs from the training run | Check the config used to train the checkpoint. Route model option details to `model-zoo-and-apis` and dataset class-count details to `data-and-configs`. |
| Metrics contain NaN | A class is absent, the validation subset is too small, all labels are ignored/invalid, or the split is wrong | Inspect aggregate metrics plus per-class IoU. Confirm valid labels are in `[0, n_classes)`; loss uses `ignore_index=250` and metrics masks labels outside the class range. |
| Mean IoU is much lower than expected | Wrong checkpoint/config pairing, missing preprocessing, different split, disabled/enabled flip mismatch, or class-count mismatch | Rebuild the validation command with explicit flip and timing flags. Verify config, dataset split, image size, and checkpoint provenance before rerunning. |
| FPS output is noisy or misleading | `--measure_time` reports simple per-batch wall-time fps, can include flip averaging and data movement, and does not use a benchmark protocol | Use `--no-measure_time` for metric-only validation. For benchmarking, create a separate controlled timing script with warm-up and synchronization. |
| TensorBoard log directory surprises the user | Training creates `runs/<config-stem>/<random-run-id>/`, copies the config there, and writes logs/checkpoints | Confirm write permissions and disk budget before running. Best checkpoints are saved inside that generated run directory. |
| Resume after changing optimizer/scheduler settings fails | Resume loads optimizer and scheduler state dictionaries from the checkpoint | Keep optimizer/scheduler settings compatible with the checkpoint, or start a fresh run intentionally and document that resume state was not reused. |
| Validation uses more worker processes than expected | Validation hard-codes DataLoader `num_workers=8` and ignores `training.n_workers` | Patch the validation script locally or run on a machine where eight workers is acceptable. Record any local patch. |
| Need to segment one custom image | That is the `test.py` workflow, not dataset validation | Route to `single-image-inference`; do not force `validate.py` onto a single image. |

## Pre-run recovery sequence

1. Build the command with the bundled dry-run script.
2. Resolve all missing config, dataset, checkpoint, and dependency warnings.
3. Confirm the run's write location and compute budget.
4. For validation, confirm checkpoint format and `module.` prefix handling using [checkpoints-and-metrics.md](checkpoints-and-metrics.md).
5. Run the printed command manually only after the user explicitly approves the full dataset-bound workflow.
