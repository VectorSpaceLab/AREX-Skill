# FastReID cross-cutting troubleshooting

Read this when a FastReID task fails before it clearly belongs to one focused
sub-skill, or when setup, imports, backends, data, config, checkpoints, and
optional deployment dependencies interact.

## Import and installation failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastreid'` | FastReID is a source-only checkout and is not installed as a distribution. | Run from a context where the package is importable, pass `--repo-root <FASTREID_REPO>` to bundled scripts, or add the checkout root to `PYTHONPATH`/a `.pth` file. |
| `pip install -e .` says there is no `setup.py` or `pyproject.toml` | This inspected commit has no packaging metadata. | Treat FastReID as a source tree; use explicit import path handling rather than package metadata. |
| `ModuleNotFoundError: yacs` | Config dependency missing. | Install `yacs` plus `pyyaml` in the target environment before using `get_cfg()`. |
| Import errors involving `collections.Mapping` on Python 3.10+ | Older code imports aliases removed from `collections`. | Prefer Python 3.9 for this checkout or patch imports to `collections.abc` in a controlled local fork. |
| `torch.cuda.is_available() == False` but the task expects CUDA | CPU PyTorch build, missing driver/runtime passthrough, or incompatible wheel. | Use a CUDA-capable PyTorch environment and verify a tiny CUDA tensor before training/eval. Do not treat CPU import as GPU validation. |

Use `scripts/check_fastreid_environment.py` for a safe import/config/optional
backend report before debugging deeper workflow failures.

## Config and weights failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Config merge fails on `_BASE_` | The config path is wrong or base files are not available relative to it. | Use an absolute config file path or keep recipe/base files in their expected relative layout. Run `setup-and-configuration/scripts/config_merge_check.py`. |
| `opts` parsing fails or a key has the wrong type | Odd number of CLI tokens, shell quoting issue, or invalid YACS key. | Put overrides after named flags as `KEY VALUE` pairs. Quote tuple/string values. Merge with the config helper before launching. |
| Run tries to download ImageNet pretraining | Recipe sets `MODEL.BACKBONE.PRETRAIN True`. | For offline smoke/eval, set `MODEL.BACKBONE.PRETRAIN False`; for real training, provide local pretrain weights if needed. |
| Eval-only cannot load checkpoint | `MODEL.WEIGHTS` is empty, points to the wrong path, or mismatches the architecture. | Set `MODEL.WEIGHTS <CHECKPOINT_FILE>` explicitly and confirm the config family matches the checkpoint. |

## Dataset and training failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Dataset not found | `FASTREID_DATASETS` unset/wrong or built-in layout missing. | Use `data-and-datasets/scripts/validate_dataset_layout.py` against the dataset root. |
| Query/gallery empty or metrics invalid | Test split folders/list files missing or parsed incorrectly. | Check dataset-specific layout and filename/list schema in `data-and-datasets/references/dataset-formats.md`. |
| Identity sampler error | Global batch/world size/`DATALOADER.NUM_INSTANCE` combination is invalid. | Use `training-and-evaluation/scripts/train_command_builder.py` to warn on divisibility and per-rank batch issues. |
| CUDA OOM | Batch size, image size, backbone, AMP, or workers too large for the GPU. | Reduce `SOLVER.IMS_PER_BATCH`, `TEST.IMS_PER_BATCH`, image size, or workers; use AMP only when the environment supports it. |
| `--resume` did not load expected weights | Resume uses `OUTPUT_DIR/last_checkpoint`, not arbitrary checkpoint selection. | Use `MODEL.WEIGHTS` for eval-only or initialization; use `--resume` only to continue an interrupted run in the same output directory. |

## Evaluation and inference failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Warning: Cython rank evaluation unavailable | Optional Cython extension was not compiled. | Accept Python evaluation for small checks or compile the rank Cython extension in the user's environment if speed matters. |
| `ImportError: cannot import name 'evaluate_rank' from 'fastreid.evaluation'` | This checkout does not re-export `evaluate_rank` at package level. | Import `evaluate_rank` from `fastreid.evaluation.rank` or patch legacy demo code accordingly. |
| Feature shape or color looks wrong | Input tensor layout or BGR/RGB conversion mismatch. | Use `modeling-and-inference/scripts/feature_extraction_smoke.py` to validate preprocessing. Demo-style paths convert OpenCV BGR images to RGB and resize to `INPUT.SIZE_TEST`. |
| Device mismatch | Model is on CUDA while input tensor is on CPU or vice versa. | Set `MODEL.DEVICE` explicitly and move tensors to the same device before model call. |

## Deployment and project-extension failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Export script fails before `--help` with `ModuleNotFoundError: onnx` | ONNX export dependencies are not installed. | Use `deployment-and-projects/scripts/check_deployment_dependencies.py`; install ONNX export dependencies only for ONNX workflows. |
| TensorRT import fails | TensorRT Python package/runtime is absent or not compatible with the GPU/driver. | Treat TensorRT as optional hardware-gated workflow; verify TensorRT and CUDA before export/inference. |
| Caffe export/inference fails | PyCaffe/protobuf stack is missing or incompatible. | Use the Caffe workflow only in a prepared Caffe environment; do not copy generated Caffe protobuf into new projects. |
| Project config has unknown keys or registry misses | Project package/config hook was not imported before merging/building. | Use `deployment-and-projects/scripts/project_import_probe.py` and import the project package before config merge/model/data construction. |

## When to stop and ask for more context

Stop rather than guessing when the task requires private datasets, model zoo or
pretrain downloads, local checkpoints, CUDA/TensorRT/Caffe hardware, multi-node
network settings, or a long training run whose budget and expected metrics are
not specified.
