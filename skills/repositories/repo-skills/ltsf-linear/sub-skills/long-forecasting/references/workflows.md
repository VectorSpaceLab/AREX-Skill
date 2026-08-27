# Workflows

## Shared dataset layout

The root workflow and the FEDformer route use the same dataset-root convention.
Point `--root_path` to a directory that contains the CSV files and set
`--data_path` to the exact file name.

### Benchmark CSV shape

- The CSV must contain a `date` column.
- ETT CSVs are already preprocessed and are selected with `--data ETTh1`,
  `--data ETTh2`, `--data ETTm1`, or `--data ETTm2`.
- `--features M` means multivariate-to-multivariate.
- `--features S` means univariate-to-univariate.
- `--features MS` means multivariate input with a single target output.
- For `S` and `MS`, keep `--target` pointed at the prediction column, usually
  `OT`.
- For `custom`, the CSV should still have `date` plus the feature columns used
  by the model.

### Channel counts

For custom multivariate runs, set `--enc_in`, `--dec_in`, and `--c_out` to the
number of non-`date` columns that participate in the run. For the Linear family,
`--enc_in` is the critical channel count.

## Train and test

### Linear-family example

```bash
python scripts/run_long_forecasting.py \
  --is_training 1 \
  --model_id ETTh1_336_96 \
  --model DLinear \
  --data ETTh1 \
  --root_path ./dataset/ \
  --data_path ETTh1.csv \
  --features M \
  --seq_len 336 \
  --label_len 48 \
  --pred_len 96 \
  --enc_in 7 \
  --dec_in 7 \
  --c_out 7 \
  --individual \
  --des Exp \
  --itr 1
```

Use the same pattern for `Linear` or `NLinear` by changing `--model`.

### Former-family example

```bash
python scripts/run_long_forecasting.py \
  --is_training 1 \
  --model_id electricity_96_96 \
  --model Autoformer \
  --data custom \
  --root_path ./dataset/ \
  --data_path electricity.csv \
  --features M \
  --seq_len 96 \
  --label_len 48 \
  --pred_len 96 \
  --enc_in 321 \
  --dec_in 321 \
  --c_out 321 \
  --e_layers 2 \
  --d_layers 1 \
  --factor 3 \
  --embed_type 1 \
  --des Exp \
  --itr 1
```

### Test-only or predict-only

- Use `--is_training 0` to skip training.
- Add `--do_predict` to write `real_prediction.npy` and `real_prediction.csv`.
- Keep the test run's shape-related arguments identical to the training run so
  the checkpoint path resolves correctly.

Example:

```bash
python scripts/run_long_forecasting.py \
  --is_training 0 \
  --do_predict \
  --model_id ETTh1_336_96 \
  --model DLinear \
  --data ETTh1 \
  --root_path ./dataset/ \
  --data_path ETTh1.csv \
  --features M \
  --seq_len 336 \
  --label_len 48 \
  --pred_len 96 \
  --enc_in 7 \
  --dec_in 7 \
  --c_out 7
```

## Preset sweep families

The shell scripts in `scripts/EXP-LongForecasting/`, `scripts/EXP-LookBackWindow/`,
and `scripts/EXP-Embedding/` are reference-only copies of the paper's grids.
Use them as a value map, not as the default runtime interface.

- `scripts/EXP-LongForecasting/*.sh` — main benchmark presets for the core
  datasets.
- `scripts/EXP-LookBackWindow/*.sh` — vary `seq_len` while keeping the model and
  forecast length fixed.
- `scripts/EXP-Embedding/*.sh` — vary `embed_type` for the former models.

To adapt a sweep safely, keep one dataset and one model family, then change only
one axis at a time.

## DLinear weight visualization

1. Train a DLinear checkpoint.
2. Point the plotting helper at the exact checkpoint file or at the checkpoint
   directory.
3. Save the plots into a separate output root so they do not mix with training
   logs.
4. If the checkpoint used `--individual`, the helper falls back to the first
   channel weight when the non-individual keys are absent.

Example:

```bash
python scripts/plot_linear_weights.py \
  --checkpoint checkpoints/ETTh1_336_96_DLinear_ETTh1_ftM_sl336_ll48_pl96_dm512_nh8_el2_dl1_df2048_fc1_ebtimeF_dtTrue_Exp_0/checkpoint.pth \
  --output-root weights_plot
```

## Tiny smoke check

The bundled smoke helper exercises Linear, DLinear, NLinear, Informer,
Transformer, and Autoformer on a tiny deterministic batch. Use it after edits to
confirm that the model constructors and forward paths still agree.

```bash
python scripts/smoke_long_forecasting.py
```

If you only want to check the root parser, run:

```bash
python run_longExp.py --help
```
