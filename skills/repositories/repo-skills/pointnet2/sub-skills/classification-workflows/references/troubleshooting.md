# Classification troubleshooting

Use these checks when ModelNet40 training, multi-GPU training, or checkpoint evaluation fails.

## Missing HDF5 folder unexpectedly starts a download

**Symptoms**

- Importing or running classification code tries to run `wget` for `modelnet40_ply_hdf5_2048.zip`.
- Offline or CI runs hang or fail before argument validation.

**Likely cause**

`modelnet_h5_dataset.py` contains top-level code that creates `data/` and downloads/unzips the HDF5 dataset when `data/modelnet40_ply_hdf5_2048` is missing.

**Recovery**

- Do not import the source HDF5 loader for layout validation.
- Validate offline with:

  ```bash
  python sub-skills/classification-workflows/scripts/validate_modelnet_layout.py --mode h5 --repo-root .
  ```

- Place the HDF5 folder manually at `data/modelnet40_ply_hdf5_2048/` or provide a custom dataset root to the validator/smoke script.

## Missing split files or sample directories

**Symptoms**

- `IOError` / `FileNotFoundError` for `train_files.txt`, `test_files.txt`, `modelnet40_train.txt`, or a class sample file.
- Normal-resampled runs fail on a path like `data/modelnet40_normal_resampled/<class>/<shape_id>.txt`.

**Likely cause**

The selected dataset mode does not match the available folder, or a split file lists samples that were not extracted.

**Recovery**

- HDF5 mode needs `shape_names.txt`, `train_files.txt`, and `test_files.txt` in `data/modelnet40_ply_hdf5_2048/`.
- Normal mode needs `shape_names.txt`, `modelnet40_train.txt`, `modelnet40_test.txt`, and per-class sample directories under `data/modelnet40_normal_resampled/`.
- Run the validator in the same mode as the command you plan to run:

  ```bash
  python sub-skills/classification-workflows/scripts/validate_modelnet_layout.py --mode h5 --repo-root . --num-point 1024
  python sub-skills/classification-workflows/scripts/validate_modelnet_layout.py --mode normal --repo-root . --num-point 5000
  ```

## `--num_point` assertion or too-short sample files

**Symptoms**

- `AssertionError` soon after script startup.
- Loader smoke reports files with fewer rows than the requested point count.
- HDF5 smoke reports `data` has fewer than the requested number of points.

**Likely cause**

- HDF5 mode asserts `NUM_POINT <= 2048`.
- Normal-resampled mode asserts `NUM_POINT <= 10000`.
- Custom or tiny fixture files may have fewer rows than the source assertions allow.

**Recovery**

- Use `--num_point 1024` for stock HDF5 ModelNet40 unless deliberately testing another value.
- Use small values such as `16` or `32` for tiny fixture smoke tests.
- For normal-resampled experiments, the README cites `5000` points, but the actual files must contain at least the chosen number of rows.

## `--normal` produces a channel-shape mismatch

**Symptoms**

- TensorFlow feed error mentioning a placeholder shaped like `(batch, num_point, 3)` but data shaped like `(batch, num_point, 6)`.
- A normal-resampled run reaches graph/session construction and fails at the first batch.

**Likely cause**

With `--normal`, `ModelNetDataset(..., normal_channel=True)` returns XYZ+normal features with 6 channels. The stock classification model files observed here define `placeholder_inputs()` with three input channels.

**Recovery**

- For default stock classification, use HDF5 mode without `--normal`.
- For true XYZ+normal experiments, adapt the selected model's placeholder and first layer to accept six channels before running.
- If the user only needs a CPU baseline or data smoke, choose `pointnet_cls_basic` without `--normal`.

## PointNet++ custom-op dependency mismatch

**Symptoms**

- Import errors for TensorFlow custom op libraries such as sampling, grouping, or interpolation `.so` files.
- `pointnet2_cls_ssg` or `pointnet2_cls_msg` fails before or during graph construction, while `pointnet_cls_basic` can build.

**Likely cause**

PointNet++ set-abstraction layers depend on the repository's shared custom TensorFlow operators. The CPU baseline `pointnet_cls_basic` uses only standard TensorFlow helper layers and does not require those PointNet++ custom ops.

**Recovery**

- If the user needs PointNet++ training/evaluation, route to the sibling `model-apis-and-custom-ops` sub-skill to inspect or compile the custom-op backend.
- If the user accepts a CPU baseline or smoke path, generate a command with `--model pointnet_cls_basic`.
- Do not treat a successful TensorFlow import as proof that PointNet++ custom ops are ready.

## Checkpoint restore fails

**Symptoms**

- `NotFoundError`, `DataLossError`, or variable-shape mismatch during `saver.restore(sess, MODEL_PATH)`.
- Evaluation starts with the wrong model flag and fails to restore variables.

**Likely cause**

- `--model_path` points to a directory, `.meta` file, stale checkpoint, or nonexistent prefix.
- The evaluation `--model` does not match the architecture used during training.
- The checkpoint was produced with a normal-channel or otherwise modified model, but evaluation uses the stock three-channel model.

**Recovery**

- Use the TensorFlow checkpoint prefix, for example `log_cls_ssg/model.ckpt`, not just `log_cls_ssg/`.
- Keep `--model` consistent between training and evaluation.
- Keep `--num_point` and `--normal` consistent with the model/checkpoint assumptions.
- Use the command builder to make the checkpoint path explicit:

  ```bash
  python sub-skills/classification-workflows/scripts/build_classification_command.py --action evaluate --model pointnet2_cls_ssg --model-path log_cls_ssg/model.ckpt --num-votes 1
  ```

## Voting is slow or misused

**Symptoms**

- Evaluation is much slower than expected.
- User sets `--num_votes 0` or expects voting to affect training.

**Likely cause**

`evaluate.py` repeats each batch once per vote, rotating the point cloud by a different angle and summing class scores. Voting is evaluation-only and cost scales roughly linearly with `--num_votes`.

**Recovery**

- Use `--num_votes 1` for smoke or checkpoint sanity checks.
- Use larger values such as `12` only for a full evaluation.
- The command builder rejects values below 1.

## Multi-GPU batch or device failure

**Symptoms**

- `AssertionError` from `BATCH_SIZE % NUM_GPUS == 0`.
- TensorFlow cannot place `/gpu:0`, `/gpu:1`, etc.
- Unexpected GPU ids are used.

**Likely cause**

`train_multi_gpu.py` splits the global batch evenly across visible GPU tower ids. Physical ids must be exposed through `CUDA_VISIBLE_DEVICES` before the script starts.

**Recovery**

- Pick a global `--batch_size` divisible by `--num_gpus`.
- Use `CUDA_VISIBLE_DEVICES=0,1` style prefixes when selecting physical devices.
- Prefer single-device training or the CPU baseline when no compatible GPU/backend exists.

## Model import or flag-name failure

**Symptoms**

- `ImportError` for a model name.
- User passes `models/pointnet2_cls_ssg.py` instead of `pointnet2_cls_ssg`.
- CLI rejects dashed flag names.

**Likely cause**

The legacy scripts import the model with `importlib.import_module(FLAGS.model)` after adding `models/` to `sys.path`; flags use underscores such as `--log_dir` and `--num_point`.

**Recovery**

- Use module names: `pointnet2_cls_ssg`, `pointnet2_cls_msg`, or `pointnet_cls_basic`.
- Use the bundled command builder; it emits source-compatible underscore flags.
