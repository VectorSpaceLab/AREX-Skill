# Forecasting Workflows

This reference explains how to construct and adapt TimeMixer forecasting commands. The bundled command builder prints commands only; it never starts training.

## Minimal environment and data precheck

1. Work from a TimeMixer repository root that contains `run.py` and the package modules.
2. Install the repository requirements before executing a generated command. If using Python 3.8, the project notes that the `sktime` requirement may need to be pinned to `0.29.1`.
3. Place external benchmark data or custom data under a relative data directory of your choice. Do not download datasets or launch full benchmark runs unless the user approves the cost.
4. For custom CSV, ECL/Traffic/Weather-style commands, and target-column questions, route raw schema checks to `data-preparation` before training.

## Build a benchmark command safely

Use the bundled command builder from this sub-skill. Resolve `scripts/build_timemixer_command.py` relative to this `forecasting-experiments` directory. Example invocations:

```bash
python scripts/build_timemixer_command.py \
  --preset weather \
  --pred-len 336 \
  --train-epochs 1 \
  --batch-size 8 \
  --no-use-gpu
```

```bash
python scripts/build_timemixer_command.py \
  --preset pems03 \
  --root-path ./dataset/PEMS/ \
  --data-path PEMS03.npz \
  --dry-run-json
```

The first command prints a CPU-fallback `run.py` command with an empty `CUDA_VISIBLE_DEVICES` prefix. The second prints structured JSON including the environment prefix, CLI argv, and warnings.

## Adapt a preset to custom data

For a multivariate custom CSV with 12 value channels and a target column named `load`:

```bash
python scripts/build_timemixer_command.py \
  --preset ecl \
  --root-path ./dataset/my_power/ \
  --data-path power.csv \
  --model-id my_power_96_336 \
  --target load \
  --enc-in 12 \
  --dec-in 12 \
  --c-out 12 \
  --pred-len 336 \
  --train-epochs 2 \
  --batch-size 4 \
  --no-use-gpu
```

For univariate target-only forecasting, also pass `--features S --enc-in 1 --dec-in 1 --c-out 1`. For multivariate-to-univariate forecasting, pass `--features MS` only after checking the current forecast path: the custom loader moves the target to the final value column, but the inspected long-term non-AMP training path does not slice MS outputs as consistently as the AMP branch. Prefer `features=M` or `features=S` for routine commands unless a tiny approved run verifies the MS shape contract.

## Generic custom long-term command

When no preset fits, provide all required runtime fields explicitly:

```bash
python scripts/build_timemixer_command.py \
  --task-name long_term_forecast \
  --data custom \
  --root-path ./dataset/custom/ \
  --data-path series.csv \
  --model-id custom_96_192 \
  --features M \
  --target OT \
  --enc-in 5 \
  --dec-in 5 \
  --c-out 5 \
  --seq-len 96 \
  --pred-len 192 \
  --label-len 0 \
  --train-epochs 3 \
  --batch-size 8 \
  --learning-rate 0.001 \
  --no-use-gpu
```

The generated command includes `--task_name`, `--is_training`, `--model_id`, `--model`, and `--data` because these are required by the CLI even though the parser also defines defaults.

## Training and test workflow

A training command (`--is_training 1`) performs this sequence for each `itr` value:

1. Build a setting name from task, model id, comment, model, data flag, sequence/prediction lengths, model dimensions, embedding/distillation flags, description, and iteration index.
2. Train with Adam, OneCycleLR when `lradj=TST`, early stopping, and validation loss.
3. Save the best checkpoint at `checkpoints/<setting>/checkpoint.pth` or under `--checkpoints` during training.
4. Immediately run the experiment's `test()` method after training.

A test-only command (`--is_training 0`) rebuilds the same setting name and calls `test(setting, test=1)`. Forecast test-only loading is hardcoded to `./checkpoints/<setting>/checkpoint.pth`, so a command that trained with a custom `--checkpoints` directory may need the checkpoint copied or the code patched before test-only mode can find it.

## Output locations

| Workflow | Outputs |
| --- | --- |
| Long-term forecasting, including ETT/ECL/Traffic/Weather/Solar/PEMS | Best model checkpoint under `checkpoints/<setting>/checkpoint.pth` during default training; printed `mse` and `mae`; periodic forecast plots under `test_results/<setting>/`. |
| PEMS long-term forecasting | Same as long-term, but validation/test metrics are computed after inverse transform and validation loss tracks MAE. |
| M4 short-term forecasting | Checkpoint under `checkpoints/<setting>/checkpoint.pth`; visual `.pdf` and `.csv` examples under `test_results/<setting>/`; seasonal forecast file under `m4_results/TimeMixer/<Season>_forecast.csv`. |
| `results/` directory | It is an ignored/generated convention in the repository, but the inspected forecasting experiment modules primarily print metrics and use `test_results/`, `checkpoints/`, and `m4_results/` rather than saving standard arrays under `results/`. |

## M4 full evaluation workflow

For M4, each seasonal run writes one forecast CSV. Averaged M4 metrics are printed only when all of these files exist for the same model output directory:

- `Yearly_forecast.csv`
- `Quarterly_forecast.csv`
- `Monthly_forecast.csv`
- `Weekly_forecast.csv`
- `Daily_forecast.csv`
- `Hourly_forecast.csv`

If fewer than six files are present, the test output states that averaged indices can be calculated after all six tasks are finished. The summary uses the M4 root data directory and expects the Naive2 submission file required by the M4 evaluator.

## GPU and CPU workflow

- The CLI defaults to `use_gpu=True`, then changes it to false when `torch.cuda.is_available()` is false.
- Because `--use_gpu` is parsed with `type=bool`, passing `--use_gpu False` to `run.py` is not a reliable way to force CPU. The bundled builder implements `--no-use-gpu` by prefixing the printed command with `CUDA_VISIBLE_DEVICES=''`.
- Use smaller `batch_size`, fewer workers, and fewer epochs for CPU/debug commands. Such commands are not comparable to published benchmark settings.
- Multi-GPU requires `--use_multi_gpu --devices <ids>` in raw `run.py`; the bundled builder keeps presets single-device by default.

## When to execute a generated command

Execute a generated `run.py` command only after:

- the user approves training cost and external data use;
- the dataset exists and the data-preparation checks match the command dimensions;
- a CPU/GPU plan has been chosen;
- any benchmark-comparability changes are called out explicitly.
