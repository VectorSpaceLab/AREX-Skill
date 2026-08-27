# BAPPS Training Troubleshooting

## Purpose

Read this when training, fine-tuning, or checkpointing does not work on the first try.

## Common issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for the checkpoint directory | The output directory was never created. | Use the bundled `train_bapps.py` helper, which creates the directory automatically. |
| `ModuleNotFoundError: dominate` or old HTML/visdom errors | The stock `train.py` uses the visualization stack. | Use `scripts/train_bapps.py`; it avoids the old stack entirely. |
| Training is slow on CPU | LPIPS training is heavier than simple comparison. | Keep the smoke default (`--max_steps 1`) for quick checks, or move to CUDA if available. |
| `FROM_SCRATCH` and `TRAIN_TRUNK` feel confusing | The mode flags affect the trunk initialization and whether the trunk may be tuned. | `train_test_metric_scratch.sh` sets both; `train_test_metric_tune.sh` sets only `TRAIN_TRUNK=1`. |
| Checkpoint names do not match the source script | The output path or trial name was changed. | Check `<checkpoints_dir>/<name>/` for `latest_net_.pth` and related files. |
| CUDA was requested but the run stayed on CPU | The environment cannot see a CUDA device. | Leave `USE_GPU=0`, or install a CUDA-capable Torch build in a CUDA-visible environment. |
| The loss does not move much in a smoke run | The step budget is intentionally tiny. | Increase `--max_steps` or `--epochs` once the smoke path is confirmed. |

## Recommended recovery order

1. Create a tiny fixture with `../../scripts/make_tiny_bapps_fixture.py`.
2. Run `scripts/train_bapps.py` with `--max_steps 1`.
3. Inspect `<checkpoints_dir>/<name>/train_log.txt` and the checkpoint files.
4. Only then increase the step budget or switch to the larger BAPPS splits.

## Read next

- `../../references/api-reference.md`
- `../../references/bapps-dataset.md`
- `../../references/troubleshooting.md` for cross-cutting install and backend problems
