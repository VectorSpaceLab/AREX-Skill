# Training troubleshooting

- **v2 import cannot load a custom `.so`:** stop before dataset allocation and
  complete the custom-op gate; v1 success does not validate v2.
- **checkpoint restore reports missing or mismatched variables:** compare model
  id, TensorFlow version, point/channel configuration, and checkpoint prefix.
  Never force partial restoration without reviewing every omitted variable.
- **`cPickle` or Python-3 division errors:** apply the documented compatibility
  import and convert batch-count divisions to explicit integers in a recorded
  port.
- **dataset file missing or object stream ends early:** validate the generated
  pickle count/schema; regenerate a staging file rather than training on a
  truncated artifact.
- **out of memory:** reduce batch size first, then point count; record the
  changed experiment configuration because it affects comparability.
- **GPU requested but operations are placed on CPU:** inspect TensorFlow device
  logs and CUDA visibility. `allow_soft_placement=True` can hide a missing GPU.
- **loss is NaN:** check empty segmentation masks, invalid box residuals,
  learning rate, and data corruption before changing the loss implementation.
