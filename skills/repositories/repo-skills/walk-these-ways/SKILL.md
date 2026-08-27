---
name: walk-these-ways
description: "Guide static and backend-aware Walk These Ways Go1 simulation
  configuration, PPO/PPO-CSE policy workflows, actuator-network data handling,
  and safe Unitree Go1 deployment preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Walk These Ways

Use this repo skill when a task names **Improbable-AI/walk-these-ways** or asks
about its Go1 locomotion environment, PPO/PPO-CSE/RMA policies, actuator
networks, checkpoints, or Unitree Go1 deployment boundary.

This is a self-contained operating context. Use the bundled references and
read-only helpers; do not require the original checkout to remain available.

## First route and safety gate

1. Read [repo provenance](references/repo-provenance.md) when version freshness,
   package identity, or source evidence matters.
2. Run [check_installation.py](scripts/check_installation.py) for a read-only
   package/import/backend report. A PyTorch CUDA result is not an Isaac Gym
   result.
3. Select exactly one primary route:
   - [simulation-environment](sub-skills/simulation-environment/SKILL.md) for
     Go1 `Cfg`, `config_go1`, observations, history, terrain, rewards, domain
     randomization, assets, and simulator prerequisites.
   - [training-and-policy](sub-skills/training-and-policy/SKILL.md) for PPO or
     PPO-CSE/RMA dimensions, rollout/history contracts, checkpoints, export,
     and bounded policy evaluation.
   - [actuator-network](sub-skills/actuator-network/SKILL.md) for deployment-log
     validation, six-feature sample extraction, CPU model checks, and explicitly
     bounded actuator-network training planning.
   - [robot-deployment](sub-skills/robot-deployment/SKILL.md) for Go1 policy
     artifact review, LCM/RC/controller contracts, safety, network/container
     prerequisites, and deployment planning without actuation.
4. For a cross-route question, start here, preserve the route boundaries, and
   read the nearest references from each involved sub-skill before proposing a
   change.

## Verified scope and hard limits

The verified construction scope is static/API/configuration guidance, policy
shape and artifact checks, actuator data/model checks, and deployment planning.
The following are **not** verified on the construction host:

- Isaac Gym Preview 4 simulator construction, stepping, native PPO training, or
  native playback. The simulator is a separately installed NVIDIA dependency;
  it is not replaced by a CPU import or a CUDA-Torch probe.
- Unitree Go1 closed-loop actuation, SDK startup, LCM publication, calibration,
  network mutation, Docker launch, SSH/rsync transfer, or motor commands.

Keep these as `BLOCKED_REQUIRED_BACKEND` or an equivalent explicit limitation
when reporting a result. Never silently downgrade a missing required backend to
pass. Never execute a robot, controller, transfer, privileged, or network
mutation command from this skill.

## Shared operating contracts

- The package snapshot is `go1_gym==1.0.0` from the recorded source commit;
  see provenance for the exact revision and relative evidence paths.
- The simple Go1 environment contract is 42 actor observations, 18 declared
  privileged observations, 15 history frames (flattened width 630), and 12
  actions. The checked-in PPO-CSE training recipe is a separate 70-observation,
  2-privileged-value, 30-frame contract with flattened history width 2100 and
  12 actions. Do not confuse frame count with flattened width.
- A successful static helper, package import, or CPU TorchScript/model-shape
  check proves only that narrow contract. It does not prove simulator physics,
  learned locomotion quality, sim-to-real behavior, or safe robot actuation.
- Treat pickle checkpoints and model files as caller-owned artifacts. Do not
  unpickle untrusted `parameters.pkl`; validate explicit paths and shapes first.

## Installation and minimal check

Install the public package in an isolated caller-owned environment from a
trusted checkout or package source, then run:

```bash
python -m pip install -e .
# from this skill directory
python scripts/check_installation.py --json
```

The helper is read-only and only reports package/module presence. It does not
install Isaac Gym or prove simulator or robot readiness.

## Cross-cutting troubleshooting

Use [troubleshooting.md](references/troubleshooting.md) for installation,
optional dependencies, path/config validation, backend gates, and cross-route
failures. The sub-skill troubleshooting references own workflow-specific
failures.

## Safe construction boundary

Bundled scripts are diagnostics, validators, or deterministic offline data
helpers. They accept explicit paths, avoid source-relative discovery, do not
write unless an explicit safe output is requested, and do not start external
services. Any native simulator, training, logger, deployment, Docker, SDK,
LCM, SSH, rsync, sudo, or motor action requires a separately approved and
backend-qualified operator workflow outside this skill.
