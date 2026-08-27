# ProtoMotions troubleshooting

## Install and import failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: isaacgym` | IsaacGym is not on PyPI and was not manually installed | Use a Python 3.8 IsaacGym-specific environment and install the NVIDIA Preview 4 Python API before ProtoMotions. |
| IsaacLab import fails or reports unsupported version | ProtoMotions targets a pinned IsaacLab/IsaacSim stack | Use the documented Python 3.12 IsaacLab workspace and install ProtoMotions into that workspace, not a generic unrelated env. |
| Torch imports before IsaacGym/IsaacLab and backend crashes | Import-order contract violated | Parse args first, call `import_simulator_before_torch(simulator)`, then import `torch`. |
| `protomotions info` reports optional simulator modules unavailable | Only the base/MuJoCo stack is installed | Install the specific backend environment; do not install all extras together. |
| `GLFWError: DISPLAY environment variable is missing` during import or help | Headless server imports MuJoCo/glfw | Use headless mode for runtime checks or provide an EGL/X11 setup for rendering. Treat import-only warnings as nonfatal if checks pass. |

## Asset failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Asset tree missing from package | Package-only install or incomplete wheel/assets | Run `protomotions info --json`; set `PROTOMOTIONS_ASSET_ROOT` to a complete asset tree if needed. |
| SMPL or SMPL-H asset path missing | Assets intentionally excluded from built distributions for licensing | Obtain licensed assets separately and point `PROTOMOTIONS_ASSET_ROOT` to the complete tree. |
| IsaacLab says a USD is not a valid layer | Git LFS pointer file instead of actual asset | In a source checkout, fetch LFS assets; verify files do not contain the Git LFS pointer header. |
| Checkpoints or example motion files are missing | Pretrained models/motions are large Git LFS artifacts, not always present in package-only installs | Use a Git LFS source checkout or provide user-owned checkpoint/motion paths. |

## Config and checkpoint failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Inference cannot find `resolved_configs_inference.pt` | Checkpoint directory lacks inference config sidecar | Regenerate configs with current code or use a checkpoint directory that contains the resolved inference config. |
| Resume ignores new CLI overrides | Resume loads exact saved `resolved_configs.pt` | Start a new experiment name for changed configs, or intentionally create/migrate configs. |
| YAML edit has no effect | YAML is readable sidecar only | Modify experiment Python or use scalar `--overrides`; do not edit resolved YAML as runtime source. |
| PEFT/RLFT cannot load prior | Wrong checkpoint role or legacy submodule path | Load the full prior model checkpoint expected by the PEFT config, not an old `actor.mu` submodule. |

## Simulator/runtime failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| MuJoCo run uses too many envs | MuJoCo is CPU-oriented/single-env for many workflows | Use `--num-envs 1` for quick debug and deployment validation. |
| Newton device allocation fails | Warp device not set, incompatible CUDA stack, or CPU torch env | Use a Newton environment with CUDA torch and verify a tiny CUDA/Warp smoke before running native examples. |
| IsaacLab MJCF conversion hangs or crashes | Kit/Isaac Sim runtime, EULA, or converter dependency issue | Validate IsaacLab workspace, EULA acceptance, and use Kit-free helper tests before real conversion. |
| Cross-sim policy performs poorly | Policy not trained with transfer-oriented domain randomization or robot joint representation differs | Use the model card and domain-randomization recipe; do not assume transfer for SMPL/SMPL-X spherical joints. |

## Motion data and retargeting failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| MotionLib body count mismatch | Motion data was packaged for a different skeleton/robot than the selected config | Verify skeleton format, MJCF body names, and `robot_type` during conversion. |
| Contact labels length mismatch | Contact FPS or downsample factor differs from retargeted motion | Preserve source-contact FPS metadata and downsample both motion and contacts consistently. |
| Retargeted robot motion filtered out | Motion quality filter thresholds or invalid root/joint data | Inspect min height, velocity, DOF velocity, and duration filters; temporarily process a tiny subset with relaxed thresholds. |
| PyRoki imports conflict with ProtoMotions | PyRoki/JAX stack differs from ProtoMotions simulator stack | Use a separate PyRoki environment and pass both Python interpreters to the retargeting pipeline. |

## Deployment failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| ONNX export cannot find resolved configs | Checkpoint directory lacks `resolved_configs_inference.pt` or `resolved_configs.pt` | Export from a full run directory with config sidecars. |
| ONNX runtime reports missing input feed | Deployment assembler does not source a semantic input requested by YAML/ONNX | Inspect the YAML sidecar and update input assembly for all requested semantic keys. |
| Robot travels in the wrong frame | Future reference positions were not aligned to the robot start frame | Align both full-body and anchor reference positions using the heading offset before assembling ONNX inputs. |
| Turning behavior is wrong | Root angular velocity frame is wrong | Use local-frame gyro/qvel directly; only rotate world-frame angular velocity into local frame. |
| Real robot motion is unsafe | Policy, PD targets, blend-in/out, or emergency stop not validated | Validate in MuJoCo first, enforce deployment safety procedures, and require human approval before hardware execution. |
