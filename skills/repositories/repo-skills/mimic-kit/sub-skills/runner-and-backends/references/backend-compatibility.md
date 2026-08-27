# Backend compatibility

This reference summarizes the supported engine backends, the asset formats they accept, and the verified environment limits for this checkout.

## What is actually verified here

Verified in the inspection environment:

- repository Python requirements installed successfully
- PyTorch CUDA works and can allocate on a CUDA device
- source imports succeed when the checkout root and `mimickit/` directory are on `PYTHONPATH`
- `python -m compileall -q mimickit tools` succeeds
- parser / converter help checks succeed for the bundled utility scripts
- tiny converter fixtures work for the motion conversion helpers

Not verified here:

- Isaac Gym runtime installation
- Isaac Lab / Isaac Sim runtime installation
- Newton / Warp runtime installation
- simulator-native train / test / view workflows

Treat the simulator stacks as external prerequisites, not as verified facts of this environment.

## Engine table

| Engine | Engine config | Builder branch | Supported asset formats | Notes |
| --- | --- | --- | --- | --- |
| Isaac Gym | `data/engines/isaac_gym_engine.yaml` | `IsaacGymEngine` | `.xml` only for spawned assets | Uses MJCF-style XML assets. The engine asserts on other extensions. |
| Isaac Lab | `data/engines/isaac_lab_engine.yaml` | `IsaacLabEngine` | `.usd` or `.usda` input, normalized to `.usd` | Spawns rigid objects and articulations from USD assets. |
| Newton | `data/engines/newton_engine.yaml` | `NewtonEngine` | `.xml` and `.urdf` | Uses MuJoCo XML or URDF. Unsupported extensions assert. |

## Engine config facts

All three bundled engine YAMLs share the same basic control shape:

- `control_mode: pos`
- `control_freq: 30`
- `env_spacing: 5`

The sim frequency differs by engine:

- Isaac Gym: `sim_freq: 120`
- Isaac Lab: `sim_freq: 120`
- Newton: `sim_freq: 240`

The bundled Isaac Gym engine config also defines `ground_contact_height: 0.3`.

## Asset-format notes

### Kinematic validation vs simulator spawn

The kinematic character loaders can understand multiple file types, but that does **not** mean every backend can spawn them.

- `.xml` is the common MJCF path and is the safest choice for Isaac Gym and Newton.
- `.usd` is the native path for Isaac Lab.
- `.urdf` is accepted by Newton's model builder.

### Representative asset evidence in this checkout

- `data/assets/humanoid/humanoid.xml`
- `data/assets/humanoid/humanoid.usd`

### Common mismatch pattern

A frequent failure is picking an environment whose `char_file` extension does not match the selected engine backend.

Examples:

- Isaac Gym + `.usd` asset path -> wrong backend / format combination
- Isaac Lab + raw `.xml` asset path -> wrong backend / format combination
- Newton + `.usd` asset path -> unsupported asset extension

## Backend prerequisites

### CUDA / torch

The current host can run CUDA-enabled torch code. That is sufficient for:

- source inspection
- parser and config checks
- CUDA tensor smoke tests
- non-simulator helper workflows

It is **not** a substitute for a simulator backend.

### Simulator stacks

To run the real runner workflows, install the matching external simulator stack and its required assets:

- Isaac Gym for Isaac Gym presets
- Isaac Lab / Isaac Sim for Isaac Lab presets
- Newton + Warp for Newton presets

### Data prerequisites

The repo intentionally treats several assets as external downloads or placeholders:

- motion clips under `data/motions/`
- pretrained models under `data/models/`
- training logs under `data/logs/`
- some object assets referenced by task / vault configs

If a run fails because the env config points at a missing asset, the fix is usually to download the external data or switch to a config that references available files.

## Readiness guidance

Use this rule of thumb:

- **Torch CUDA verified** means the host can run the Python / tensor side of MimicKit.
- **Simulator installed** means the chosen backend can actually build and step environments.
- **Simulator native workflow verified** means both the backend and its required assets were actually run successfully.

Do not collapse those three into one claim.
