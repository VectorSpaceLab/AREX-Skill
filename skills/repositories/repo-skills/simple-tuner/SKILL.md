---
name: simple-tuner
description: "Use SimpleTuner for diffusion model training, dataloaders,
  model/adaptor tooling, WebUI/API operations, and repository maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# SimpleTuner repo skill

Use this skill when a task names SimpleTuner, `simpletuner`, `simpletuner-train`, SimpleTuner WebUI/API, SimpleTuner dataloaders, packaged model examples, LoRA/LyCORIS/ControlNet training, CaptionFlow, Prompt2Effect, DeepSpeed/FSDP2, or contributing to this repository.

This is an operating repo skill. It should be usable without reopening the source checkout. Use the bundled references and scripts here, and do not run model downloads, real training, cloud submissions, credentialed operations, checkpoint rewrites, or source-repo mutations unless the user explicitly approves the side effect and target.

## First checks

1. If the task is about whether SimpleTuner is installed, read [references/install-and-entrypoints.md](references/install-and-entrypoints.md) and run [scripts/check_simpletuner_environment.py](scripts/check_simpletuner_environment.py) if a read-only probe is useful.
2. If the task may depend on source freshness, read [references/repo-provenance.md](references/repo-provenance.md). Refresh this skill when the checkout commit, package metadata, public entry points, docs, examples, or tests changed materially.
3. If the task is broad, route to one focused sub-skill below. Do not answer complex training, data, model, WebUI, and maintainer questions only from this root router.
4. If a failure crosses install, backend, data, training, operations, and maintainer boundaries, start with [references/troubleshooting.md](references/troubleshooting.md), then jump to the owning sub-skill.

## Route by task

| user intent | read |
|---|---|
| Install SimpleTuner, choose hardware extra, inspect entry points, list packaged examples, or run a minimal import/CLI check. | [references/install-and-entrypoints.md](references/install-and-entrypoints.md), [scripts/check_simpletuner_environment.py](scripts/check_simpletuner_environment.py), [scripts/list_simpletuner_examples.py](scripts/list_simpletuner_examples.py) |
| Plan or launch `simpletuner train`, choose config backend/env/example, select model-family quickstart, plan validation/checkpointing, or diagnose DeepSpeed/FSDP/context-parallel/accelerator/memory issues. | [sub-skills/training-workflows/SKILL.md](sub-skills/training-workflows/SKILL.md) |
| Author or validate `data_backend_config`, dataloader JSON, text/image/conditioning caches, captions, image/video/audio datasets, S3/Hugging Face/Webshart backends, or ControlNet conditioning data. | [sub-skills/data-and-config/SKILL.md](sub-skills/data-and-config/SKILL.md) |
| Choose model family/flavour, PEFT vs LyCORIS vs ControlNet, LoRA format/export, adapter extraction/conversion/merge, model registry inspection, CaptionFlow, Prompt2Effect, or distillation/experimental features. | [sub-skills/model-and-adapter-tooling/SKILL.md](sub-skills/model-and-adapter-tooling/SKILL.md) |
| Operate WebUI/server/API, local job queue, GPU allocation, workers, cloud jobs, auth, API keys, quotas, approvals, audit, metrics, backups, notifications, or webhooks. | [sub-skills/webui-and-operations/SKILL.md](sub-skills/webui-and-operations/SKILL.md) |
| Modify SimpleTuner source/tests/docs/templates, select validation, review plans, handle frontend E2E, update translations, preserve untracked files, or scan public text before publishing. | [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md) |
| Understand which source scripts were copied, adapted, wrapped, or left reference-only. | [references/source-script-map.md](references/source-script-map.md) |

## Package and command facts

- Distribution: `simpletuner`.
- Import package: `simpletuner`.
- Verified package version at skill creation: `4.7.0`.
- Python support from metadata: `>=3.12,<3.14`.
- Verified console entry points: `simpletuner`, `simpletuner-train`, `simpletuner-configure`, `simpletuner-inference`.
- Root CLI help exposed commands: `train`, `examples`, `configure`, `server`, `shutdown`, `cloud`, `jobs`, `quota`, `notifications`, `auth`, `backup`, `database`, `metrics`, `webhooks`, and `worker`.
- Installed metadata exposed 41 model families and 110 packaged examples during skill creation.

## Install variant quick guide

Use public install commands and match the target runtime:

```bash
pip install 'simpletuner[cuda]'
pip install 'simpletuner[cuda13]' --extra-index-url https://download.pytorch.org/whl/cu130
pip install 'simpletuner[rocm]' --extra-index-url https://download.pytorch.org/whl/rocm7.1
pip install 'simpletuner[apple]'
pip install 'simpletuner[cpu]'
```

Do not treat CPU importability as proof of GPU training readiness. If the user asks for actual training or backend verification, route through `training-workflows` and require hardware/model/data approval before expensive actions.

## Bundled root helpers

```bash
python skills/disco/simple-tuner/scripts/check_simpletuner_environment.py --json
python skills/disco/simple-tuner/scripts/check_simpletuner_environment.py --probe-torch
python skills/disco/simple-tuner/scripts/list_simpletuner_examples.py --filter flux --limit 20
```

These helpers are safe by default. They do not download models, start servers, run training, submit jobs, or require the original source checkout.

## Cross-skill cautions

- Training commands can trigger downloads and long GPU jobs. Use command builders and validation first; run only after explicit user approval.
- Dataloader mistakes often surface as training failures. Check `data-and-config` before changing model or distributed settings.
- Adapter conversion and safetensors merge workflows can rewrite large checkpoint files. Use dry-run/preflight and require output-path approval.
- WebUI/API/queue/cloud actions can affect active jobs, users, costs, and credentials. Use skeleton builders until the user confirms the target server and operation.
- Repository contributions must use `unittest`, not pytest, and public text must not contain local machine identity.

## Import and router metadata

The structured router metadata for managed repo-skill import is in [references/repo-routing-metadata.json](references/repo-routing-metadata.json). The user requested **not to import** this generated skill in the creation run, so this runtime tree is staged only in the repository output directory until a future explicit import decision.
