---
name: sim2sim-deployment
description: "Deploy exported TorchScript humanoid policies in MuJoCo sim-to-sim."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Sim2Sim Deployment

Use this sub-skill when you already have an exported TorchScript policy and need to validate the XBot-L MuJoCo assets, choose plane vs terrain, and launch the rendered sim-to-sim loop safely.

## Use this when
- You have a TorchScript policy such as `policy_1.pt` or `policy_example.pt`.
- You want to pick the plane MJCF or the terrain MJCF before launch.
- You need to confirm the 705-D observation contract and 12-D action contract before opening the viewer.
- You want a command builder and static validator that do not run the 60s rollout.

## Route elsewhere when
- You still need to train, resume, checkpoint, or export a policy. Use `training-and-evaluation`.
- You need to change `XBotLCfg` observation/action sizes, frame stack, or control constants. Use `environment-customization`.
- You need Isaac Gym train/play native verification. That remains `BLOCKED_REQUIRED_BACKEND` here when the proprietary backend is unavailable; this sub-skill only consumes exported policies.

## Bundled helpers
- `references/workflow.md`
- `references/policy-and-assets.md`
- `references/troubleshooting.md`
- `scripts/build_sim2sim_command.py`
- `scripts/validate_sim2sim_assets.py`

## Operator checklist
1. Validate the repo assets and, optionally, the policy shape.
2. Choose plane or terrain.
3. Build the launch command.
4. Confirm a graphical display path before running MuJoCo.

## Short contract
- Policy input: 705 by default, or an explicitly overridden input width when diagnosing a matching export.
- Policy output: 12 actions.
- Simulation loop: MuJoCo + viewer, not headless.
- Main source of truth: the bundled references and scripts in this sub-skill tree.
