# Repo Provenance

Generated skill id: `reinforcement-learning`

## Source snapshot

- Public repository: `https://github.com/rlcode/reinforcement-learning.git`
- Commit: `3d421f6e4d11c6f170c67a3b449f15d0a940fe1a`
- Branch: `master`
- Exact tag: none detected
- Package/distribution metadata: `project.name = "reinforcement-learning"`, `version = "0.1.0"`, `requires-python = "==3.11.*"`
- Installability note: dependency metadata exists, but the checkout is a flat script collection and editable package installation may fail unless packaging discovery is configured. Treat workflows as standalone scripts rather than an import package.

## Dirty state at generation

The source checkout had untracked `skills/` content while this skill was generated. That directory contains generated skill, verification artifacts, and production logs; it is not part of the upstream source evidence used for algorithm behavior.

## Evidence paths

- `README.md`
- `pyproject.toml`
- `uv.lock`
- `1-grid-world/1-policy_iteration.py`
- `1-grid-world/2-value_iteration.py`
- `1-grid-world/3-sarsa.py`
- `1-grid-world/4-q_learning.py`
- `1-grid-world/5-deep_sarsa.py`
- `1-grid-world/6-reinforce.py`
- `1-grid-world/env.py`
- `2-cartpole/1-dqn.py`
- `2-cartpole/2-a2c.py`
- `2-cartpole/3-ppo.py`
- `2-cartpole/env.py`
- `3-atari/1-dqn.py`
- `3-atari/2-ppo.py`
- `3-atari/env.py`
- `4-atari-hard/1-ppo-rnd.py`
- `4-atari-hard/2-go-explore.py`
- `4-atari-hard/3-robustify.py`
- `4-atari-hard/env.py`
- `4-atari-hard/env_go_explore.py`
- `4-atari-hard/env_robustify.py`
- `4-atari-hard/extract_demo.py`
- `wiki/install_guide_osx+ubuntu.md` and `wiki/how-to-windows.md` as historical setup/background evidence only

## Refresh triggers

Refresh this skill if any of these change:

- New or removed algorithm workflow files.
- CLI flags, checkpoint names, model/state_dict shapes, or run-directory contracts.
- Dependency versions or Python requirement in project metadata.
- Atari preprocessing, env keys, device selection, W&B behavior, envpool/raw-ALE split, Go-Explore archive/demo schema, or robustification curriculum logic.
- Public README benchmark/protocol descriptions.
