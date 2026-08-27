# Deployment Troubleshooting

## Server errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `415 Unsupported Media Type` | MsgPack server received JSON or missing `application/msgpack`. | Use the MsgPack client/payload validator and set the correct content type. |
| HTTP 500 with action endpoint | Checkpoint/model load or payload schema failed. | Check server logs, validate checkpoint layout, validate payload keys/shapes, and confirm CUDA. |
| `Action un-norm key ... not found` | Client `unnorm_key` not present in checkpoint stats. | Inspect checkpoint statistics and use the dataset key from training. |
| `load_in_8bit` and `load_in_4bit` both true | Mutually exclusive quantization flags. | Choose at most one quantization mode. |
| Empty/invalid actions from server | Model flags do not match checkpoint or wrong robot constants. | Verify `num_images_in_input`, `use_proprio`, `use_pro_version`, and platform/action dimensions. |

## Client errors

- If fake client cannot connect, normalize the server URL and confirm port,
  firewall, and that `/act` is reachable.
- If payload validation fails, fix image shape/dtype or state dimension before
  hitting the server.
- If real client ROS imports fail, run inside the robot's ROS environment and
  install `cv_bridge`, message packages, and sensor dependencies there.

## Real robot hazards

- Treat `unnorm_key` mismatch, action dimension mismatch, and stale checkpoints
  as safety blockers.
- Never bypass operator prompts or manual stop logic for convenience.
- If the robot base is enabled, verify base velocity scaling separately from arm
  joint commands.
