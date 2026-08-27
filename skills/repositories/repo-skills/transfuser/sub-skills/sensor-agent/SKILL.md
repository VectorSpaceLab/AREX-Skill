---
name: sensor-agent
description: "Operate a trained TransFuser model through the CARLA sensor-agent
  interface, with checkpoint, sensor, tensor, control, and safety guidance that
  preserves the external CARLA runtime boundary."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TransFuser Sensor Agent

Use this sub-skill to prepare or diagnose the learned `HybridAgent` runtime for
CARLA Leaderboard sensor-track evaluation. It covers the agent entry point,
checkpoint-directory contract, backbone-dependent sensors, preprocessing,
route-to-target transforms, CUDA placement, ensembling, PID control, and
stuck/emergency behavior.

## Route The Task

1. For entry-point, configuration-directory, checkpoint, ensemble, CUDA, or
   Leaderboard interface questions, read
   [agent-runtime.md](references/agent-runtime.md).
2. For sensor IDs, camera/LiDAR preprocessing, tensor shapes, coordinates, GPS
   route planning, or target-point construction, read
   [sensor-and-tensor-contracts.md](references/sensor-and-tensor-contracts.md).
3. For action repetition, waypoint ensembling, NMS, PID conversion, stuck
   recovery, or emergency braking, read
   [control-and-safety.md](references/control-and-safety.md).
4. For missing CARLA/CUDA, bad `args.txt`, checkpoint-prefix mismatches,
   architecture drift, missing sensors, or route failures, read
   [troubleshooting.md](references/troubleshooting.md).
5. Before arranging a CARLA evaluation, run the bundled, side-effect-free
   preflight:

   ```bash
   python scripts/validate_agent_config.py /path/to/team-config
   ```

   Add `--json` for machine-readable output or `--strict` to make warnings
   fail. The validator parses JSON and checks checkpoint files statically; it
   does not import CARLA or PyTorch, deserialize weights, allocate CUDA memory,
   run inference, launch a server, or download anything.

## Inputs And Outputs

- Input configuration is a directory containing `args.txt` and one or more
  `.pth` model state-dict files. The directory, not `args.txt`, is the
  Leaderboard `TEAM_CONFIG` value.
- The Python agent module must expose `get_entry_point()` returning exactly
  `HybridAgent`; `HybridAgent` implements the Leaderboard `AutonomousAgent`
  interface and returns `carla.VehicleControl` from `run_step`.
- The learned runtime is CUDA-only as implemented. CPU-only checks can validate
  files and schemas but cannot prove model inference.
- Route execution needs an externally supplied global plan, synchronized sensor
  frames, and a CARLA 0.9.10.1-compatible Python API/server stack.

## Boundaries

This bundle deliberately does **not** launch CARLA, build evaluation commands,
download checkpoints, run model inference, or modify checkpoints. Route full
Longest6/local evaluation to the sibling `carla-evaluation` sub-skill, and
route model training or checkpoint provenance to `model-training`.

The verified inspection environment had Python 3.7, CUDA, PyTorch
1.12.1+cu113, `mmcv-full` 1.6.0, `mmdet` 2.25.0, and `timm` 0.6.7; model,
data, config, and train imports passed. The CARLA Python module was absent.
Therefore preserve an explicit external dependency on CARLA 0.9.10.1, its
Python API, a running server, and the compatible Leaderboard/scenario-runner
stack. Do not interpret static validation as end-to-end simulator readiness.
