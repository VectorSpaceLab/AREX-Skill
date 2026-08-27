# OpenPCDet Cross-cutting Troubleshooting

## Runtime and import failures

- `ModuleNotFoundError: pcdet`: run from a checkout with package on `PYTHONPATH`, or install OpenPCDet into the selected environment. Prefer checking with `scripts/inspect_openpcdet_runtime.py`.
- `ImportError` for `pcdet.ops.*_cuda`: the editable/native build did not compile or the runtime linker cannot see CUDA/PyTorch libraries. Rebuild after verifying PyTorch CUDA version, CUDA toolkit headers, `nvcc`, `thrust`, `cub`, `spconv` suffix, and `LD_LIBRARY_PATH`/system linker visibility.
- `No module named spconv` or sparse-convolution errors: install the spconv wheel that matches the PyTorch CUDA runtime (`spconv-cuXXX`) and verify `cumm` imports.
- `pcdet.datasets` fails in Argo2/kornia TorchScript code: pin kornia to a version compatible with the active PyTorch; `kornia==0.6.12` was verified during construction with PyTorch CUDA 12.4.
- Demo visualization import fails: install either Open3D or Mayavi, or adapt demo inference to skip visualization and save predictions.

## Config and checkpoint failures

- `NotFoundKey` from `--set`: the override key must already exist in the loaded YAML tree. Use `scripts/summarize_openpcdet_config.py` before adding overrides.
- Type mismatch from `cfg_from_list`: OpenPCDet converts overrides to the type of the original value. Quote lists/strings carefully and avoid changing a scalar into a mapping unless the existing field is already an EasyDict.
- Checkpoint shape/class mismatches: verify `CLASS_NAMES`, detector `MODEL.NAME`, voxel/point range, and model family match the checkpoint's training config.
- Unexpected output directory: train/test derive the output path from config group, config file stem, and `--extra_tag`.

## Dataset failures

- Missing info files or database sampler files: run the dataset info-generation entrypoint for the dataset and verify `DATA_CONFIG.INFO_PATH`, `DB_INFO_PATH`, and `DB_DATA_PATH` names.
- Empty dataloader: check split files, `DATA_CONFIG.DATA_SPLIT`, dataset root, class names, and filtered point-cloud range.
- KITTI failures often come from missing `ImageSets`, calibration, labels, or generated `kitti_infos_*.pkl` files.
- NuScenes/Lyft failures often come from wrong version folder names, missing sweeps, or missing official devkit metadata.
- Waymo failures often come from unprocessed sequence data, missing `waymo_infos_*.pkl`, or excessive worker/shared-memory settings.
- CustomDataset failures usually trace to malformed `custom_infos_*.pkl`, wrong point feature dimension, class-name mismatch, or missing `points`/`ImageSets` folders.

## Training/evaluation failures

- Batch-size assertion: when distributed, `--batch_size` is total batch size and must be divisible by GPU count; the script divides it per GPU.
- NCCL or distributed initialization hangs: verify `CUDA_VISIBLE_DEVICES`, `--launcher`, `--tcp_port`, rank variables, and that each process sees the expected GPU count.
- Out-of-memory: reduce batch size, voxel count, point range, image branch resolution, number of sweeps, or dataloader workers; turn off visualization/debug outputs.
- Repeated evaluation appears stuck: `--eval_all`/repeat evaluation waits for new checkpoints up to `--max_waiting_mins` after the first eval.

## Safe debugging order

1. Run `scripts/inspect_openpcdet_runtime.py --require-cuda-ops`.
2. Run `scripts/summarize_openpcdet_config.py --cfg <config.yaml>`.
3. For dataset jobs, run `sub-skills/data-preparation/scripts/check_openpcdet_dataset_layout.py` with the dataset root.
4. Use `scripts/plan_openpcdet_command.py` to print the intended command.
5. Only then execute train/test/demo or dataset conversion.
