---
name: training-and-configs
description: "Guides Nerfstudio method selection, ns-train command construction,
  typed config overrides, resume behavior, logging, CUDA, and reduced smoke
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Configs

Use this route when the task is to train a Nerfstudio model, choose a built-in
method, edit a typed config, resume from a run, or build a correct `ns-train`
command.

## What this route covers

- Built-in methods such as `nerfacto`, `splatfacto`, `instant-ngp`, `vanilla-nerf`, `tensorf`, `mipnerf`, `dnerf`, `depth-nerfacto`, `neus`, and `neus-facto`.
- CLI ordering: `ns-train {method} [method args] {dataparser} [dataparser args]`.
- The `--data` alias, dataparser overrides, viewer/logging options, CUDA/CPU choices, ray batch memory knobs, and multi-GPU flags.
- Resume and checkpoint distinction: `--load-dir` for model checkpoint loading during training, `--load-config` for loading a saved config where supported.
- Reduced CPU smoke checks versus real CUDA training.

## What this route excludes

- Raw capture conversion and `transforms.json` validation: use `data-preparation`.
- Viewer/eval/render/export after a run exists: use `visualization-and-export`.
- Packaging custom methods/dataparsers: use `api-extension`.

## Read/run these bundled files

- [`references/model-overview.md`](references/model-overview.md) for built-in method families and backend notes.
- [`references/configuration.md`](references/configuration.md) for typed config and CLI override rules.
- [`references/workflows.md`](references/workflows.md) for training, resume, logging, and multi-GPU recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for CUDA, tyro, OOM, and checkpoint issues.
- [`scripts/build_ns_train_command.py`](scripts/build_ns_train_command.py) to construct a command string without launching training.

## Safe workflow

1. Validate or identify the dataset directory.
2. Choose a method whose model/data assumptions match the scene and hardware.
3. Use `ns-train METHOD --help` and, when needed, `ns-train METHOD DATAPARSER --help` to verify flag ownership.
4. Build the command with method flags before dataparser flags.
5. Run a small CPU or CUDA smoke only when it is explicitly a smoke task; otherwise treat real training as a long GPU job.
6. Preserve the generated `config.yml` for viewer/eval/render/export handoff.
