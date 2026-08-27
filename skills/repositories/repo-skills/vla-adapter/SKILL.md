---
name: vla-adapter
description: "Guides VLA-Adapter tiny-scale vision-language-action model setup,
  fine-tuning, evaluation, deployment, and package API workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# VLA-Adapter External-Checkout Adapter

This skill is an **external-checkout adapter**. Its generated directory contains
only builders, validators, and documentation/references. It must not contain or
vendor the native `prismatic/`, `vla-scripts/`, `experiments/robot/`, or other
runtime trees. Those paths belong only to the separately provisioned native
checkout at `VLA_ADAPTER_REPO_ROOT`.

Use this skill when the task involves VLA-Adapter, Prismatic VLMs, tiny-scale
vision-language-action policies, LIBERO/CALVIN benchmark evaluation, ALOHA
real-robot deployment, LoRA adapter fine-tuning, OpenVLA checkpoint conversion,
or debugging the native checkout's workflows.

Set an absolute checkout root and install the native distribution before any
native import or workflow:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"  # import package: prismatic
```

The checkout must provide `prismatic/`, `vla-scripts/`,
`experiments/robot/`, `scripts/`, `pyproject.toml`, compatible pretrained
VLM/config assets, and a complete local checkpoint. LIBERO, CALVIN, and ALOHA
are external prerequisites: install the selected simulator/data stack,
CALVIN ABC→D checkout/assets, or ALOHA TFDS/ROS/robot dependencies. A
checkpoint must match the platform and include `config.json`, weights, and
`dataset_statistics.json` when native VLA action unnormalization is needed.

Every native command must begin with `cd <absolute-repo-root>` and must run
from `VLA_ADAPTER_REPO_ROOT`, never from this generated skill directory. The
bundled builders and validators are not native entrypoints: they only render
commands or inspect synthetic/local layouts. This skill is not self-contained,
does not install external prerequisites, and does not execute training,
evaluation, deployment, serving, robot clients, or package loading/conversion.

## First checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) before
   deciding whether this skill is current for a checkout or installed package.
2. Read [references/package-overview.md](references/package-overview.md) for the
   repository layout, supported workflows, dependency classes, and public model
   surfaces.
3. Run [scripts/check_vla_adapter_env.py](scripts/check_vla_adapter_env.py) in
   the target environment to check imports, PyTorch CUDA, TensorFlow/RLDS, and
   optional benchmark/robot stacks without launching training or a robot.
4. If install, backend, data layout, or optional dependency errors appear, read
   [references/troubleshooting.md](references/troubleshooting.md) and then route
   to the focused sub-skill below.

Minimal import smoke for a prepared package environment:

```bash
python - <<'PY'
import prismatic, torch
print("prismatic import: ok")
print("torch:", torch.__version__, "cuda:", torch.cuda.is_available())
PY
```

## Route by task

| Task shape | Read |
| --- | --- |
| Install, dependency selection, benchmark data/checkpoint placement, VLM config directories, LIBERO/CALVIN/ALOHA storage planning | [setup-and-data](sub-skills/setup-and-data/SKILL.md) |
| Build VLA-Adapter fine-tuning commands, choose VRAM profiles, configure LoRA/Pro/proprio/frozen options, handle W&B/log/checkpoint output | [training](sub-skills/training/SKILL.md) |
| Run or debug LIBERO and CALVIN evaluation plans, map checkpoints to suites, interpret success logs, avoid benchmark dependency traps | [evaluation](sub-skills/evaluation/SKILL.md) |
| Serve a policy, validate MsgPack/JSON action payloads, run ALOHA fake-client sanity checks, adapt real ROS topics safely | [deployment](sub-skills/deployment/SKILL.md) |
| Inspect the package layout/API reference and checkpoint surfaces without implementing loaders, action heads, or conversions | [package-apis](sub-skills/package-apis/SKILL.md) |

All linked sub-skills preserve the same external-checkout boundary and local
links; use the package API reference as a map, not as an implementation.

## Operating principles

- Treat CUDA as required for real model action generation, training, benchmark
  rollouts, and serving. CPU checks prove importability only.
- Treat LIBERO, CALVIN, FlashAttention, ROS, robot hardware, checkpoints, and
  datasets as optional stacks that must be installed or pointed to explicitly.
- Do not run full training, benchmark rollouts, or real robot clients until data
  roots, checkpoint layouts, unnormalization keys, GPU memory, and safety
  boundaries are checked.
- The repository uses command-line arguments to infer robot constants
  (`libero`, `calvin`, `aloha`, or `bridge`). If action dimensions look wrong,
  verify the launched command contains the intended platform word and read
  [package-apis/references/api-reference.md](sub-skills/package-apis/references/api-reference.md).
- Prefer the enhanced Pro checkpoints and Pro training flag unless a task asks
  to reproduce the original non-Pro baseline.

## Common entry points

The following paths are **skill-local** helpers and are invoked by absolute
skill path. They do not replace the native source entrypoints:

- Environment/import check: `python "$VLA_ADAPTER_SKILL_ROOT/scripts/check_vla_adapter_env.py" --repo-root "$VLA_ADAPTER_REPO_ROOT"`
- Data/checkpoint layout check: `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/setup-and-data/scripts/validate_data_layout.py" --benchmark libero --data-root "$VLA_ADAPTER_REPO_ROOT/data/libero" --checkpoint "$VLA_ADAPTER_REPO_ROOT/outputs/LIBERO-Spatial-Pro" --vlm-config-dir "$VLA_ADAPTER_REPO_ROOT/pretrained_models/configs"`
- Fine-tuning command renderer: `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/training/scripts/build_finetune_command.py" --repo-root "$VLA_ADAPTER_REPO_ROOT" --help`; native entrypoint is `vla-scripts/finetune.py`.
- Evaluation command renderer: `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/evaluation/scripts/build_eval_command.py" --repo-root "$VLA_ADAPTER_REPO_ROOT" --help`; native entrypoints are `experiments/robot/libero/run_libero_eval.py` and `vla-scripts/evaluate_calvin.py`.
- ALOHA command renderer: `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/deployment/scripts/build_aloha_launch.py" --repo-root "$VLA_ADAPTER_REPO_ROOT" --help`; native entrypoints are the server/client scripts named in deployment references.
- Synthetic MsgPack validator: `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/deployment/scripts/validate_msgpack_payload.py" --help`; it is not a server or client.
- Checkpoint layout validator: `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/package-apis/scripts/check_checkpoint_layout.py" --help`; it does not load a model.

`VLA_ADAPTER_SKILL_ROOT` is the installed/generated skill directory and
`VLA_ADAPTER_REPO_ROOT` is the separate native source checkout. Never resolve
native relative paths from the skill directory or copy native runtime trees
into it.
