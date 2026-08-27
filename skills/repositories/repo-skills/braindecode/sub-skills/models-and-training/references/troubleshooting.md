# Models and training troubleshooting

- **`n_times`/`n_chans` or final-layer shape error**: inspect the data shape and
  sampling rate, pass explicit signal parameters, and run one forward before
  `fit`. Do not copy constructor values from a different model.
- **Module name cannot be resolved**: check the model registry spelling and
  whether the selected model is classification-compatible. Instantiate the
  class directly when registry resolution is insufficient.
- **Skorch target or dataset error**: inspect one dataset item and target dtype;
  use `y=None` only when the dataset supplies targets in the expected form.
  Check `classes`, regression output dimensions, and split indices.
- **Cropped loss/aggregation mismatch**: compare model output rank, crop count,
  target rank, `cropped`, `criterion`, and `aggregate_predictions`. Validate
  trialwise predictions on a tiny fixture before reporting scores.
- **Training hangs or out-of-memory**: use CPU, a smaller model/batch/window,
  `n_jobs=1`, and a bounded epoch count; CUDA availability does not guarantee
  allocatable memory.
- **Checkpoint load reports keys**: expected missing keys are usually a new
  head; unexpected keys or missing backbone keys indicate wrong architecture,
  channel configuration, or checkpoint format. Stop and resolve the contract.
- **Pretrained/Hub import failure**: install only the selected optional extra,
  verify repository ID, network/token/cache permissions, and fall back to a
  local randomly initialized smoke model when testing API wiring.
