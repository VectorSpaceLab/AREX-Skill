# RLinf Package Overview

## Purpose

RLinf is a distributed reinforcement-learning infrastructure for embodied agents, reasoning/agentic LLM workflows, SFT/offline RL, reward models, and heterogeneous cluster execution. Read this reference for the package mental model before choosing a sub-skill.

## Architecture map

| Area | What it owns | Key public concepts |
| --- | --- | --- |
| Configuration | Hydra/OmegaConf YAML composition and validation | `runner.task_type`, `cluster`, `algorithm`, `actor`, `rollout`, `env`, `reward`, `critic`, `data` |
| Scheduler | Ray process groups, placement, channels, hardware resources | `Cluster`, `Worker`, `WorkerGroup`, `Channel`, `PlacementStrategy`, node groups |
| Runners | Training/eval loops for each task family | embodied, async embodied, reasoning, reasoning eval, coding online RL, agent, AgentLightning, SFT, offline |
| Workers | Remote actor/rollout/env/reward/inference/sft processes | FSDP/Megatron actor workers, SGLang/vLLM rollout, env workers, reward workers |
| Algorithms | Advantage, loss, reward, and support math | PPO, GRPO, SAC, CrossQ, IQL, DAPO/Reinforce-style variants, registry decorators |
| Models | Embodied policies and tokenization/model wiring | OpenVLA/OFT, OpenPI/OpenPI_RLinf, GR00T, DreamZero, StarVLA, Evo1, MLP/CNN/Flow/CMA, Qwen/DeepSeek families |
| Environments | Simulator and real-world env adapters | ManiSkill, LIBERO, RoboTwin, IsaacLab, MetaWorld, Behavior, CALVIN, RoboCasa, FrankaSim, RealWorld, D4RL, Polaris, world models |
| Hybrid engines | Rollout/training backend integration | SGLang, vLLM, FSDP, Megatron, weight syncers |
| Data/eval/tools | Datasets, replay buffers, checkpoint tools, auto-placement, evaluation scripts | reasoning/VLM datasets, LeRobot utilities, eval configs, parity/log tools |

## Verified routing constants

Inspection of RLinf 0.4.0 confirmed:

- Task types: `embodied`, `embodied_eval`, `reasoning`, `reasoning_eval`, `coding_online_rl`, `sft`, `offline`.
- Training backends: `megatron`, `fsdp`.
- Rollout backends: `sglang`, `vllm`.
- Environment type values: `maniskill`, `maniskill_rlt`, `libero`, `robotwin`, `isaaclab`, `metaworld`, `behavior`, `calvin`, `robocasa`, `robocasa365`, `realworld`, `frankasim`, `habitat`, `opensora_wm`, `wan_wm`, `genesis`, `embodichain`, `roboverse`, `d4rl`, `polaris`.
- Model type values include `qwen2.5`, `qwen2.5_vl`, `qwen3`, `qwen3_vl`, `qwen3_moe`, `openvla`, `openvla_oft`, `molmoact2`, `openpi`, `openpi_rlinf`, `starvla`, `mlp_policy`, `rlt_mlp_policy`, `rlt_td3_mlp_policy`, `gr00t`, `dexbotic_pi`, `dexbotic_dm0`, `dreamzero`, `cnn_policy`, `flow_policy`, `cma`, `lingbotvla`, `abot_m0`, `resnet`, `cfg_model`, `recap_value_model`, `steam_value_model`, `qwen3_vl_moe`, `deepseek_v3`, `gr00t_n1d6`, `gr00t_n1d7`, and `evo1`.

Use [`../scripts/rlinf_public_api_snapshot.py`](../scripts/rlinf_public_api_snapshot.py) in a target environment to refresh these facts before relying on them for code changes.

## How an RLinf run is assembled

1. The user chooses an entrypoint or launcher and a Hydra YAML config.
2. `validate_cfg` normalizes and checks the composed config.
3. A `Cluster` attaches to the Ray cluster and discovers nodes, accelerators, hardware labels, and environment variables captured when Ray started.
4. Component placement maps worker groups such as actor, rollout, env, reward, critic, inference, and agent onto resources.
5. Worker classes create Ray actor groups via `create_group(...).launch(...)`.
6. The selected runner drives rollout, reward computation, advantage/return calculation, actor/critic updates, checkpointing, validation, and logging.

## Sub-skill ownership

- Use `setup-and-cluster` when the question is about installing RLinf, Ray cluster lifecycle, node ranks, component placement, or scheduler APIs.
- Use `embodied-workflows` for simulators, VLA/robot policies, real-world data collection, reward-model data, embodied offline RL, and embodied configs.
- Use `reasoning-agent-workflows` for math/VQA reasoning, agentic RL, coding online RL, SearchR1/rStar2/WideSeek, AgentLightning, rollout backends, SFT, and service/reward integration.
- Use `extension-development` for adding algorithms, models, envs, workers, runners, rewards, config validation, install/Docker/CI/docs/tests.
- Use `operations-evaluation-debugging` for metrics, checkpoints, resume, evaluation, profiling, auto-placement, data/checkpoint utilities, CI/test selection, and log triage.

## Safety and cost defaults

- Do not run training, evaluation, Ray start/stop, asset downloads, model downloads, Docker builds, robot motion, checkpoint conversion, or dataset mutation unless the user explicitly authorizes that operational work.
- Prefer static config inspection and read-only artifact checks before GPU/cluster execution.
- When full workflow validation requires GPUs, simulator assets, model checkpoints, network services, or real robots, state those prerequisites instead of treating a CPU import as proof of the workflow.
