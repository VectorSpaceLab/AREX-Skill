# Evaluation workflows

## End-to-end flow

The repo's training/evaluation wrapper is `train_test.sh`:

```bash
bash train.sh <run-name> <gpu-ids>
bash test.sh <gpu-ids-for-test>
```

`test.sh` first runs inference and then evaluates every configured testset:

1. `CUDA_VISIBLE_DEVICES=<ids> python inference.py --pred_root <pred_root> --resolution <resolution>`
2. `python eval_existingOnes.py --pred_root <pred_root> --data_lst <testset> --metrics all`

The default prediction and result directories are relative to the current working directory, so use explicit paths if you are not launching from the repo root.

## `test.sh`

Important arguments:

- `devices` defaults to `0`
- `pred_root` defaults to `e_preds`
- `resolutions` defaults to `config.size`

Behavior notes:

- Multiple resolutions can be passed as a whitespace-separated list.
- The script loops over `config.testsets` and writes one evaluation log per testset under `e_logs/`.
- The inference stage writes predictions into the `pred_root` tree using checkpoint- and resolution-specific subfolders.

## `eval_existingOnes.py`

CLI arguments:

| Argument | Default | Meaning |
|---|---|---|
| `--gt_root` | `os.path.join(config.data_root_dir, config.task)` | Ground-truth root for the current task. |
| `--pred_root` | `./e_preds` | Prediction root containing one folder per checkpoint/model. |
| `--data_lst` | `config.testsets.replace(',', '+')` | `+`-separated list of testsets. |
| `--save_dir` | `e_results` | Directory that receives the pretty-table text files. |
| `--metrics` | `S+MAE` | Metric subset for the evaluator. |

How it maps files:

- Ground truth is read from `<gt_root>/<dataset>/gt/*`.
- Predictions are expected under `<pred_root>/<model>/<dataset>/`.
- The script maps each GT path to a prediction path by replacing the GT root and `/gt/` segment.
- It sorts candidate model folders by the `epoch_<N>` suffix when possible.

Special notes:

- `--metrics all` expands to the full evaluator set.
- HCE is only meaningful for DIS-style evaluation; the source code omits it outside DIS5K when building the `all` list.
- Each dataset produces a table in `e_results/<dataset>_eval.txt`.

## `gen_best_ep.py`

This helper reads the evaluation tables and collects the best checkpoint lines into a summary file.

What it assumes:

- You run it from a directory that already contains `e_results/*_eval.txt`.
- The tables follow the standard layout emitted by `eval_existingOnes.py`.
- `config.task` describes the current task family.

What it uses:

- `sm` and `wfm` for the main selection signal.
- `hce` only when the task is `DIS5K`.
- The `e_results/eval-<task>_best_on_<metric>.txt` output naming convention.

## Practical patterns

- For one-off evaluation of existing predictions, call `eval_existingOnes.py` directly.
- For a full train→eval run, use `train_test.sh`.
- For checkpoint ranking after a run, use `gen_best_ep.py` after the `e_results` tables exist.
