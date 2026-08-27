# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import or weight lookup fails | `--repo-root` is wrong or one of the shipped checkpoint files is missing | Re-run `scripts/inspect_superglue_api.py --repo-root <repo-root>` and confirm `models/weights/superpoint_v1.pth`, `superglue_indoor.pth`, and `superglue_outdoor.pth` are present |
| `Expected 4D input` or tensor shape errors | Image tensors are not grayscale float tensors shaped `1x1xHxW` | Load with `read_image` or `frame2tensor`, and keep the tensor on the same device as the model |
| `torch.stack` fails inside `Matching.forward` | You batched variable-length local features | Use one pair at a time, or pre-pad / normalize feature lengths before stacking |
| All matches are `-1` | Image is blank, too small, or the thresholds are too strict | Lower `keypoint_threshold` first, then lower `match_threshold`; also try a larger resize and the correct indoor/outdoor weights |
| CUDA device mismatch | The model and tensors are on different devices | Move the model and every input tensor to the same CPU or CUDA device |
| `ValueError: "max_keypoints" must be positive or "-1"` | Invalid SuperPoint limit | Use `-1` or a positive integer |
| Poor quality after config edits | Architecture defaults no longer match the shipped checkpoint | Keep `descriptor_dim=256`, `keypoint_encoder`, and `GNN_layers` aligned with the bundled weights |
| Pose recovery returns `None` | Fewer than five usable matches survived | Inspect match density, relax the detector / matcher thresholds, or check the intrinsics |
| Small-resolution warning | Resize choice fell below the recommended range | Stay near or above the 160px lower bound unless you deliberately want a tiny smoke test |
| Geometry helpers complain about shapes | NumPy arrays are not `(N, 2)`, `(3, 3)`, or `(4, 4)` as expected | Check the input array shapes before calling the pose or plotting helpers |

## What is normal

- Empty keypoint lists on blank images are valid.
- `matches0` / `matches1` with `-1` entries are the normal representation for unmatched points.
- The smoke helper is allowed to succeed even when it prints zero matches on a very weak synthetic input.

## Fast checks

1. Run `python scripts/inspect_superglue_api.py --repo-root <repo-root>` to confirm signatures, defaults, and weights.
2. Run `python scripts/run_matching_api_smoke.py --repo-root <repo-root> --device cpu` to verify the basic forward path.
3. If CPU works but CUDA does not, the bug is usually a device-placement issue rather than a model issue.
