# Deployment and robot troubleshooting

## Export failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `resolved_configs_inference.pt` missing | Checkpoint directory incomplete | Use a full run directory or regenerate inference configs. |
| Export cannot find `mimic` control config | Checkpoint is not a mimic/tracker policy | Use a compatible tracker checkpoint or a different export path. |
| ONNX validation differs from PyTorch | Unsupported op, shape mismatch, or input semantic mismatch | Inspect YAML sidecar, verify actor input keys, and compare all required inputs. |

## Deployment input failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing ONNX feed | Deployment assembler does not cover an input semantic key | Map every YAML input name to sensor/reference data before running ONNX. |
| Large position offsets | Future positions or reference anchor not aligned into robot frame | Apply heading/reference alignment to body positions and anchor positions. |
| Wrong turning behavior | Local/world angular velocity confused | Use local gyro/free-joint angular velocity directly; rotate only world-frame `cvel` into local. |
| Quaternion mismatch | MuJoCo `wxyz` passed as ProtoMotions `xyzw` | Convert at data-source boundary. |
| Bad body index | Forgot MuJoCo world-body offset | Use `body_id + 1` for MuJoCo body arrays. |

## MuJoCo validation failures

- If MJCF load fails, check asset root, mesh references, and whether the runner patches sensors/ground as expected.
- If rollout diverges quickly, compare PD stiffness/damping, timestep, decimation, acceleration clamp, EMA filter, and heading alignment with YAML metadata.
- If cached motion behaves differently than raw `.motion`, inspect FPS resampling and cache freshness.

## Custom robot failures

- Unknown robot name: factory registration missing.
- Body mapping errors: semantic foot/hand/head/torso names do not match MJCF bodies.
- Bad default posture: root height, joint limits, or PD gains unsuitable.
- IsaacLab conversion errors: Kit runtime/EULA/dependencies or MJCF-to-USD conversion edge case.
- Cross-simulator mismatch: friction, joints, and quaternion conventions differ; validate one backend at a time.

## Real-robot failures

Stop immediately if the robot behaves unexpectedly. Validate in MuJoCo, confirm sensor frame conventions, check ONNX YAML metadata, enforce acceleration/EMA filtering, and require a human operator with emergency-stop control.
