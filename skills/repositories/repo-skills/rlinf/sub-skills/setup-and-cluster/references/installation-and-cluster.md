# Installation and cluster readiness

This reference helps future agents choose an RLinf setup path, verify readiness without mutation, and start/check Ray clusters. It is self-contained and intentionally avoids invoking RLinf installation by default.

## Setup decision tree

| Situation | Prefer | Why | What to decide |
|---|---|---|---|
| Reproducible embodied stack, GPU rendering, simulator assets, or many optional packages | Docker image or Docker build target | Embodied dependencies are large and platform-sensitive; images bundle one or more virtual environments and helper commands such as `switch_env` inside the container. | Hardware platform, image/build target, GPU/runtime flags, which bundled venv to activate. |
| Local source development, extension work, or exact Python/package control | UV/local virtual environment using RLinf's installer interface | Gives editable control and target-specific dependency selection. | `target`, `--venv`, `--platform`, `--python`, model/env/engine selector, mirror options. |
| Agentic/reasoning workloads with model-parallel backends | Local or Docker agentic/reason setup | Agentic dependencies include rollout engine pins and Megatron-related packages. | `agentic` target; `--engine sglang` or `--engine vllm`; separate venvs if both engines are needed. |
| Documentation build | Docs setup | Needs both agentic and embodied documentation dependencies. | `docs` target. |
| Only inspect an already-installed package | No install; run probes | Avoids unnecessary environment mutation. | Python executable, optional `--repo-root`, whether Ray is already running. |

### Installed package facts to expect

- Package name/version: `rlinf` / `0.4.0`.
- Requires Python `>=3.10`; default local installer Python is 3.11.14, with some environments requiring Python 3.10.
- Core dependencies include Ray `>=2.47.0`, Torch `>=2.5.0`, Hydra/OmegaConf, NumPy, datasets, and logging backends.
- Optional local install extras include `agentic`, `embodied`, `franka`, `xsquare_turtle2`, and `gim_arm`.

## Local installer selector matrix

Treat the installer as a selector interface, not a command to run automatically. If the user authorizes installation, construct a plan from these dimensions:

| Selector | Values evidenced for RLinf 0.4.0 | Notes |
|---|---|---|
| Target | `embodied`, `agentic`, `docs` | `embodied` requires an environment for most model workflows; `agentic` covers reasoning/agent stacks; `docs` builds documentation dependencies. |
| Hardware platform | `nvidia`, `amd`, `ascend`, `musa` | NVIDIA is the default/fully tested route. AMD uses ROCm selection; Ascend adds `torch-npu`; MUSA expects vendor-provided Torch/Torch-MUSA in the image interpreter. |
| Embodied model selector | `openvla`, `openvla-oft`, `openpi`, `gr00t`, `gr00t_n1d6`, `gr00t_n1d7`, `dexbotic`, `starvla`, `lingbotvla`, `dreamzero`, `qwen3_vl`, `abot_m0`, `molmoact2`, `evo1` | If no model is selected, environment-only installation is possible for supported environments. |
| Environment selector | `behavior`, `maniskill_libero`, `libero`, `metaworld`, `calvin`, `isaaclab`, `robocasa`, `robocasa365`, `franka`, `franka-dexhand`, `franka-franky`, `frankasim`, `robotwin`, `habitat`, `opensora`, `wan`, `genesis`, `xsquare_turtle2`, `liberopro`, `liberoplus`, `roboverse`, `embodichain`, `d4rl`, `dosw1`, `gim_arm`, `dummy`, `polaris` | Pick only the envs required by the user's workflow. |
| Agentic rollout engine | `sglang`, `vllm` | Engine versions pin different kernels; use separate venvs when both engines are required. |
| Common knobs | `--venv`, `--python`, `--torch`, `--use-mirror`, `--no-root`, `--no-flash-attn`, `--no-apex`, `--install-rlinf` | Use these to avoid broad optional installs and to respect host constraints. |

Do not claim a GPU/accelerator setup is ready from a CPU-only import. Use the probe script plus hardware-specific checks from the user's environment.

## Docker decision points

Docker is usually the fastest route for complex embodied workloads because the image can bundle simulator dependencies, assets, and multiple Python virtual environments. RLinf Docker build target names include:

