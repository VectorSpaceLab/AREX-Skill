# FCOS Native Test Selection

## Safe or usually short CPU candidates

- Config loading: validates all YAML files merge into the base config.
- `BoxCoder`, `BoxList`, segmentation/keypoint structures: pure tensor/structure behavior.
- Metric logger and sampler tests: utility behavior not tied to datasets.
- Tiny checkpoint stripping: synthetic checkpoint with optimizer/scheduler/iteration keys.

## Extension-dependent candidates

- NMS, ROIAlign/ROIPool, sigmoid focal loss, deformable conv/pool, detector/backbone construction, and full predictor tests may require `fcos_core._C` and a compatible PyTorch binary.

## Dataset/benchmark candidates

- `train_net.py` and `test_net.py` workflows require actual datasets, weights, and usually GPUs. Treat them as integration or benchmark jobs, not unit tests.

## Maintenance workflow

1. Reproduce import/config issues with `inspect_fcos_components.py`.
2. Run config and structure tests before dataset-heavy tests.
3. If changing FCOS head/loss/postprocess, add or select a tiny tensor-level test where possible.
4. Run full train/eval only after unit-level changes and environment compatibility are verified.
