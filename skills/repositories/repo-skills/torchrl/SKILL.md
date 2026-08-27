---
name: torchrl
description: "Use TorchRL for TensorDict-first reinforcement-learning
  environments, collectors, replay buffers, modules, objectives, LLM/RLHF/VLA
  workflows, services, rendering, and maintainer-safe repository changes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TorchRL

Use this repo skill when the task involves TorchRL (`torchrl`), the PyTorch reinforcement-learning library built around TensorDict data, composable environments, collectors, replay buffers, modules, losses, trainers, LLM/RLHF/VLA extensions, services, rendering, or contributing to the `pytorch/rl` repository.

## First checks

1. Confirm the installed package and backend scope before making claims:

   ```bash
   python - <<'PY'
   import torch, tensordict, torchrl
   print('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.is_available())
   print('tensordict', tensordict.__version__)
   print('torchrl', torchrl.__version__)
   PY
   ```

2. For a reusable base smoke, run [scripts/check_torchrl_env.py](scripts/check_torchrl_env.py). It imports the major TorchRL surfaces, runs a native `PendulumEnv` rollout, samples a small replay buffer, inspects `rlrender` help, and reports optional backend availability without downloading models or starting services.
3. If the task depends on Gym, MuJoCo, DM Control, IsaacLab, VMAS, Ray, vLLM, SGLang, LeRobot/OpenX, video codecs, or CUDA kernels, read [backend compatibility](references/backend-compatibility.md) and the owning sub-skill's troubleshooting file before deciding whether a CPU result is enough.
4. If you are working in a source checkout, compare it with [repository provenance](references/repo-provenance.md). Refresh this skill if commit, package version, public entry points, or dirty source state differ materially.

## Route by task

| Task signal | Read |
| --- | --- |
| `EnvBase`, `PendulumEnv`, `GymEnv`, specs, `TransformedEnv`, `Compose`, transforms, `check_env_specs`, `step_mdp`, `SerialEnv`, `ParallelEnv`, simulator wrappers | [envs-and-transforms](sub-skills/envs-and-transforms/SKILL.md) |
| `Collector`, rollout loops, evaluator, `frames_per_batch`, `sync`, backend selection, replay buffers, storages, samplers, prioritized replay, HER, memmap, Ray replay | [collectors-and-replay](sub-skills/collectors-and-replay/SKILL.md) |
| `Actor`, `ProbabilisticActor`, `ValueOperator`, `QValueActor`, TensorDictModule keys, specs, distributions, recurrent GRU/LSTM modules, multi-agent models, model-based wrappers | [modules-and-policies](sub-skills/modules-and-policies/SKILL.md) |
| PPO/SAC/DQN/DDPG/TD3/IQL/CQL/MAPPO losses, value estimators, `set_keys`, target updaters, trainers, Hydra configs, SOTA algorithm recipes | [objectives-and-training](sub-skills/objectives-and-training/SKILL.md) |
| LLM post-training, RLHF/GRPO/SFT, `ChatEnv`, `LLMCollector`, vLLM/SGLang wrappers, VLA schemas/actions, service registry, render CLI, video/checkpoint surfaces | [llm-vla-and-services](sub-skills/llm-vla-and-services/SKILL.md) |
| Editing TorchRL source, adding public APIs, tests, docs, benchmarks, deprecations, optional-dep CI labels, GPU markers, Hydra config parity | [development-and-testing](sub-skills/development-and-testing/SKILL.md) |

## Install and dependency stance

- General users: `pip install torchrl` with a PyTorch build appropriate for the task. Match PyTorch and TensorDict versions; TorchRL releases are synchronized with the PyTorch ecosystem.
- Source contributors: use an editable install only in a checkout, after installing the intended PyTorch build. When using `uv` with a preselected PyTorch/nightly build, use `--no-deps` for editable installs to avoid unintended framework downgrades.
- Install optional extras narrowly. Examples: `torchrl[dm_control]`, `torchrl[gym_continuous]`, `torchrl[marl]`, `torchrl[offline-data]`, `torchrl[llm]`, `torchrl[llm-vllm]`, `torchrl[llm-sglang]`, `torchrl[grpo]`, `torchrl[vla]`, `torchrl[rendering]`, `torchrl[video]`.
- Do not install broad dev/test/LLM/simulator extras just to answer a CPU-verifiable API question. Document unverified optional backend limits instead.

Read [install and extras](references/install-and-extras.md) for the package metadata, console entry points, and safe install/probe commands.

## Core mental model

TorchRL components pass structured `TensorDict` objects through the whole loop:

```text
TensorDict -> policy/module writes action/log_prob -> environment writes next/reward/done
           -> collector batches trajectories -> replay buffer stores/samples
           -> loss reads named keys -> optimizer updates ordinary PyTorch parameters
```

Keep keys explicit, prefer `NestedKey` tuples for nested data, validate specs early, and route optional backend failures to the narrow owner rather than rewriting the full pipeline.

## Tiny CPU integration smoke

For a no-download, no-simulator sanity check across the main RL path, run these bundled helpers from their local skill directories after installing TorchRL:

```bash
python scripts/check_torchrl_env.py --steps 3 --check-cli
python sub-skills/envs-and-transforms/scripts/smoke_env_rollout.py --steps 3 --check-specs
python sub-skills/modules-and-policies/scripts/smoke_actor.py
python sub-skills/collectors-and-replay/scripts/smoke_collector.py
python sub-skills/objectives-and-training/scripts/inspect_loss_keys.py --loss ClipPPOLoss
```

When wiring PPO, remember that `ClipPPOLoss` defaults `sample_log_prob` to `action_log_prob`; make the actor write that key or remap the loss with `set_keys(sample_log_prob=...)`.

## Cross-cutting troubleshooting

Read [troubleshooting](references/troubleshooting.md) for install/import failures, version mismatches, optional dependency errors, CLI misuse, backend claims, and when to stop instead of silently falling back. Workflow-specific failure matrices live in each sub-skill's `references/troubleshooting.md`.
