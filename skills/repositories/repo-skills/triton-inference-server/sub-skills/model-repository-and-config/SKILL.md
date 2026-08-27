---
name: model-repository-and-config
description: "Create, validate, and troubleshoot Triton model repositories and
  config.pbtxt files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Repository and Config

Use this sub-skill when the user needs to create, inspect, validate, or debug Triton model repositories, `config.pbtxt`, custom config files, labels, version directories, or model-control behavior.

## Route Within This Sub-skill

- **Repository layout, version directories, local vs cloud repository paths**: read [`references/model-repository.md`](references/model-repository.md).
- **`config.pbtxt` fields, shapes, datatypes, batching, ensembles, backend-specific config details**: read [`references/config-reference.md`](references/config-reference.md).
- **Model load/unload mode, polling, safe repository mutation, and update behavior**: read [`references/model-management.md`](references/model-management.md).
- **Layout mistakes, config mistakes, model unload/load failure, and poll/explicit mode pitfalls**: read [`references/troubleshooting.md`](references/troubleshooting.md).
- **Static layout validation helper**: run [`scripts/validate_model_repository.py`](scripts/validate_model_repository.py).

If the user wants a server launch plan, route to [`../server-runtime-and-deployment/SKILL.md`](../server-runtime-and-deployment/SKILL.md). If the user wants to build a request payload, route to [`../client-protocols/SKILL.md`](../client-protocols/SKILL.md).

## Safe Default Workflow

1. Confirm the model repository root path and whether the user wants a static preflight or a live load error investigation.
2. Check that each model directory has a version subdirectory with the files required by the backend.
3. Verify the `config.pbtxt` name, `platform`/`backend`, `max_batch_size`, input/output names, datatypes, and dims.
4. Distinguish CPU-loadable models from GPU-only models before the user tries to launch Triton on CPU.
5. Use the validator script against a local repository copy or fixture before any live server start.

## Do Not Do Without Approval

- Pull model weights from the network, rewrite production repositories in place, or claim a static validation pass proves runtime load success.
- Treat `POLL` as a safe production mutation mode without warning about partial update observation.
