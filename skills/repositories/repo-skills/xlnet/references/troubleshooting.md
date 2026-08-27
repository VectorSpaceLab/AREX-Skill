# XLNet cross-cutting troubleshooting

## When to read

Read this for install/import, model artifact, backend, and command-selection failures that can affect multiple XLNet workflows. Task-specific data and CLI failures live in the nearest sub-skill troubleshooting file.

## Legacy TensorFlow runtime problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AttributeError: module 'tensorflow' has no attribute 'contrib'` | TensorFlow 2.x runtime. XLNet source uses TensorFlow 1.x APIs. | Use a TensorFlow 1.x-compatible environment for original scripts, or port the code intentionally before running. For inspection-only work, run the root `scripts/check_xlnet_environment.py` diagnostic. |
| `Descriptors cannot not be created directly` from protobuf during TensorFlow import | TensorFlow 1.x with too-new protobuf. | Install a protobuf 3.20.x runtime or set `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` as a short-term workaround. Prefer a pinned environment for repeatable jobs. |
| `DuplicateFlagError` while importing several XLNet scripts | `run_classifier.py`, `run_squad.py`, `run_race.py`, `train_gpu.py`, and other CLIs define overlapping Abseil flags. | Inspect each CLI in a fresh Python process. Do not import multiple flag-heavy scripts in a long-lived notebook kernel or service process. |
| `ModuleNotFoundError: tensorflow.contrib.tpu.proto` when importing TPU pretraining code | Some TensorFlow 1.x wheels do not include the TPU proto path required by `tpu_estimator.py`. | Treat TPU pretraining as an environment-specific optional backend. Use a TPU-capable legacy TensorFlow runtime, or use `train_gpu.py` when GPU pretraining is acceptable. |
| `ImportError: sentencepiece` or SentencePiece load failure | Missing package or wrong path to `spiece.model`. | Install `sentencepiece` and pass the `spiece.model` from the same release bundle as the checkpoint/config whenever possible. |

## Model artifact problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Config loading fails with missing keys | `xlnet_config.json` does not match XLNet's expected key set. | Run `sub-skills/model-api/scripts/inspect_xlnet_config.py` or root `scripts/check_xlnet_environment.py --config ...`. Required keys are listed in `references/model-overview.md`. |
| Checkpoint restore reports many uninitialized variables | Wrong checkpoint prefix, incompatible config, or using a fine-tuned checkpoint for a different head/scope. | Verify `--model_config_path`, `--init_checkpoint`, `--cls_scope`, and task head settings. Keep pretrained initialization separate from fine-tuned `model_dir`. |
| Evaluation uses the wrong checkpoint | Confusing `init_checkpoint`, `model_dir`, `predict_ckpt`, and `eval_all_ckpt`. | In train mode, `init_checkpoint` initializes variables. In eval mode, checkpoints normally come from `model_dir`; in predict mode use `predict_ckpt` when needed. |
| Reused TFRecord/feature cache gives stale results | `output_dir` already contains files from a different sequence length, task, tokenizer, or split. | Use a fresh `output_dir` or pass the task script's overwrite flag. Keep cache directories task- and configuration-specific. |

## Backend and hardware problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| GPU out-of-memory at sequence length 512 | XLNet-Large has high memory use, especially for SQuAD/RACE. | Use XLNet-Base, lower `max_seq_length`, reduce per-GPU `train_batch_size`, add GPUs, or switch to TPU recipes. See `references/model-overview.md` for README memory anchors. |
| Multi-GPU training works but eval metrics look wrong | Evaluation sharding across multiple GPUs is tricky in this codebase. | Follow the README pattern: train on multiple GPUs if needed, then evaluate with `num_core_per_host=1` on one GPU. |
| TPU command cannot find checkpoints or write outputs | Mixing local paths and GCS paths. | Task scripts often preprocess locally while checkpoints/model outputs live in GCS. Verify each `--model_config_path`, `--spiece_model_file`, `--init_checkpoint`, `--output_dir`, and `--model_dir` path intentionally. |
| Cloud TPU resolver errors | Missing `--tpu`, `--tpu_zone`, `--gcp_project`, service account, or incompatible runtime. | Confirm GCP/TPU setup outside XLNet first; the generated skill command builders only print commands and do not provision TPUs. |

## How to choose the nearest sub-skill

- Use `sub-skills/model-api/` for configs, tokenizer helpers, TensorFlow graph APIs, checkpoints, losses, and optimizer wiring.
- Use `sub-skills/classification/` for `run_classifier.py`, GLUE MNLI/STS-B, IMDB, Yelp-5, and processor-backed classification/regression.
- Use `sub-skills/squad-qa/` for SQuAD JSON preprocessing, prediction, n-best outputs, and no-answer thresholding.
- Use `sub-skills/race-reading-comprehension/` for RACE four-choice passage/question/answer workflows.
- Use `sub-skills/data-pretraining/` for raw corpus validation, pretraining TFRecord generation, and `train_gpu.py`/`train.py` pretraining commands.

When the user gives a broad request such as "fine-tune XLNet," ask which task family and dataset shape they mean before selecting task-specific flags.