- `reason` for agentic/reasoning stacks.
- `embodied-maniskill_libero`, `embodied-behavior-openvlaoft`, `embodied-behavior-openpi`, `embodied-metaworld`, `embodied-calvin`, `embodied-robocasa`, `embodied-robocasa365`, `embodied-isaaclab`, `embodied-franka`, `embodied-robotwin`, `embodied-opensora`, `embodied-wan`, `embodied-frankasim`, `embodied-embodichain`, `embodied-libero`, `embodied-liberopro`, `embodied-liberoplus`, `embodied-roboverse`, `embodied-polaris`, and `embodied-genesis` for embodied stacks.
- Platform base choices cover NVIDIA, AMD/ROCm, Ascend/CANN, and MUSA.

Inside a built image, expect virtual environments under `/opt/venv/` and a shell helper named `switch_env` to activate a model/environment venv. For GPU rendering, keep GPU runtime access and driver capabilities enabled; do not hide or overwrite image asset/venv directories unless the user explicitly accepts that consequence.

## Safe readiness probes

From this sub-skill directory:

```bash
python scripts/rlinf_env_probe.py
python scripts/rlinf_env_probe.py --json
```

When inspecting a local source checkout without installing it, prepend it only for the probe process:

```bash
python scripts/rlinf_env_probe.py --repo-root /path/to/rlinf/source
```

The probe checks Python, importability and versions for important packages, Torch/CUDA visibility, Ray CLI/status, and RLinf-related environment variables. It does not start Ray or install packages.

Minimum readiness checklist:

1. `rlinf` imports and reports the expected package version.
2. `ray` imports and `ray --version` is available; Ray should be `>=2.47.0`.
3. `torch` imports; `torch.cuda.is_available()` and device count match the intended accelerator plan when CUDA is required.
4. Optional backends (`sglang`, `vllm`, Megatron bridge packages, `transformer_engine`, `flash_attn`) import only when the selected workflow requires them.
5. Environment variables intended for Ray workers are set before `ray start` where Ray captures them.

## Single-node Ray startup

For a single machine, Ray may be auto-started by RLinf, but explicit startup makes state visible:

```bash
# Activate the intended Python environment first.
export RLINF_NODE_RANK=0
ray start --head --port=6379
ray status
python scripts/rlinf_env_probe.py --ray-status
```

Rules:

- Export `RLINF_NODE_RANK=0` before `ray start` even on one node when you want config behavior to match multi-node usage.
- If you installed packages, changed the Python executable, changed `RLINF_NODE_RANK`, or changed communication env vars after Ray started, run `ray stop` and start Ray again from the corrected shell.
- Do not call `ray.init()` manually before the RLinf driver constructs `Cluster`; RLinf sets its namespace, logging behavior, manager actors, and optional code sync.

## Multi-node Ray startup

On every node, activate the intended Python environment and export `RLINF_NODE_RANK` **before** starting Ray. Ranks are zero-based and must be unique. The head is usually rank 0.

Head node:

```bash
export RLINF_NODE_RANK=0
# Optional, when the host has multiple NICs:
# export RLINF_COMM_NET_DEVICES=eth0
ray start --head --port=6379 --node-ip-address=<head_ip>
```

Worker node:

```bash
export RLINF_NODE_RANK=<worker_rank>
# Optional, match the reachable NIC used by the head/workers:
# export RLINF_COMM_NET_DEVICES=eth0
ray start --address='<head_ip>:6379'
```

After all nodes join:

```bash
ray status
```

Confirm node count, per-node CPU/GPU resources, and `ALIVE` state. Then ensure the task YAML uses `cluster.num_nodes: <actual_node_count>`.

Important details:

- `--node-ip-address` must be the IP other machines can reach, not `127.0.0.1` or an unreachable container-only address.
- Firewalls/security groups must allow the Ray port and any needed worker communication ports.
- `RLINF_COMM_NET_DEVICES` selects the network interface for inter-node communication when multiple NICs exist.
- Ray freezes the Python interpreter path and environment variables at `ray start`; reinstalling or exporting after startup does not update already-started Ray workers.

## Optional code sync for non-shared filesystems

When the driver and workers do not share an identical local checkout, set code sync before the RLinf driver first initializes Ray:

```bash
export RLINF_CODE_WORKING_DIR=auto
```

Allowed values:

- unset, `0`, `false`, `off`, `no`: disabled; every node must have a compatible local RLinf package/tree.
- `auto`: infer the RLinf checkout/package root from the launch environment.
- Absolute path: a repository root containing package metadata plus `rlinf/`, or the `rlinf` package directory.

Only the `rlinf/` package subtree is packaged and shipped. Config files, model weights, datasets, simulator assets, checkpoints, and other large files must still be reachable on each node through local paths or shared storage.

