# Cross-cutting troubleshooting

Read this before changing dependencies or retrying a failing LeRobot command.
Classify the failure first; do not fix every problem by installing `all`.

## Install and import

- **`No matching distribution` or Python version error:** use Python 3.12+ and
  check the installed LeRobot version. Select a scoped extra from the route
  owner. Keep PyTorch, torchvision, CUDA/ROCm, and compiled policy extensions
  on compatible versions.
- **`lerobot` imports but a feature module fails:** identify the missing module
  and install only its documented extra (for example dataset/video,
  transformers-based policy, hardware SDK, async/gRPC, or environment). Re-run
  `lerobot-info`, then `python -m pip check`.
- **Resolver conflict:** inspect the environment-specific notes before adding
  a simulator or vendor package. Some simulators pin incompatible NumPy or
  package versions and need a separate environment/container. Do not overwrite
  a working policy/data environment.
- **Editable/local-vs-installed confusion:** inspect `import lerobot` and
  `importlib.metadata.version("lerobot")` from the intended Python. Refresh the
  skill when the code and package version are not the same baseline.

## Torch, CUDA, and memory

- **`torch.cuda.is_available()` is false:** check the torch build, driver
  visibility, `CUDA_VISIBLE_DEVICES`, and device permissions. A CPU fallback is
  valid only for a capability with a full CPU substitute; report GPU work as
  blocked or partial otherwise.
- **`no kernel image` / undefined symbol / extension import crash:** record
  torch version, CUDA tag, Python, GPU capability, and extension version. Use a
  matching wheel or the policy's native fallback; do not compile a large CUDA
  extension without a toolkit, memory, and explicit budget.
- **CUDA out-of-memory:** lower image resolution, batch size, action horizon,
  workers, or precision only when the policy supports it. Close unrelated
  processes and verify the checkpoint/model size before retrying. Do not present
  a smaller smoke run as evidence for the intended training budget.
- **CPU/GPU tensor mismatch:** inspect the policy config device and processor
  output together. Move all model inputs through the documented processor and
  validate shapes/dtypes before calling `forward` or `select_action`.

## Dataset, codec, and configuration

- **Metadata/feature/episode mismatch:** stop before constructing a reader or
  editing data. Compare `meta/info.json`, Parquet columns, episode ranges,
  task indices, dtypes/shapes, FPS, and stats. Use the dataset helper for a
  bounded local preflight.
- **Video file/codec/torchcodec error:** verify the referenced MP4 exists and
  try the supported decoder/FFmpeg path explicitly. An image-only or metadata
  success is not video support. Do not silently skip corrupted frames.
- **`KeyError`, unknown type, or draccus field error:** run the command's
  `--help`, check the registered choice spelling, and distinguish a config file
  path from a Hub/local repo id. Preserve dotted field names exactly.
- **Checkpoint loads but inference fails:** verify `config.json`, weights,
  pre/postprocessor files, feature names/shapes, normalization statistics, and
  the policy-specific extra. Do not rename features unless the checkpoint
  contract requires it.

## Hub, services, and remote work

- **Hub/Jobs/W&B authentication or network failure:** prove the local config and
  schema without credentials first. Ask before downloading, uploading, logging,
  or submitting a remote job; never paste tokens into commands or skill files.
- **gRPC/async endpoint or port mismatch:** compare role, host/port, protocol
  version, serialization fields, policy latency/frequency, and client/server
  config. Use the local config helper; do not start a daemon as a smoke check.
- **Annotation validation passes but the run fails remotely:** local schema
  validity does not prove model endpoint, task target, credentials, or remote
  dataset access. Report the missing remote gate separately.

## Hardware and simulation

- **Serial/CAN/SDK/camera failure:** inspect ports and permissions, select the
  exact robot/camera/motor type, verify calibration and firmware/SDK versions,
  and use mock/config checks before opening a device. Stop if the device is not
  identified or an emergency stop is unavailable.
- **Robot moves unexpectedly or replay is ambiguous:** stop the process and
  remove execution flags. Confirm robot, workspace, speed/limits, teleoperator,
  dataset, policy, and emergency-stop procedure before retrying.
- **Simulator import succeeds but rollout fails:** check the exact environment
  extra, external assets, renderer/MuJoCo/runtime, task name, and GPU/display
  requirements. Treat registry/config dispatch as weaker evidence than a real
  episode.
- **RL run diverges or hangs:** validate observation/action spaces, reward/task
  shape, environment reset/step behavior, seed, replay/queue capacity, and
  bounded rollout before changing algorithm settings. Avoid benchmark-scale
  retries until the tiny configuration passes.

## Stop conditions

Stop and return a structured blocked report when the required backend, data,
checkpoint artifacts, simulator assets, credentials, or physical safety control
is unavailable. Name the exact missing gate, the evidence already checked, the
safe fallback (if any), and the next authorized action.
