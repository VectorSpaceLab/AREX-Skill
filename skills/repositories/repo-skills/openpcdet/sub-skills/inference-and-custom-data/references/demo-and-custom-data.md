# Demo and Custom Data Workflows

## DemoDataset behavior

The demo workflow constructs a lightweight dataset around either one point-cloud file or all files in a directory.

- `.bin`: loaded with `numpy.fromfile(dtype=float32).reshape(-1, 4)`.
- `.npy`: loaded with `numpy.load` and passed through as an array.
- Each sample receives a numeric `frame_id` and then flows through `DatasetTemplate.prepare_data` using the YAML `DATA_CONFIG`.
- Predictions are visualized with Open3D when available, otherwise Mayavi is attempted.

From the generated skill root, validate files before demo:

```bash
python sub-skills/inference-and-custom-data/scripts/check_point_cloud_array.py <sample.bin> --feature-dim 4
```

## Config/checkpoint/data pairing

A valid demo needs:

- A model config compatible with the checkpoint.
- `CLASS_NAMES` matching the checkpoint's classes.
- `POINT_FEATURE_ENCODING` matching the point-cloud feature dimension.
- A point cloud range and voxel size appropriate for the data coordinates.
- CUDA native ops and spconv importable for the selected model.

If a checkpoint comes from KITTI and point clouds are in another coordinate frame, predictions can be meaningless even when the command runs.

## Non-visual inference adaptation

For headless environments, adapt the demo loop to:

1. Build `DemoDataset` from the config and point files.
2. Build the network with `pcdet.models.build_network`.
3. Load checkpoint to CPU first, then move model to CUDA.
4. For each sample, collate, call `pcdet.models.load_data_to_gpu`, and run `model.forward` under `torch.no_grad()`.
5. Serialize `pred_boxes`, `pred_scores`, and `pred_labels` instead of calling visualization utilities.

Keep visualization optional; do not install GUI packages for batch prediction unless the user asks.

## CustomDataset route

CustomDataset is for training/evaluation on a custom dataset, not just one-off demo files. It requires:

- A custom dataset config with `DATASET: CustomDataset`.
- Class names that match labels.
- A point-cloud feature schema in `POINT_FEATURE_ENCODING`.
- Generated `custom_infos_*.pkl` files.
- Ground-truth database products if database sampling is enabled.

Use `../data-preparation/SKILL.md` to prepare the info/database products. Use this inference sub-skill only for point-file sanity, demo command construction, and adapting the demo loop.

## Visualization troubleshooting

- If neither Open3D nor Mayavi imports, demo will fail before parsing arguments. Install one visualization backend or use a non-visual adaptation.
- On headless servers, prefer non-visual output or configure an offscreen renderer; interactive `mlab.show` can block.
- Large point clouds can make visualization appear frozen; first validate array shape and run a small sample.
