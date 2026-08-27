# Forecasting Workflows

## Long-term forecasting

Core command pattern:

```bash
python -u run.py \
  --task_name long_term_forecast --is_training 1 \
  --root_path ./dataset/ETT-small/ --data_path ETTh1.csv \
  --model_id ETTh1_96_96 --model TimesNet --data ETTh1 \
  --features M --seq_len 96 --label_len 48 --pred_len 96 \
  --e_layers 2 --d_layers 1 --factor 3 \
  --enc_in 7 --dec_in 7 --c_out 7 \
  --d_model 16 --d_ff 32 --top_k 5 --des Exp --itr 1
```

For a CPU smoke, switch to a local tiny `custom` CSV, `DLinear`, short windows, `--train_epochs 1 --num_workers 0 --no_use_gpu`, and matching channel counts.

## Custom CSV forecasting

Use `--data custom` when the user has their own CSV with `date` and target columns. Set:

- `--root_path` to the folder.
- `--data_path` to the CSV filename.
- `--features M`, `S`, or `MS`.
- `--target` to the target column for `S`/`MS`.
- `--enc_in`, `--dec_in`, `--c_out` to match the feature mode and model expectations.

## Short-term M4 forecasting

Pattern:

```bash
python -u run.py \
  --task_name short_term_forecast --is_training 1 \
  --root_path ./dataset/m4 --seasonal_patterns Monthly \
  --model_id m4_Monthly --model TimesNet --data m4 \
  --features M --enc_in 1 --dec_in 1 --c_out 1 \
  --batch_size 16 --d_model 32 --d_ff 32 --top_k 5 \
  --learning_rate 0.001 --loss SMAPE --des Exp --itr 1
```

Run all six seasonal patterns (`Yearly`, `Quarterly`, `Monthly`, `Weekly`, `Daily`, `Hourly`) before expecting averaged M4 summary metrics.

## TimeXer / exogenous forecasting

TimeXer recipes are ordinary `long_term_forecast` commands with `--model TimeXer`. Exogenous script folders use datasets such as ECL, EPF, ETT, Traffic, and Weather. Some recipes use `features MS` to forecast the target channel with other variables as exogenous context.

Example target-only TimeXer shape expectation: `features MS` returns `(batch, pred_len, 1)`.

## Zero-shot forecasting

Pattern:

```bash
python -u run.py \
  --task_name zero_shot_forecast --is_training 0 \
  --root_path ./dataset/ETT-small/ --data_path ETTh1.csv \
  --model_id ETTh1_2048_96 --model Chronos2 --data ETTh1 \
  --features M --seq_len 2048 --pred_len 96 --enc_in 7 --des Exp --itr 1
```

Before running, confirm the selected model package, model cache/network access, and device assumptions. Several zero-shot model files instantiate remote pretrained models and hard-code CUDA or CUDA-like device maps.

## Scaling from smoke to benchmark

1. Validate data locally.
2. Run a CPU or one-GPU smoke with tiny windows and one epoch.
3. Restore benchmark window lengths and model dimensions.
4. Restore GPU selection and batch sizes.
5. Run one horizon/dataset first.
6. Expand to all horizons/seasons only after outputs are correct.
