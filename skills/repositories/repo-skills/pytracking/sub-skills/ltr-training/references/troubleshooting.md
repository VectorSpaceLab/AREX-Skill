# LTR training troubleshooting

Use this guide to diagnose training setup and static launch issues before starting long runs.

## Local config failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RuntimeError: YOU HAVE NOT SETUP YOUR local.py!!!` | `ltr/admin/local.py` is missing. | Generate the template with `ltr.admin.environment.create_default_local_file()`, then edit every required path. |
| Checkpoints or TensorBoard paths are empty or created in an unexpected place | `workspace_dir` or `tensorboard_dir` is empty or relative in `local.py`. | Set writable absolute paths. Keep `tensorboard_dir` inside or near `workspace_dir` unless the user has a logging policy. |
| `AttributeError: EnvironmentSettings object has no attribute ...` | The selected setting references a local config field not in the generated template. | Add the missing attribute to `EnvironmentSettings.__init__`. TaMOs commonly needs `imagenet_vid_gmot_dir` and `tao_burst_dir`. Some dataset classes can reference DAVIS variant fields. |
| Dataset constructor raises file-not-found or split errors | The root points to the wrong dataset layout, or the split name does not match the local dataset copy. | Verify the setting’s dataset list, root path, split argument, and split text files. Do this before launching epochs. |

## Command and setting selection failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: ltr.train_settings.<module>.<name>` | Wrong `train_module`/`train_name`, missing copied setting, or missing `__init__.py` in a new module directory. | Run `scripts/build_training_command.py --list` from this sub-skill, create the file, and add `__init__.py` for new module directories. |
| `AttributeError: module ... has no attribute run` | Setting file does not define `def run(settings):`. | Add the expected entry function; keep heavy construction inside the function. |
| `--cudnn_benchmark False` still behaves as enabled | The source CLI parses boolean arguments with `type=bool`, so non-empty strings can evaluate truthy. | Use the command builder with `--no-cudnn-benchmark`; it emits a Python API command with `cudnn_benchmark=False`. |
| Training resumes from an unintended checkpoint | `settings.project_path` points at an existing workspace project path, or the copied setting kept another module/name project path. | Confirm `settings.project_path` and checkpoint directory before launch. Rename the setting or change project path only intentionally. |

## Checkpoint and pretrained-weight failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| File not found under `pretrained_networks` | Required pretrained weight was not downloaded or is named differently. | Place the expected file under `pretrained_networks`, or update the setting to the actual filename after confirming compatibility. |
| LWL stage 2 cannot load stage 1 | Stage-1 workspace checkpoint is missing or project path differs. | Train or provide the stage-1 checkpoint under the expected workspace project path, or update the load path intentionally. |
| LWL box-init cannot load stage 2 | Stage-2 workspace checkpoint is missing or project path differs. | Provide the stage-2 checkpoint under the expected workspace project path. |
| KeepTrack cannot initialize base network | `super_dimp_simple.pth.tar` is missing or incompatible. | Supply the expected SuperDiMP simple checkpoint; verify its model state matches the target candidate matching setup. |
| KYS cannot initialize base network | `dimp50.pth` is missing or incompatible. | Supply a compatible DiMP-50 checkpoint before starting KYS training. |
| Network type assertion fails while loading | The checkpoint’s saved `net_type` differs from the current model class. | Do not force-load across unrelated settings. Use matching setting/checkpoint pairs or write a deliberate conversion routine. |

## Optional dependency and extension failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: pycocotools` | COCO wrappers require pycocotools. | Install a compatible `pycocotools` wheel in the active environment. |
| `ModuleNotFoundError: lvis` | LVIS dataset wrapper requires the `lvis` package. | Install `lvis` only if the setting actually uses LVIS. Do not add LVIS to an ATOM/DiMP setting unless you also modify the dataset pipeline. |
| `ModuleNotFoundError` or build error for PreciseRoIPooling / `prroi_pool` | PreciseRoIPooling extension is missing or incompatible with the active PyTorch/CUDA compiler stack. | Build or install a compatible extension for the environment. ATOM/DiMP/PrDiMP-style IoU and target-classifier components can require it. |
| `ModuleNotFoundError: spatial_correlation_sampler` | KYS cost-volume model imports `spatial-correlation-sampler`. | Install a version compatible with the active PyTorch/CUDA stack, or avoid KYS execution until available. |
| `jpeg4py` / libjpeg / turbojpeg errors | Image loader backend missing host library or Python package. | Install the missing loader dependency or switch a dataset constructor to a working image loader after testing. |
| TensorBoard import warning or missing writer | `torch.utils.tensorboard` unavailable and `tensorboardX` fallback missing. | Install TensorBoard support in the active environment before expecting logs. |

## CUDA, memory, and multiprocessing failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Immediate CUDA OOM | Batch size, crop size, feature size, sequence length, or multi-GPU setting exceeds memory. | Reduce `settings.batch_size`, image/output sizes, `num_train_frames`, `num_test_frames`, or choose fewer visible GPUs. |
| TaMOs has invalid zero batch size on CPU | TaMOs settings compute batch size from `torch.cuda.device_count()`. | Use CUDA or override batch size and worker count explicitly for static/tiny CPU debugging. |
| Worker crash, OpenCV crash, or hanging loader | Multiprocessing workers, OpenCV threading, bad image file, or non-picklable transform. | Set `settings.num_workers=0`, keep OpenCV thread suppression, validate a tiny dataset sample, then increase workers gradually. |
| CUDA device mismatch | A setting hard-codes `settings.device` or wraps in `MultiGPU`, while visible device selection changed. | Check `CUDA_VISIBLE_DEVICES`, `settings.device`, and `settings.multi_gpu` together. |
| Very slow first epochs | Large validation loaders or heavy dataset I/O. | Inspect loader sample counts, validation `epoch_interval`, worker count, and storage throughput. |
| Nondeterministic runtime or convolution selection issues | cuDNN benchmark mode is enabled by default. | Use the command builder with `--no-cudnn-benchmark` or call the Python API with `cudnn_benchmark=False`. |

## Data pipeline and actor mismatch failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing key in actor input data | Processing output does not match actor expectations. | Compare the chosen actor with its original processing class and sampler. Keep key names and tensor shapes compatible. |
| Shape mismatch in loss or model head | Feature size, output size, filter size, number of frames, or dense-label shape changed inconsistently. | Update `settings.feature_sz`, `settings.output_sz`, processing label generation, model constructor arguments, and actor loss expectations together. |
| Segmentation setting fails on bounding-box-only dataset | LWL/RTS processing expects masks. | Use VOS/mask datasets or generated/pregenerated masks required by that setting. |
| KeepTrack sampler fails on JSON fields | Candidate-matching JSON was generated by an incompatible tracker/parameter or interrupted. | Regenerate or repair the JSON through the tracker-execution workflow, then point `lasot_candidate_matching_dataset_path` at the valid file. |

## Safe diagnostic order

1. Run the command builder with `--list` and validate the pair.
2. Inspect the selected setting for `settings.env.*` fields and pretrained checkpoint filenames.
3. Verify local config paths and required files exist.
4. Verify imports for `ltr`, PyTorch, dataset dependencies, and optional extensions.
5. For code edits, run static checks and a tiny loader/model construction probe only if the user permits safe execution.
6. Only then launch full training.
