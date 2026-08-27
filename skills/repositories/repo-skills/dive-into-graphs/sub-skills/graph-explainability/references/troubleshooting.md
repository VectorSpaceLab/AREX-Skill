# Graph Explainability Troubleshooting

## Model Config Mismatch

- Explanation APIs depend on the base model output shape and task level.
- If `model_config`, `task_level`, or `return_type` disagree with the model, explanation calls will fail or metrics will be meaningless.

## Missing or Wrong Masks

- `control_sparsity` only transforms a 1D mask vector; pass one mask per class or explanation target.
- `ExplanationProcessor` requires edge masks and a model with `MessagePassing` layers.

## Checkpoint Compatibility

- If a checkpoint from an older PyG version fails to load, run it through `compatible_state_dict` first.
- Watch for renamed convolution weight keys when upgrading PyG.

## Dataset or Checkpoint Downloads

- Synthetic datasets and benchmark checkpoints may be fetched externally.
- Use the smoke script for documentation-level checks before requesting a real benchmark run.
