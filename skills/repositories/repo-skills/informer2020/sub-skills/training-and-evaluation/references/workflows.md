# Workflows

## 1) Smoke-first path
- Build a tiny synthetic fixture with [`../../../scripts/make_tiny_forecast_csv.py`](../../../scripts/make_tiny_forecast_csv.py).
- Validate the fixture with [`../../../scripts/check_forecast_csv.py`](../../../scripts/check_forecast_csv.py).
- Run the bundled smoke helper with [`../../../scripts/run_forecasting_smoke.py`](../../../scripts/run_forecasting_smoke.py).
- For CPU-only verification, use the smoke helper's CPU backend option or hide CUDA before launching.
- Keep smoke runs small: `model=informer`, `attn=prob`, `itr=1`, short lengths, small batch size, and a unique description.

## 2) Choose the model and attention
| Choose | When | Notes |
| --- | --- | --- |
| `informer` | Default long-sequence training | Single encoder; `e_layers` is an integer. |
| `informerstack` | You want the stacked encoder variant | `s_layers` is the real depth control; the builder reads that list instead of `e_layers`. |
| `prob` | Long sequences, normal benchmark runs | ProbSparse encoder attention; default in shipped presets. |
| `full` | Small debug runs or transformer baseline | Slower and heavier; decoder cross-attention is still full in either case. |

- `distil` toggles encoder downsampling off when the flag is added.
- `mix` toggles decoder mix attention off when the flag is added.
- `output_attention` adds attention tensors to the forward return, but the trainer still optimizes the prediction tensor.
- `informerlight(TBD)` is only a placeholder label in the help text; the current model builder accepts `informer` and `informerstack`.

## 3) Standard train / validate / test cycle
1. Pick the data family and feature mode (`M`, `S`, or `MS`).
2. Set `seq_len`, `label_len`, and `pred_len` to match the horizon you care about.
3. Set `itr` for the number of independent repeats. Each repeat gets its own repeat index in the setting string.
4. Tune `train_epochs`, `batch_size`, `patience`, `learning_rate`, `lradj`, and `use_amp`.
5. Launch the run. The source entry point trains, validates, tests, and, when requested, predicts.
6. Read the artifacts:
   - `checkpoints/<setting>/checkpoint.pth`
   - `results/<setting>/metrics.npy`
   - `results/<setting>/pred.npy`
   - `results/<setting>/true.npy`
   - `results/<setting>/real_prediction.npy` when `do_predict` is enabled

There is no separate eval-only branch in the shipped entry point; train/test is the normal path, and best-checkpoint loading happens after training.

## 4) Interpret outputs
- `metrics.npy` stores `[mae, mse, rmse, mape, mspe]`.
- Lower is better for every metric.
- `mape` and `mspe` are fragile when true values are near zero.
- `setting` is the directory fingerprint for the run; it includes model, data, feature mode, lengths, architecture, attention, factor, embed type, `distil`, `mix`, description, and the repeat index.

## 5) Benchmark preset guidance
The shipped long-run presets are reference templates, not smoke defaults. They all use `model=informer`, `attn=prob`, and `des=Exp`, then sweep lengths and depths by dataset family.

- ETTh1: M presets `48/48/24`, `96/48/48`, `168/168/168`, `168/168/336`, `336/336/720`; S presets `720/168/24`, `720/168/48`, `720/336/168`, `720/336/336`, `720/336/720`; mostly `e_layers=2`, `d_layers=1`, `itr=5`.
- ETTh2: M presets `48/48/24`, `96/96/48`, `336/336/168`, `336/168/336`, `720/336/720`; S presets `48/48/24`, `96/96/48`, `336/336/168`, `336/168/336`, `336/336/720`; mixes `e_layers=2/3`, `d_layers=1/2`, `itr=5`.
- ETTm1: M presets `672/96/24`, `96/48/48`, `384/384/96`, `672/288/288`, `672/384/672`; S presets `96/48/24`, `96/48/48`, `384/384/96`, `384/384/288`, `384/384/672`; minute-level family, so adapt it with `freq=t`; `itr=5`.
- WTH: M presets `168/168/24`, `96/96/48`, `336/168/168`, `720/168/336`, `720/336/720`; S presets `720/168/24`, `720/168/48`, `168/168/168`, `336/336/336`, `720/336/720`; `e_layers=2/3`, `d_layers=1/2`, `itr=3`.

If you need the stack variant, swap to `informerstack` and supply `s_layers` instead of relying on the single-encoder pattern.
