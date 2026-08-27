# Troubleshooting

This file collects cross-cutting failures that affect multiple AutoTrain Advanced workflows.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` while importing `autotrain` | Torch / vision / audio stack is missing or incompatible | Install a matching `torch`, `torchvision`, and `torchaudio` build for your platform, then rerun the import check. |
| `autotrain --help` fails before printing help | A core dependency such as `torch` or `accelerate` cannot import | Fix the Python environment first; the CLI imports many submodules eagerly. |
| `python -m pip check` reports broken requirements | Mixed package versions or partially repaired wheels | Reinstall the pinned package set in the inspection environment until `pip check` is clean. |

## Backend and accelerator issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA is not visible | CPU-only torch build, missing driver, or missing CUDA libs | Install a CUDA-enabled PyTorch wheel and confirm the host exposes an NVIDIA GPU. |
| `autotrain` works, but GPU workflows are slow | The current runtime is CPU-only or the GPU wheel is not active | Use the GPU-capable environment for training/backends and keep CPU only for import checks. |
| `setup --update-torch` changes the environment unexpectedly | The setup helper is a maintainer-style mutation command | Use it only when you explicitly want to replace the current torch/xformers stack. |

## CLI and config problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `autotrain vlm` is rejected as an invalid choice | VLM is not a registered top-level CLI subcommand | Use the app/API/config flow under `vision-multimodal`. |
| Config parsing stops on a missing field | A task-specific YAML config is incomplete or the task alias is wrong | Validate the file with `scripts/validate_config.py` and compare it against the owning sub-skill's workflow reference. |
| Project name errors mention alphanumeric or length limits | `AutoTrainParams` validates `project_name` before training starts | Use a short alphanumeric name with hyphens only. |

## Data-layout problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Text or CSV training complains about missing columns | Wrong column mapping or mismatched task family | Use the text/tabular validator and check the task-specific column names in the owning sub-skill. |
| Image classification rejects the directory | Folder layout, file count, or extension rules do not match the preprocessor | Rebuild the dataset to match the expected image-folder layout. |
| Object detection / image regression / VLM rejects metadata | Missing `metadata.jsonl`, missing required keys, or unsupported column mapping | Check the metadata schema in the vision sub-skill and the bundled validator. |

## Auth and deployment problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `autotrain app --share` fails | `NGROK_AUTH_TOKEN` is missing | Set the token before using the share mode. |
| Cloud backend routes fail with auth errors | Missing or invalid Hugging Face token / username | Confirm the token has write access and that the backend-specific auth variables are set. |
| Local UI refuses a new run because another job is active | The local runner keeps one job at a time | Stop the running job first or switch to a non-local backend. |

## Utility command problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Adapter merge fails to load the base model | Wrong model path, missing token, or remote-code restriction | Verify the base model and adapter paths and check the `ALLOW_REMOTE_CODE` behavior. |
| `convert_to_kohya` fails on the input file | The source file is not a safetensors LoRA state dict | Confirm the input path points at the expected LoRA artifact. |

## Where to go next

- Read `sub-skills/cli-config/references/workflows.md` for CLI and config routing details.
- Read `sub-skills/llm-training/references/troubleshooting.md` for PEFT, quantization, and LLM-specific backend issues.
- Read `sub-skills/text-and-tabular/references/troubleshooting.md` for CSV/JSONL and column mapping errors.
- Read `sub-skills/vision-multimodal/references/troubleshooting.md` for folder and metadata layout issues.
- Read `sub-skills/app-backends/references/troubleshooting.md` for auth, jobs, and hosted-backend failures.
- Read `sub-skills/model-tools/references/troubleshooting.md` for adapter merge and conversion failures.
