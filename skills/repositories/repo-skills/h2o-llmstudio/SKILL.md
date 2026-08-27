---
name: h2o-llmstudio
description: "Use H2O LLM Studio for no-code and CLI LLM fine-tuning,
  dataset/config preparation, training diagnostics, evaluation, prompting,
  export, and the Wave GUI runtime."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# H2O LLM Studio

Use this repo skill when a task involves H2O LLM Studio as a package or runtime: preparing datasets/configs, launching the Wave GUI, running or debugging fine-tuning experiments, understanding model/evaluation behavior, or prompting/exporting a trained experiment.

## Before you act

1. Read [repo provenance](references/repo-provenance.md) if the user is working in a checkout and you need to decide whether this skill matches the current source version.
2. Read [runtime setup](references/runtime-setup.md) before recommending install, app, Docker, CUDA, DeepSpeed, or working-directory commands.
3. Run or adapt [scripts/check_environment.py](scripts/check_environment.py) for safe import/backend/runtime-asset diagnostics before starting services, downloads, or training.
4. Use [cross-cutting troubleshooting](references/troubleshooting.md) for Python version, package layout, CUDA/NVIDIA, DeepSpeed, keyring, data/model download, and credential failures.

## Route by task

| User task | Read |
|---|---|
| Start or debug the no-code Wave GUI, Docker app, remote proxy, app workdir, settings, keyring, or browser/server lifecycle | [app-and-ui](sub-skills/app-and-ui/SKILL.md) |
| Build or validate YAML configs, choose problem types, map dataset columns, inspect data schemas, or round-trip config files | [configuration-and-data](sub-skills/configuration-and-data/SKILL.md) |
| Launch or diagnose `train.py`, CPU/GPU tiny smokes, multi-GPU/DeepSpeed, mixed precision, LoRA, output artifacts, or experiment status | [training-and-experiments](sub-skills/training-and-experiments/SKILL.md) |
| Understand model wrappers, losses, metrics, prediction files, plots, AI judge metrics, or generation vs forward-pass evaluation behavior | [modeling-and-evaluation](sub-skills/modeling-and-evaluation/SKILL.md) |
| Prompt a trained experiment, preflight saved artifacts, change generation parameters, publish to Hugging Face Hub, or hand off to h2oGPT | [export-and-prompt](sub-skills/export-and-prompt/SKILL.md) |

## Install and quick verification

From a user's own H2O LLM Studio runtime root, use the repo-supported Python 3.10 setup path before app or training work:

```bash
make setup
python scripts/check_environment.py --runtime-root . --check-config-assets
```

When `make setup` is not appropriate, create an isolated Python 3.10 environment and install the same locked/runtime dependency set described in [runtime setup](references/runtime-setup.md); do not modify a user-owned environment without approval.

## Fast runtime facts

- Package metadata expects Python 3.10 and a GPU-oriented PyTorch/Transformers stack.
- The documented runtime is usually a source-layout H2O LLM Studio runtime root or Docker image, not a tiny import-only library. Commands that refer to `llm_studio/...` should be run from the user's own runtime root or translated to an equivalent module/wrapper command.
- Production fine-tuning is NVIDIA-GPU oriented. CPU-style unit/integration configs can validate mechanics, but they do not prove real large-model throughput or DeepSpeed/multi-GPU behavior.
- The app and config layers use runtime assets such as `prompts/`, `model_cards/`, `static/`, and `pyproject.toml`; importing `llm_studio` alone is not enough to prove a working app/training root.
- Optional or external services include Hugging Face Hub/model downloads, Kaggle/HF datasets, OpenAI-compatible judge metrics, W&B logging, S3/Azure/H2O Drive data connectors, Docker/NVIDIA container runtime, and browser UI tests.

## Safe first checks

```bash
python scripts/check_environment.py --runtime-root . --check-cuda --check-config-assets
python sub-skills/configuration-and-data/scripts/inspect_config.py --help
python sub-skills/training-and-experiments/scripts/check_training_environment.py --help
python sub-skills/export-and-prompt/scripts/check_experiment_artifacts.py --help
```

These helpers diagnose environment/config/artifact readiness. They do not download models, start Wave, run training, call OpenAI, publish to Hugging Face, or mutate experiment outputs unless an option explicitly says so.

## When to stop and ask

Ask before running long training, downloading datasets/models, starting a public-facing Wave server, using API/HF/W&B/cloud credentials, publishing to Hugging Face Hub, modifying a user-owned Python environment, changing Docker/NVIDIA host setup, or overwriting an experiment output directory.
