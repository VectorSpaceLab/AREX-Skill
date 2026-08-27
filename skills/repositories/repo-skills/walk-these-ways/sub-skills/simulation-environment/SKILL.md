---
name: simulation-environment
description: "User-facing Go1 Isaac Gym environment and configuration guidance:
  Cfg and config_go1 setup, terrain, observations and history, reward scales,
  domain randomization, assets, installation and backend diagnosis, and safe
  static validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Simulation Environment

Use this sub-skill when the user needs static/API/configuration help for the
Go1 Isaac Gym environment: choosing and validating `Cfg` fields, applying
`config_go1`, understanding terrain and observation construction, checking
reward and domain-randomization surfaces, locating assets, or diagnosing
installation and backend prerequisites.

## Operating boundary

- This is a static, API, configuration, and prerequisite-diagnosis skill.
  Isaac Gym Preview 4 is absent in the construction environment, so do not
  launch simulation, training, playback, rendering, or native environment
  construction here.
- A successful PyTorch import or `torch.cuda.is_available()` result is not
  evidence that Isaac Gym or the simulator runtime works.
- Treat source evidence as already distilled into the bundled references. Do
  not tell future agents to open original repository files.
- Route PPO/training/checkpoints to `training-and-policy`, actuator fitting or
  actuator-network behavior to `actuator-network`, and physical Go1 operation
  or hardware safety to `robot-deployment`.

## Procedure

1. Read [configuration.md](references/configuration.md) for the effective Go1
   defaults, field names, configuration order, dimensions, and known static
   mismatches before suggesting edits.
2. Read [api-reference.md](references/api-reference.md) before describing
   constructors, wrapper behavior, or return values. Every API claim there is
   marked Isaac Gym-required and must not be presented as host-verified.
3. Read [runtime-prerequisites.md](references/runtime-prerequisites.md) for
   installation facts, the separation between PyTorch and Isaac Gym, and the
   limits of this host. Use [check_runtime.py](scripts/check_runtime.py) for a
   read-only diagnostic when a repository root is available.
4. Use [validate_config.py](scripts/validate_config.py) to validate a JSON
   configuration summary or the bundled documented Go1 static defaults. It
   never imports Isaac Gym and is suitable for CI or a machine without the
   simulator.
5. Use [troubleshooting.md](references/troubleshooting.md) to classify a
   failure before changing configuration. Keep missing optional dependencies
   and unverified backend behavior explicit.

## Bundled files

- [Configuration reference](references/configuration.md)
- [API reference](references/api-reference.md)
- [Runtime prerequisites](references/runtime-prerequisites.md)
- [Troubleshooting guide](references/troubleshooting.md)
- [Static configuration validator](scripts/validate_config.py)
- [Read-only runtime diagnostic](scripts/check_runtime.py)

## Handoff limit

The generated scope is static/API/configuration and prerequisite diagnosis
pending Isaac Gym. It does not certify simulator execution, CUDA PhysX
behavior, training quality, playback, checkpoints, actuator fitting, or robot
hardware deployment.
