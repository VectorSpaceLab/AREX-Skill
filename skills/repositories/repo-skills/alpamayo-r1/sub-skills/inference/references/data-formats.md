# Alpamayo R1 inference data formats

## Loader outputs

`load_physical_aiavdataset` returns a dictionary with the following keys.

| Key | Shape / type | Meaning |
| --- | --- | --- |
| `image_frames` | `torch.Tensor` of shape `(N_cameras, num_frames, 3, H, W)` | Multi-camera image clip in channel-first format. The inference path flattens this to 4D before prompt construction. |
| `camera_indices` | `torch.Tensor` of shape `(N_cameras,)` | Stable camera ordering index. The loader sorts by this index before returning the stack. |
| `ego_history_xyz` | `torch.Tensor` of shape `(1, 1, 16, 3)` by default | Historical ego positions, already transformed into the local frame at `t0`. The final history point is the origin. |
| `ego_history_rot` | `torch.Tensor` of shape `(1, 1, 16, 3, 3)` by default | Historical ego rotation matrices in the same local frame. The final rotation is the local identity pose. |
| `ego_future_xyz` | `torch.Tensor` of shape `(1, 1, 64, 3)` by default | Ground-truth future ego positions in the local frame. |
| `ego_future_rot` | `torch.Tensor` of shape `(1, 1, 64, 3, 3)` by default | Ground-truth future ego rotation matrices in the local frame. |
| `relative_timestamps` | `torch.Tensor` of shape `(N_cameras, num_frames)` | Frame timestamps in seconds relative to the earliest stacked frame. |
| `absolute_timestamps` | `torch.Tensor` of shape `(N_cameras, num_frames)` | Absolute timestamps in microseconds. |
| `clip_id` | `str` | Clip identifier used to fetch the sample. |
| `t0_us` | `int` | Timestamp used for the history/future split. |

## Stable camera order

The loader maps camera feature names to stable indices before sorting the stack. The default inference route uses four cameras and returns them in index order, not in arbitrary feature-list order.

## Prompt-side format

`helper.create_message(data["image_frames"].flatten(0, 1))` expects a 4D tensor of frames with shape `(N, C, H, W)`.

The resulting chat template has three messages:

1. System: `You are a driving assistant that generates safe and accurate actions.`
2. User: stacked image blocks followed by the trajectory placeholder text
3. Assistant: `<|cot_start|>` seed so the model can continue the reasoning trace

The trajectory placeholder block uses 48 repeated `<|traj_history|>` tokens between `<|traj_history_start|>` and `<|traj_history_end|>`.

## Model outputs

| Output | Shape / type | Meaning |
| --- | --- | --- |
| `pred_xyz` | `torch.Tensor` with shape `[B, num_traj_sets, num_traj_samples, 64, 3]` | Predicted future ego positions in the local frame at `t0`. |
| `pred_rot` | `torch.Tensor` with shape `[B, num_traj_sets, num_traj_samples, 64, 3, 3]` | Predicted future ego rotation matrices. |
| `extra["cot"]` | NumPy array of strings | Chain-of-Causation text per sampled trajectory. |
| `extra["meta_action"]` | NumPy array of strings | Optional intermediate reasoning / action text. |
| `extra["answer"]` | NumPy array of strings | Optional answer text span if emitted by the model. |

The default action-space decoder is a 64-waypoint unicycle accel/curvature trajectory at 10 Hz. It reconstructs `x`, `y`, and orientation from the sampled action and keeps `z` fixed to the last history height.

## Ground-truth comparison

The repository smoke example computes minADE on the `xy` plane only:

```python
gt_xy = data["ego_future_xyz"].cpu()[0, 0, :, :2].T.numpy()
pred_xy = pred_xyz.cpu().numpy()[0, 0, :, :, :2].transpose(0, 2, 1)
diff = np.linalg.norm(pred_xy - gt_xy[None, ...], axis=1).mean(-1)
min_ade = diff.min()
```

Use the same comparison unless you intentionally want a different metric.
