---
name: deployment-and-robots
description: "Export ProtoMotions trackers, validate deployment input contracts,
  test MuJoCo deployment, and add or troubleshoot robot assets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProtoMotions deployment and robots

Use this sub-skill for G1 deployment tracker workflows, ONNX export, standalone MuJoCo validation, tracker input semantics, real-robot integration cautions, custom robot configs, MJCF/USD conversion, and cross-simulator robot issues.

## Read first

- `references/deployment-contract.md`: ONNX tracker inputs, frame conventions, MuJoCo validation, and real-robot safety.
- `references/onnx-export.md`: export artifact roles and checkpoint/config requirements.
- `references/custom-robots-and-assets.md`: adding robots, asset requirements, MJCF/USD, and factory registration.
- `references/troubleshooting.md`: deployment, input-frame, robot asset, and simulator migration failures.
- `scripts/inspect_tracker_yaml.py`: summarize a deployment YAML sidecar.
- `scripts/tracker_alignment_smoke.py`: pure NumPy smoke for the heading/reference alignment contract.

## Deployment action pattern

1. Verify the checkpoint directory includes `resolved_configs_inference.pt` or an accepted fallback config.
2. Export the policy to `unified_pipeline.onnx` plus `unified_pipeline.yaml` using a CPU-capable environment with PyTorch and ProtoMotions; no simulator should be needed for export.
3. Inspect YAML input/output metadata before wiring a deployment framework.
4. Validate in standalone MuJoCo before real hardware.
5. Preserve heading alignment, root-local angular velocity frame, action post-processing, acceleration clamp, EMA action filter, and PD target semantics.
6. Require explicit human approval and safety procedures for real robot execution.

## Custom robot action pattern

1. Provide MJCF as the source-of-truth robot asset.
2. Define robot config: body-name mappings, trackable body subset, asset config, default root height, PD controls, and per-simulator params.
3. Register the robot name in the factory.
4. Run factory/config smokes before simulator instantiation.
5. Validate in a random-pose or simple simulation check before training.
6. For IsaacLab, handle MJCF-to-USD conversion and D6 workaround behavior carefully.

## Non-negotiable safety

Real-robot deployment can cause unsafe physical motion. Never skip MuJoCo validation, PD/action post-processing checks, emergency-stop verification, or human authorization when moving from simulation to hardware.
