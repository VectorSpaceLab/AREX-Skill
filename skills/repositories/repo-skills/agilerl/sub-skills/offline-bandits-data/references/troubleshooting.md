# Offline And Bandit Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| HDF5 key error | Dataset keys differ from examples | Print keys and map fields explicitly. |
| Replay add/sample shape error | Missing vectorized dimension or wrong TensorDict batch size | Use `transition.unsqueeze(0)` and `transition.batch_size = [1]` for single rows. |
| Offline training uses simulator unexpectedly | Confusing evaluation env with data source | Use env for spaces/evaluation, but fill replay from static data. |
| Minari call downloads data unexpectedly | Remote dataset requested | Ask before network access or require a local dataset path. |
| Bandit target error | Targets are not encoded as expected arms | Normalize labels and confirm `env.arms`. |
| UCI example hangs/fails | `ucimlrepo` or network unavailable | Use local/synthetic features for smoke checks. |
| W&B login error | Logging enabled in training helper | Disable W&B for local/offline smoke tests. |

## Schema Checklist

1. Check field names.
2. Check all field lengths agree.
3. Check observation/action shapes match spaces.
4. Check terminal flags are boolean-compatible.
5. Check dtypes can convert to Torch tensors.
6. Sample one replay batch before training.
