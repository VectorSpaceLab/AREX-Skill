# CLI Reference

This route centers on `run_longExp.py`. The bundled wrapper in
[`scripts/run_long_forecasting.py`](../scripts/run_long_forecasting.py)
forwards the core arguments to the root launcher and adds a small amount of
safety around paths, dataset checks, and CPU forcing.

## Launch shape

```bash
python scripts/run_long_forecasting.py \
  --is_training 1 \
  --model_id <run-tag> \
  --model <Linear|DLinear|NLinear|Informer|Transformer|Autoformer> \
  --data <ETTh1|ETTh2|ETTm1|ETTm2|custom> \
  --root_path ./dataset/ \
  --data_path <csv-name> \
  --features <M|S|MS> \
  --seq_len <input-length> \
  --label_len <label-length> \
  --pred_len <forecast-length>
```

## Core flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--is_training` | Train/test/predict driver | `1` runs training first. `0` skips training and only tests or predicts. |
| `--train_only` | Skip validation and test | The root parser treats this as a bool-typed flag; the wrapper normalizes truthy and falsey forms. |
| `--model_id` | Run tag | Used inside the checkpoint directory name. Keep it stable between train and test. |
| `--model` | Model family | One of the six core models in this route. |
| `--data` | Dataset preset | `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, or `custom`. |
| `--root_path` | Dataset root | Usually a `dataset/` directory. |
| `--data_path` | CSV file name | Must resolve under `root_path`. |
| `--features` | Forecasting mode | `M`, `S`, or `MS`. |
| `--target` | Target column | Used for `S` and `MS`. The default is `OT`. |
| `--seq_len` | Look-back window | Input length to the encoder or linear layer. |
| `--label_len` | Decoder warm-up length | Used by the former models and prediction mode. |
| `--pred_len` | Forecast horizon | Output length. |
| `--checkpoints` | Checkpoint root | Default is `./checkpoints/`. |
| `--do_predict` | Save future predictions | Writes `real_prediction.npy` and `real_prediction.csv`. |

## Linear-family flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--individual` | Per-channel Linear layers | Common in the benchmark scripts for Linear, DLinear, and NLinear. |

For the Linear family, `enc_in` is the important channel count. `dec_in` and
`c_out` can mirror it for consistency, even though the forward pass does not use
the decoder path.

## Former-model flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--embed_type` | Embedding branch | The benchmark scripts sweep values `1` through `4` for the former models. |
| `--embed` | Time-feature embedding kind | Usually `timeF` in this repo. |
| `--d_model` | Hidden width | Default is `512` in the root CLI. |
| `--n_heads` | Attention heads | Must divide `d_model`. |
| `--e_layers` | Encoder depth | The reference scripts often use `2`. |
| `--d_layers` | Decoder depth | The reference scripts often use `1`. |
| `--d_ff` | Feed-forward width | Default is `2048`. |
| `--moving_avg` | Decomposition kernel | Used by Autoformer. |
| `--factor` | Attention factor | Used by Informer and Autoformer. |
| `--distil` | Enable distillation | The root parser uses `store_false`, so the default path keeps distillation on. |
| `--output_attention` | Return attention maps | Useful for inspection, not required for standard runs. |
| `--use_amp` | Mixed precision | Optional if the GPU and driver stack support it. |

## Device flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--use_gpu` | GPU toggle in the root parser | The root parser uses `type=bool`, so `False` values are misleading. Prefer the wrapper's `--cpu` flag. |
| `--gpu` | Primary GPU index | Used when the run is not multi-GPU. |
| `--use_multi_gpu` | Wrap the model in `DataParallel` | Requires `--devices` to list the visible GPU ids. |
| `--devices` | GPU id list | Comma-separated string such as `0,1,2,3`. |

## Setting and path naming

The root launcher builds the checkpoint and result directory name from the run
configuration. The key pattern is:

```text
{model_id}_{model}_{data}_ft{features}_sl{seq_len}_ll{label_len}_pl{pred_len}_dm{d_model}_nh{n_heads}_el{e_layers}_dl{d_layers}_df{d_ff}_fc{factor}_eb{embed}_dt{distil}_{des}_{itr}
```

That string is why train/test path mismatches happen when `model_id`, `des`, or
any of the shape-related flags change between runs.

## Dataset presets

- `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`: benchmark CSVs with a `date` column and
  preprocessed time features.
- `custom`: any CSV with a `date` column plus the feature columns used by the
  model.

For the shared dataset layout used by this route and FEDformer, point
`--root_path` to the directory that contains the CSVs and keep `--data_path`
set to the exact file name.

## Raw help check

To inspect the root parser directly, run:

```bash
python run_longExp.py --help
```

Use the wrapper when you want safer path resolution or CPU forcing.
