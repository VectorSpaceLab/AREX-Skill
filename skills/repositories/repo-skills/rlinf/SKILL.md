---
name: rlinf
description: "Routes RLinf repository tasks for distributed reinforcement
  learning setup, embodied and agentic workflows, extension development,
  evaluation operations, and debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RLinf repo skill

Use this skill when a task asks about RLinf, a distributed reinforcement-learning stack for embodied agents, reasoning/agentic LLM workflows, SFT/offline RL, reward models, Ray/Hydra cluster execution, or RLinf-specific source extensions.

This skill is operational guidance. It is not permission to run long training, evaluation, Ray cluster lifecycle commands, Docker builds, model/data downloads, robot motion, checkpoint conversion, or dataset mutation. Start with read-only inspection and ask for explicit approval before side-effecting or expensive work.

## Fast start

1. Read [`references/package-overview.md`](references/package-overview.md) for the architecture map and verified task/model/env routing constants.
2. Run [`scripts/rlinf_public_api_snapshot.py`](scripts/rlinf_public_api_snapshot.py) in the target environment when you need to verify the installed package version, imports, task types, model types, or env types.
3. Pick one sub-skill from the route table below. Most real tasks need exactly one primary sub-skill plus a setup or operations cross-link.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when symptoms span install, Ray, config, optional backends, runtime logs, or ambiguous ownership.
5. Check [`references/repo-provenance.md`](references/repo-provenance.md) before trusting this skill for a newer checkout; refresh when the commit, dirty state, package metadata, examples, docs, or public APIs changed.

## Sub-skill route table

| User task signals | Read this sub-skill | What it covers |
| --- | --- | --- |
| install target, Docker vs UV, Ray start/status, `RLINF_NODE_RANK`, multi-node, `cluster.num_nodes`, `component_placement`, heterogeneous node groups, worker/channel/placement APIs | [`setup-and-cluster`](sub-skills/setup-and-cluster/SKILL.md) | Installation planning, non-mutating environment probes, Ray cluster setup, Hydra cluster config, execution modes, scheduler mental model, and placement troubleshooting. |
| ManiSkill, LIBERO, RoboTwin, RoboCasa, Behavior, IsaacLab, Franka/real-world, OpenVLA/OFT/OpenPI/GR00T/DreamZero/StarVLA/Evo1, embodied PPO/GRPO/SAC/DAgger/RLT, reward data, offline RL, `ROBOT_PLATFORM`, MuJoCo/EGL | [`embodied-workflows`](sub-skills/embodied-workflows/SKILL.md) | Embodied recipes, config preflight, simulator/model/asset requirements, real robot safety, reward data/offline/SFT intersections, and embodied troubleshooting. |
| math/VQA reasoning RL, Qwen/DeepSeek, GRPO/PPO with LLMs, SGLang/vLLM rollout, coding online RL, Continue integration, AgentLightning, SearchR1, rStar2, WideSeek-R1, SFT/VLM SFT, reward services | [`reasoning-agent-workflows`](sub-skills/reasoning-agent-workflows/SKILL.md) | Reasoning/agentic recipes, rollout backend and data prerequisites, config inspection, service/judge requirements, SFT/reward intersections, and agentic troubleshooting. |
| add model/env/algorithm/reward/worker/runner, `register_model`, `RLINF_EXT_MODULE`, `SupportedEnvType`, policy loss/advantage registry, install/Docker/CI/docs/e2e updates, contributor policy | [`extension-development`](sub-skills/extension-development/SKILL.md) | Extension touchpoints, registries, source-edit recipes, distributed registration pitfalls, install/Docker/CI/docs checklists, style/tests, and contribution rules. |
| metrics, TensorBoard/W&B/SwanLab, checkpoints, resume, evaluations, profiling, auto-placement, parity/log analysis, replay buffers, checkpoint tools, CI test selection, NCCL/Gloo/CUDA/SGLang/EGL failures | [`operations-evaluation-debugging`](sub-skills/operations-evaluation-debugging/SKILL.md) | Evaluation planning, run artifact inspection, metric/checkpoint layout, resume, profiling, data/checkpoint utilities, CI/test choice, and runtime failure triage. |

## Installation and readiness quick check

- First choose the smallest public install target: embodied workflows need an embodied model/env pair, reasoning/agentic workflows need the agentic stack plus a rollout engine/version choice, docs-only work needs only docs dependencies, and reproducible deployments may prefer the documented Docker image family.
- If the user is working in a live RLinf checkout, the `setup-and-cluster` sub-skill explains how to map that target to the repo-maintained installer selectors without running them by default.
- After activating the chosen public environment, verify with `python -c "import rlinf; print(rlinf.__file__)"`, `ray --version`, and the bundled [`scripts/rlinf_public_api_snapshot.py`](scripts/rlinf_public_api_snapshot.py).
- Do not run install commands unless the user has approved environment mutation; use `setup-and-cluster` to plan the minimum target first.

## Repository-wide facts to verify first

- Public package/distribution: `rlinf`, version `0.4.0` in the snapshot used to build this skill.
- Core runtime: Ray for distributed processes; Hydra/OmegaConf for YAML composition; PyTorch for model/algorithm code.
- Confirmed task types: `embodied`, `embodied_eval`, `reasoning`, `reasoning_eval`, `coding_online_rl`, `sft`, and `offline`.
- Confirmed training backends: `fsdp` and `megatron`.
- Confirmed rollout backends: `sglang` and `vllm`.
- Full training/evaluation often needs GPUs or vendor accelerators, model checkpoints, simulator assets, datasets, services, or real hardware; read-only imports and static config checks are not full workflow validation.

## Safe operating defaults

- Prefer static YAML inspection, environment probes, artifact audits, and narrow unit/static tests before native e2e or GPU jobs.
- Do not treat missing optional packages as a bug until the selected workflow and install target are known.
- Do not launch original repository examples or scripts as a skill-default action. Use bundled scripts for safe checks and ask before running user-provided launchers.
- When a workflow spans sub-skills, keep one owner: setup handles Ray/placement, task sub-skills handle configs/recipes, operations handles logs/checkpoints/evals, and extension handles source changes.
- For real robots, require explicit operator approval, calibrated hardware, workspace safety, and e-stop readiness before any motion or controller script.

## Bundled root references and script

- [`references/package-overview.md`](references/package-overview.md) — architecture map, verified routing constants, run assembly flow, and sub-skill ownership.
- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting symptom map and safe triage ladder.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source snapshot and refresh baseline.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — structured managed router metadata.
- [`scripts/rlinf_public_api_snapshot.py`](scripts/rlinf_public_api_snapshot.py) — read-only package/API snapshot helper.
