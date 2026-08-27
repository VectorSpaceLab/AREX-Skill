# ModelScope Package Overview

## Purpose

Read this reference when choosing which ModelScope surface to use, what optional extras to install, and what verification is safe before a workflow downloads models or uses accelerators.

## Public package identity

- Distribution: `modelscope`.
- Primary import: `modelscope`.
- Console scripts: `modelscope` and `ms`.
- Python support in current package metadata: Python `>=3.10`.
- Declared base dependency file: Hub runtime requirements.
- Verified private inspection version for this skill: `2.0.0+main`; see `repo-provenance.md` for source snapshot.

## Major package surfaces

| Surface | What it owns | Read next |
| --- | --- | --- |
| Hub and CLI | Repository download/upload, cache inspection/clearing, auth, endpoints, `snapshot_download`, `model_file_download`, `HubApi`. | `../sub-skills/hub-and-cli/SKILL.md` |
| Pipelines and models | `pipeline(...)`, `Pipeline`, `Model.from_pretrained`, registries, tasks, preprocessors, output keys, local config-driven inference. | `../sub-skills/pipelines-and-models/SKILL.md` |
| Datasets and config | `MsDataset.load`, dataset source modes, file IO, JSON/YAML/Python configs, local recipe validation. | `../sub-skills/datasets-config/SKILL.md` |
| Training and evaluation | `build_trainer`, `TrainingArgs`, fine-tuning/evaluation preflight, hooks, checkpoints, safe config previews. | `../sub-skills/training-and-evaluation/SKILL.md` |
| Serving/export/tools | FastAPI `modelscope server`, vLLM handoff, exporters, checkpoint conversion and weight-diff tools. | `../sub-skills/serving-export-and-tools/SKILL.md` |
| Customization/development | Custom pipeline/model/preprocessor scaffolding, registries, contribution tests/style, trust boundaries. | `../sub-skills/customization-and-development/SKILL.md` |

## Optional dependency groups

ModelScope is broad; do not install every extra by default.

| Extra/group | Typical use | Caution |
| --- | --- | --- |
| `hub` / base install | Hub APIs, CLI dispatch, downloads/cache, package import. | Network/credentials still needed for real remote operations. |
| `datasets` | `MsDataset`, Hugging Face datasets integration, local/remote dataset loading. | Remote Hub loads may download data; streaming still contacts remote endpoints. |
| `framework` | Core modeling/training utilities, transformers, config/data support. | May bring torch/transformers and compiled packages; choose CPU/GPU variants deliberately. |
| `server` | FastAPI/Uvicorn wrapper for `modelscope server`. | Starting a server can load models and allocate GPUs. |
| `cv`, `nlp`, `multi-modal`, `science`, `audio*` | Domain-specific model/pipeline/trainer implementations. | Large optional dependencies, version conflicts, GPUs, media libraries, and model downloads are common. Install only for selected task families. |
| `tests`, `docs` | Contributor verification and documentation build. | Not needed for using ModelScope as a package. |
| `all` | Broad non-audio stack. | Too broad for routine agents; can be slow or destabilizing. |

## Environment selection

- For safe inspection and planning, use a private Python 3.10/3.11 environment and install only base plus the extras the task needs.
- For portable inference checks, pass `device='cpu'` explicitly to `pipeline(...)` because the factory defaults to GPU when `device` is omitted.
- For CUDA/ROCm/MPS/vendor accelerators, verify the framework wheel, driver/runtime, package extra, and a tiny device operation in the target environment. A CPU import does not prove accelerator workflows.
- For vLLM, DeepSpeed, Megatron, TensorFlow 1.x, ONNX, audio, CV, and multi-modal workflows, treat requirements as workflow-specific and verify before execution.

## Safe verification tiers

| Tier | Examples | Safe by default? |
| --- | --- | --- |
| Import/version/help | Import `modelscope`, run `modelscope --help`, inspect signatures. | Yes. |
| Static/dry-run planners | Download command planner, TrainingArgs preview, dataset recipe validator, checkpoint conversion planner. | Yes. |
| Local tempdir smoke | Custom registered pipeline on CPU with no model download. | Usually yes. |
| Hub download or dataset load | `snapshot_download`, `modelscope download`, `MsDataset.load` remote ids. | Requires network/cache/credential policy. |
| Real inference/training/serving/export | `pipeline` with remote model id, `trainer.train`, `modelscope server`, exporters. | Requires model/data/backend/resource approval. |
| Destructive tools | Checkpoint conversion in-place, cache clear, remote upload/delete. | Requires explicit approval and backups when applicable. |

## Trust boundaries

- `trust_remote_code=True` permits execution of model-repository code/plugins. Use only after the source is known and trusted.
- Python config files execute top-level Python; prefer JSON/YAML for passive configs.
- Hub tokens, endpoint overrides, and credential persistence are private execution context; never embed them in scripts or public artifacts.
- Uploads and cache clears mutate remote or local state; plan first and obtain approval.
