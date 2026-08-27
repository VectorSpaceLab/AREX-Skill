# Training troubleshooting

## Common symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Constructor assertion about `models`, `loss_funcs`, `mining_funcs`, `optimizers`, or `lr_schedulers` | A required key is missing or misspelled | Match the trainer schema exactly; the base class validates those dictionaries. |
| `freeze_these` assertion | The frozen name is not one of the allowed model/loss keys | Freeze only names that actually appear in `models` or `loss_funcs`. |
| Trainer steps but nothing appears in logs | The end-of-iteration hook is missing or logging frequency is too low | Attach `HookContainer.end_of_iteration_hook` or lower `log_freq`. |
| Validation never runs | The end-of-epoch hook was not created or the validation split name is wrong | Create the hook with a real dataset dict that contains the split name. |
| Checkpoint files are missing | `save_models` is disabled or the model folder was never created | Enable saving and use a writable folder. |
| `record-keeper` / tensorboard import errors | The logging extra is missing | Install the `with-hooks-cpu` extra or the logging dependencies directly. |
| Distributed wrapper errors on CPU | The wrapper was used without a distributed process group or without the intended backend | Treat distributed training as optional unless you have the required GPU/distributed setup. |
| Loss is zero or the trainer cannot mine tuples | The batch sampler does not provide enough label structure | Use a sampler such as `MPerClassSampler` or reduce the miner strictness. |

## Recovery checklist

1. Confirm the trainer dictionary keys before touching the model code.
2. Run the trainer on a tiny in-memory dataset before using real data.
3. If you want logging or early stopping, create the `HookContainer` first and wire both hooks explicitly.
4. If you want validation metrics, make sure the tester and dataset dict agree on split names.
5. If you are experimenting with distributed wrappers, keep that work separate from ordinary single-process training until the base trainer path is green.

## When to read the script

Run `scripts/smoke_training.py` to confirm a minimal trainer/logging path on toy data before moving to a longer job.
