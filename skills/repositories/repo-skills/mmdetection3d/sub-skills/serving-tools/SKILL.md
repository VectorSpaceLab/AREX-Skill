---
name: serving-tools
description: "Package, publish, inspect, and troubleshoot MMDetection3D serving utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDetection3D serving-tools sub-skill

Use this sub-skill when the task is one of:

- package a checkpoint for TorchServe-style serving,
- verify the packaging inputs before export,
- publish or convert a checkpoint for release,
- inspect training logs, FLOPs, or throughput,
- print configs or fuse Conv+BN for utility work.

This sub-skill is safe by default. The bundled checker only validates paths and required artifacts; it does not start servers, build containers, download weights, or run model execution.

## Start here

1. Identify the utility family: serving packaging, checkpoint publishing/conversion, log analysis, FLOPs/throughput, or config inspection.
2. Before packaging, run [`scripts/check_serving_artifacts.py`](scripts/check_serving_artifacts.py) to confirm the config, checkpoint, handler, model name, and export target are ready.
3. For the serving flow and handler assumptions, read [`references/serving.md`](references/serving.md).
4. For the utility script catalog and safe-use boundaries, read [`references/tools-reference.md`](references/tools-reference.md).
5. For common failures and stop conditions, read [`references/troubleshooting.md`](references/troubleshooting.md).

## Route away

- Choosing a model family, config alias, or checkpoint family belongs in `configuration-model-zoo`.
- Raw inference demo commands or inferencer APIs belong in `inference`.
- Training, testing, evaluation, TTA, distributed launch, and Slurm workflows belong in `training-evaluation`.
- Geometry, box conversion, coordinate systems, and visualization internals belong in `structures-visualization`.
- Dataset preparation and conversion belong in `data-preparation`.
- Custom component implementation belongs in `customization-extensions`.

## Minimal operating rules

- Do not run TorchServe, Docker, download checkpoints, or benchmark jobs unless the user explicitly asks for execution.
- Treat the bundled checker as a preflight only; it prints missing artifacts and exits, but it does not repair anything.
- Keep utility advice tied to local files and explicit config/checkpoint pairs.
- Prefer the bundled references over free-form guesses when the user asks about script flags or expected artifacts.
