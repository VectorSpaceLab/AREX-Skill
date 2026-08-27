# LeRobot quick reference

Read this when the task spans more than one LeRobot route or when choosing an
extra/backend before opening a detailed sub-skill.

## Package and command surface

- Distribution: `lerobot`; public package import: `lerobot`; Python: `>=3.12`.
- Core commands: `lerobot-info`, `lerobot-train`, `lerobot-eval`,
  `lerobot-rollout`, `lerobot-record`, `lerobot-replay`, `lerobot-calibrate`,
  `lerobot-teleoperate`, `lerobot-dataset-viz`, `lerobot-edit-dataset`,
  `lerobot-convert-dcp`, `lerobot-annotate`, and device/setup discovery tools.
- Configuration uses draccus-style dotted fields such as
  `--dataset.repo_id`, `--policy.type`, `--policy.device`, and `--env.type`.
  Confirm exact flags with `<command> --help` for the installed version.

## Route ownership

| Need | Owner | First evidence |
|---|---|---|
| Dataset v3 storage, schema, episode/feature checks, transforms, streaming, video, edits | `dataset-workflows` | `data-formats.md`, `workflows.md` |
| Policy/config/processor/device/checkpoint/training/eval/rollout | `policy-training-inference` | `model-overview.md`, `configuration.md` |
| Physical robot/camera/motor/teleoperator/calibration/record/replay | `robot-control-data-collection` | `safety.md`, `hardware-overview.md` |
| Simulator/env/RL/rewards/benchmark setup | `simulation-and-rl` | `environment-overview.md`, `compatibility.md` |
| Plugins/custom components/async/transport/annotation/Jobs | `extensions-and-services` | `extension-api.md`, `services.md` |

## Extra selection

Begin with the smallest feature group that owns the task. Common groups are
`dataset`, `training`, `hardware`, `viz`, `evaluation`, `async`, `annotations`,
a policy group such as `act`, `pi`, `smolvla`, `groot`, `diffusion`, or `peft`,
and an environment group such as `pusht`, `libero`, or `metaworld`.

Important boundaries:

- Dataset/video workflows may need `lerobot[dataset]`, PyAV/torchcodec, and a
  working FFmpeg codec. Importing `torchcodec` alone does not prove decoding.
- Training generally needs `lerobot[training]`, a compatible PyTorch build,
  data, and enough device memory. A parser or preprocessing smoke is not a
  training result.
- Hardware extras install SDKs but do not create serial/CAN permissions,
  cameras, motors, calibration, or a safe workspace.
- Environment extras vary. Some documented environments are not resolvable as
  ordinary extras or require separate assets/images; use the simulation matrix.
- Policy extras are scoped. Install the named policy family rather than all
  optional models; many need transformers, tokenizers, diffusers, PEFT, or
  qwen-vl-utils.

## Backend and side-effect vocabulary

- `cpu`: valid for package/config/data checks when the behavior has a full CPU
  substitute.
- `cuda`: prove `torch.cuda.is_available()` and a small device operation before
  claiming GPU execution. Record the torch/CUDA variant and device memory.
- `simulator-specific`: a registry/config import does not prove that simulator
  assets, MuJoCo, rendering, or benchmark tasks are installed.
- `physical-hardware`: never infer device readiness from class imports or mock
  tests. Confirm ports, permissions, calibration, emergency stop, workspace,
  and an explicit actuation decision.
- `network-credentials`: Hub, W&B, HF Jobs, annotation servers, and model
  downloads require a separate consent and credential gate.

## Handoff fields

When handing work between routes, preserve: package/version, exact source
revision, dataset root/repo/revision, feature keys/shapes/dtypes, episode/FPS
assumptions, policy/checkpoint plus processor files, environment/task, device,
output path, optional extras, and which side effects were authorized or skipped.
