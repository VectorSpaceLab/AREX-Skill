# FEDformer CLI Reference

Use `FEDformer/run.py` from inside the FEDformer subtree of a checkout. The bundled wrapper `scripts/run_fedformer.py` resolves that working directory for you and prints or runs the native command.

## Native command shape

```bash
cd <repo-root>/FEDformer
python -u run.py \
  --is_training 1 \
  --model FEDformer \
  --data ETTh1 \
  --data_path ETTh1.csv \
  --root_path <dataset-root> \
  --features S \
  --seq_len 96 \
  --label_len 48 \
  --pred_len 96
```

## Model family and FEDformer-specific flags

| Flag | Values or shape | Applies to | What it controls | Notes |
| --- | --- | --- | --- | --- |
| `--model` | `FEDformer`, `Autoformer`, `Informer`, `Transformer` | all runs | Chooses the model family inside this subrepo | The parser default is `Reformer`, which is not in the model map; set this explicitly. |
| `--version` | `Fourier`, `Wavelets` | FEDformer only | Selects the FEDformer attention branch | Use `Fourier` for mode selection over frequency bins; use `Wavelets` for the multiresolution branch. |
| `--mode_select` | `random`, `low` | FEDformer + Fourier branch | Chooses which Fourier modes are kept | `random` shuffles the candidate modes; `low` keeps the lowest bins. |
| `--modes` | integer | FEDformer branch selection | Limits the number of selected modes | Values above the available frequency span are clipped in the model code. |
| `--L` | integer | Wavelets only | Ignores deeper wavelet levels | Has no practical effect in the Fourier branch. |
| `--base` | `legendre`, `chebyshev` | Wavelets only | Picks the multiresolution basis | Leave it at `legendre` unless you know you want the alternative basis. |
| `--cross_activation` | `tanh`, `softmax` | Wavelets only | Chooses the cross-attention activation in the wavelet branch | Only relevant when `--version Wavelets`. |
| `--embed_type` | `0`, `1`, `2`, `3` | FEDformer encoder/decoder embeddings | Chooses the embedding variant | `0` = no positional embedding, `1` = full embedding, `2` = value-only, `3` = value + position. |
| `--output_attention` | flag | all models | Returns attention maps as a second output | Useful for debugging and analysis. |

## Data and loader flags

| Flag | Typical values | What it controls | Notes |
| --- | --- | --- | --- |
| `--data` | `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, `custom`, `sin` | Loader preset | Pick the preset that matches the CSV family. |
| `--root_path` | directory path | Dataset root | Point to the directory that contains the CSV files. |
| `--data_path` | CSV filename | Input file | Must exist under `root_path`. |
| `--features` | `M`, `S`, `MS` | Forecasting layout | `M` is multivariate-to-multivariate, `S` is univariate, `MS` is multivariate-to-single-target. |
| `--target` | column name | Supervised target | Required for `S` and `MS`. |
| `--freq` | `h`, `t`, `d`, `b`, `w`, `m`, or a finer alias | Time features | Must match the cadence of the CSV timestamps. |

## Forecast shape flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--seq_len` | encoder input length | Common values are 96, 192, 336, 720, or the shorter look-back windows used in the sweep scripts. |
| `--label_len` | decoder warmup length | Usually half of `seq_len` in the bundled scripts. |
| `--pred_len` | forecast horizon | The main sweep axis in the long-forecasting scripts. |
| `--enc_in` | encoder channels | Must match the actual input width. |
| `--dec_in` | decoder channels | Must match the decoder input width. |
| `--c_out` | output channels | Must match the forecast width. |
| `--moving_avg` | kernel size or Python list of kernels | Decomposition window(s) | The parser default is already a list, but shell overrides are not list-parsed; leave the default alone or set it in code. |
| `--factor` | integer | Attention factor | Used by the Autoformer/Informer-style attention components. |
| `--distil` | flag | Encoder distillation | Leave it enabled unless you know you need the non-distilled path. |
| `--activation` | `relu`, `gelu` | MLP activation | Shared across the model family. |

## Training and device flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--is_training` | `1` or `0` | `1` runs the train+test path; `0` is a test-only path that is not the primary route here. |
| `--itr` | repeat count | Repeats the experiment with the same configuration. |
| `--train_epochs` | epochs | Training loop length. |
| `--batch_size` | batch size | Training and validation batch size. |
| `--patience` | early-stopping patience | Stops training when validation stops improving. |
| `--learning_rate` | float | Optimizer learning rate. |
| `--lradj` | `type1`, `type2`, `type3`, `type4` | Learning-rate schedule. |
| `--use_amp` | flag | Automatic mixed precision on CUDA. |
| `--use_gpu` | bool-like parser arg | GPU toggle | The parser uses `type=bool`, so shell strings are unreliable; keep the GPU path simple and prefer the wrapper plus CUDA visibility. |
| `--gpu` | integer | Selected GPU index | Usually `0` inside the visible GPU set. |
| `--use_multi_gpu` | flag | Multi-GPU training | Pair with `--devices`. |
| `--devices` | comma-separated ids | Multi-GPU device list | Example: `0,1`. |

## Common command patterns

### Fourier run

```bash
python scripts/run_fedformer.py --repo-root <repo-root> --run -- \
  --is_training 1 \
  --model FEDformer \
  --version Fourier \
  --mode_select low \
  --modes 64 \
  --data ETTh1 \
  --data_path ETTh1.csv \
  --root_path <dataset-root> \
  --features S \
  --seq_len 96 \
  --label_len 48 \
  --pred_len 96
```

### Wavelets run

```bash
python scripts/run_fedformer.py --repo-root <repo-root> --run -- \
  --is_training 1 \
  --model FEDformer \
  --version Wavelets \
  --L 3 \
  --base legendre \
  --cross_activation tanh \
  --data ETTm1 \
  --data_path ETTm1.csv \
  --root_path <dataset-root> \
  --features M \
  --seq_len 96 \
  --label_len 48 \
  --pred_len 96
```

## Usage notes

- Keep `--model` explicit. The parser default is not a valid model family member.
- Use the same dataset, lengths, and feature layout when comparing FEDformer with Autoformer, Informer, or Transformer.
- For `Wavelets`, the `L`, `base`, and `cross_activation` flags matter; for `Fourier`, the `mode_select` and `modes` flags matter.
- The source fork contains a `do_predict` and `is_training=0` path, but those branches are not the recommended route for new work. See `references/troubleshooting.md`.
