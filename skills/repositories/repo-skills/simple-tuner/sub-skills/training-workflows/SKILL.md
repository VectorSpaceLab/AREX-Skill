---
name: training-workflows
description: "Plan and safely launch SimpleTuner training workflows across CLI
  configuration, model quickstarts, distributed backends, validation,
  checkpointing, and runtime troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# training-workflows

Use this sub-skill when a task is about planning or launching a SimpleTuner training run, choosing a platform install variant, selecting a model-family quickstart, deciding between CLI/configuration backends, planning distributed or memory-saving runtime, or diagnosing training-runtime failures.

Real model downloads, Hub access, dataset acquisition, cloud submissions, and actual training are manual/expensive actions. Do not start them unless the user explicitly approves the runtime cost, credentials, and target hardware.

## Router

1. **Install and CLI/config route**: start with [training CLI and config](references/training-cli-and-config.md) to choose `simpletuner configure`, `simpletuner train`, `simpletuner-train`, `ENV`, `CONFIG_BACKEND`, `CONFIG_PATH`, and JSON/TOML/env/cmd config style.
2. **Model-family quickstart**: use [model family quickstarts](references/model-family-quickstarts.md) to select the family/flavour/example level. If the request is about adapter formats, extraction, merge, conversion, LyCORIS internals, ControlNet adapter mechanics, or distillation method details, reroute to `sub-skills/model-and-adapter-tooling/`.
3. **Distributed and memory plan**: use [distributed and memory](references/distributed-and-memory.md) before changing `num_processes`, DeepSpeed, FSDP2, context parallelism, attention backends, quantization, offload, or resume topology.
4. **Validation, checkpointing, or failures**: use [troubleshooting](references/troubleshooting.md) for missing config/env, invalid backend, undersized dataset buckets, DeepSpeed+FSDP conflicts, context-parallel requirements, resume constraints, platform package mismatches, OOM, model access, and validation/checkpoint path issues.

## Reroute boundaries

- Dataloader schema, cache layout, dataset filtering, captions, image/video/audio/conditioning data, and `data_backend_config` internals: `sub-skills/data-and-config/`.
- Adapter export/extraction/conversion/merge, LoRA format migration, LyCORIS details, model registry inspection scripts, CaptionFlow, Prompt2Effect, and distillation method internals: `sub-skills/model-and-adapter-tooling/`.
- WebUI/API server modes, local job queue, workers, cloud providers, auth/quotas/notifications, and webhook operations: `sub-skills/webui-and-operations/`.
- Repository tests, code changes, frontend E2E policy, docs/translations, and public-text privacy for contribution work: `sub-skills/repo-development/`.

## Safe command builder

Use the bundled helper to print a command only; it never launches training:

```bash
python skills/disco/simple-tuner/sub-skills/training-workflows/scripts/build_training_command.py --help
python skills/disco/simple-tuner/sub-skills/training-workflows/scripts/build_training_command.py --env flux-lora --config-backend json -- max_train_steps=100 report_to=none
python skills/disco/simple-tuner/sub-skills/training-workflows/scripts/build_training_command.py --config-path config/flux-lora/config.json --config-backend json -- model_family=flux model_type=lora
```

## Evidence base

This sub-skill was distilled from `README.md`, `documentation/INSTALL.md`, `documentation/TUTORIAL.md`, `documentation/QUICKSTART.md`, `documentation/OPTIONS.md`, `documentation/DEEPSPEED.md`, `documentation/FSDP2.md`, `documentation/DISTRIBUTED.md`, `documentation/attention/FLEX.md`, `documentation/attention/SLA.md`, `documentation/evaluation/*.md`, `simpletuner/cli/train.py`, `simpletuner/train.py`, `simpletuner/helpers/training/*`, `simpletuner/examples/*/config.json`, `tests/test_attention_backend.py`, `tests/test_context_parallel_plans.py`, and `tests/test_fsdp_cmd_args.py`. Source evidence is cited by repo-relative name only; do not require a future agent to reopen the source checkout to use this sub-skill.
