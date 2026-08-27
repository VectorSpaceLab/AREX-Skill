# Registration Troubleshooting

## Pair fields are missing

**Symptoms**

- Model or loss code expects `pair_ind`, `size_pair_ind`, source/target positions, or fragment identifiers.
- Collation fails for pair batches.

**Recovery**

Check whether the selected data config is patch, fragment, siamese, dense,
partial, or sparse. Pair datasets are not interchangeable with ordinary
segmentation datasets. Validate the dataset root and use a model group designed
for the same pair/fragment format.

## Sparse registration backend missing

**Symptoms**

- `MinkowskiEngine` or `torchsparse` import errors.
- Sparse convolution model construction fails.
- CUDA extension symbol errors.

**Recovery**

Switch to a dense/partial registration config only if it matches the user's
model goal. Otherwise install the sparse backend for the target PyTorch/CUDA
stack and run the root environment probe with `--require-sparse-backend` before
registration-specific verification.

## Feature or descriptor files missing

**Symptoms**

- Descriptor matcher cannot find feature files.
- Evaluation reports zero pairs or cannot associate source/target fragments.

**Recovery**

Identify the feature directory and naming convention produced by the checkpoint
or descriptor extractor. Confirm the evaluation script expects the same split,
fragment ids, descriptor dimension, and coordinate frame.

## Ground-truth log or transform mismatch

**Symptoms**

- Registration recall is zero despite non-empty descriptors.
- Transform parsing fails.
- Fragment pair ids do not match ground-truth entries.

**Recovery**

Verify the benchmark version and split. Do not mix KITTI, 3DMatch, ETH, TUM,
KAIST, or Planetary ground-truth formats. Check units and coordinate frames
before tuning thresholds.

## Open3D visualization or FPFH failures

**Symptoms**

- `open3d` import/display errors.
- Headless environment cannot open a visualization window.
- FPFH baseline consumes excessive runtime.

**Recovery**

Treat Open3D workflows as optional. Use headless/offscreen settings only if the
user specifically needs visualization. For model troubleshooting, prefer the
FPS utility smoke or a Hydra config smoke before classical FPFH evaluation.

## FPS utility mismatch

**Symptoms**

- `fps_sampling` returns unexpected correspondence indices.
- CPU and CUDA farthest-point sampling behavior differs.

**Recovery**

Run the bundled CPU smoke. If CUDA-specific FPS is required, verify a CUDA build
of PyTorch/PyG/torch-cluster and run a CUDA-specific test; the CPU utility pass
is not evidence for CUDA kernel behavior.
