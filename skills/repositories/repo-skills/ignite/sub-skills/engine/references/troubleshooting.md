# Engine troubleshooting

## Symptom -> likely cause -> fix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Arguments max_iters and max_epochs are mutually exclusive` | Both run limits were supplied. | Choose one limit and pass only that argument. |
| `epoch_length should be provided if data is None` | The engine has no iterable and no fixed length. | Pass `epoch_length` or provide an iterable `data` object. |
| `Input data has zero size` | The iterable is empty or has `len(...) == 0`. | Check the dataset, dataloader, or synthetic fixture. |
| Resume run errors about `epoch_length` or `max_epochs` / `max_iters` mismatch | The restored engine state does not match the new call. | Keep the saved state and new run arguments consistent. |
| `amp_mode cannot be used with mps device` | MPS and AMP were combined. | Disable AMP or use a CUDA path instead. |
| `amp_mode cannot be used with xla device` | TPU/XLA and AMP were combined. | Use the TPU helper without AMP. |
| `scaler argument is ... but amp_mode is ...` | `scaler` and `amp_mode` do not match. | Use `amp_mode="amp"` when you pass a GradScaler. |
| `Please install apex...` / `Please install PyTorch XLA...` | Optional backend package is missing. | Install the matching accelerator package or choose the plain CPU/CUDA path. |
| Trainer outputs look different after resume | RNG state or dataflow was not preserved. | Use deterministic helpers, fixed seeds, and a stable `epoch_length`. |

## Debugging checklist

1. Confirm the model, optimizer, and loss function run on their own without Ignite.
2. Confirm `prepare_batch` returns the same structure that the loss expects.
3. Confirm `output_transform` matches what attached metrics expect.
4. Confirm the loop limit (`max_epochs`, `max_iters`, or `epoch_length`) matches the way you want to resume.
5. If you are using optional accelerator modes, verify the backend package is actually importable before debugging the trainer itself.
