# CLI reference

This is a task-oriented map of the training / evaluation flags.

## 1) Core selection and built-in data overrides

| Flag | What it drives | Notes |
| --- | --- | --- |
| `--model` | Model family | Use `informer` or `informerstack`. The current builder does not implement `informerlight`; treat that help-text label as a placeholder. |
| `--data` | Dataset preset | When it matches a built-in family, the parser overwrites path, target, and tensor widths. |
| `--features` | Forecasting mode | `M` = multivariate in / multivariate out, `S` = univariate in / univariate out, `MS` = multivariate in / univariate out. |
| `--root_path` | Data root | Combine with `--data_path` unless the preset table rewrites it. |
| `--data_path` | CSV filename | Built-in presets replace this with the dataset-specific file name. |
| `--target` | Target column | Used for `S` and `MS`; built-in presets may overwrite it. |
| `--cols` | Input columns | For custom CSVs only; schema details belong in the custom-data sub-skill. |
| `--freq` | Time-feature granularity | Use the single-letter aliases the trainer consumes; the preset families stick to `h` or `t`. |

### Built-in preset overrides

| Data | data_path | target | `M` widths | `S` widths | `MS` widths |
| --- | --- | --- | --- | --- | --- |
| `ETTh1` | `ETTh1.csv` | `OT` | `7 / 7 / 7` | `1 / 1 / 1` | `7 / 7 / 1` |
| `ETTh2` | `ETTh2.csv` | `OT` | `7 / 7 / 7` | `1 / 1 / 1` | `7 / 7 / 1` |
| `ETTm1` | `ETTm1.csv` | `OT` | `7 / 7 / 7` | `1 / 1 / 1` | `7 / 7 / 1` |
| `ETTm2` | `ETTm2.csv` | `OT` | `7 / 7 / 7` | `1 / 1 / 1` | `7 / 7 / 1` |
| `WTH` | `WTH.csv` | `WetBulbCelsius` | `12 / 12 / 12` | `1 / 1 / 1` | `12 / 12 / 1` |
| `ECL` | `ECL.csv` | `MT_320` | `321 / 321 / 321` | `1 / 1 / 1` | `321 / 321 / 1` |
| `Solar` | `solar_AL.csv` | `POWER_136` | `137 / 137 / 137` | `1 / 1 / 1` | `137 / 137 / 1` |

## 2) Sequence and decoder shape

| Flag | What it drives | Notes |
| --- | --- | --- |
| `--seq_len` | Encoder context length | The history window fed into the encoder. |
| `--label_len` | Decoder warm-start length | The known prefix copied into the decoder input. |
| `--pred_len` | Forecast horizon | The number of future steps to predict. |
| `--padding` | Decoder padding fill | `0` uses zeros; `1` uses ones. |

The decoder input is the label window plus the padding window, so changing any of these lengths changes the run fingerprint and the result directory.

## 3) Model and architecture knobs

| Flag | What it drives | Notes |
| --- | --- | --- |
| `--enc_in`, `--dec_in`, `--c_out` | Input / output widths | Built-in data presets may rewrite them from the dataset table. |
| `--d_model` | Hidden width | Larger values increase memory and runtime. |
| `--n_heads` | Attention heads | Must divide the model width cleanly. |
| `--e_layers` | Encoder depth for `informer` | Ignored by `informerstack`; that model uses `s_layers`. |
| `--d_layers` | Decoder depth | Applies to both model families. |
| `--s_layers` | Stack depths | Comma-separated list, e.g. `3,2,1`; read only by `informerstack`. |
| `--d_ff` | Feed-forward width | Larger values increase memory and runtime. |
| `--factor` | ProbSparse sampling factor | Mostly relevant when `attn=prob`. |
| `--attn` | Attention mode | `prob` is the efficient sparse choice; `full` is the transformer baseline. |
| `--embed` | Time-feature embedding | `timeF`, `fixed`, or `learned`. |
| `--activation` | Nonlinearity | `gelu` is the default. |
| `--dropout` | Dropout rate | Affects embeddings and blocks. |
| `--distil` | Encoder distillation | This is a negative flag: adding it turns distillation off. |
| `--mix` | Decoder mix attention | This is also a negative flag: adding it turns mix attention off. |
| `--output_attention` | Attention return | Enables attention tensors in the forward return. |

Practical note: decoder cross-attention stays full attention even when encoder attention is `prob`.

## 4) Training and optimization

| Flag | What it drives | Notes |
| --- | --- | --- |
| `--itr` | Repeat count | Each repeat is a full train / test cycle with its own repeat index in the setting string. |
| `--train_epochs` | Epoch cap | Early stopping may end the run sooner. |
| `--batch_size` | Mini-batch size | Smaller values are safer for long horizons and smoke runs. |
| `--patience` | Early stopping patience | Validation loss controls the stop decision. |
| `--learning_rate` | Adam learning rate | The trainer uses Adam. |
| `--lradj` | LR schedule | `type1` halves the LR each epoch; `type2` uses a fixed step schedule. |
| `--use_amp` | Mixed precision | Only useful on CUDA. |
| `--inverse` | Output de-scaling | Restores predictions before metrics when the dataset supports it. |
| `--num_workers` | DataLoader workers | Keep low for tiny smoke runs if startup cost matters. |
| `--des` | Experiment description | Part of the result-directory fingerprint. |
| `--loss` | Loss label | This code path still uses MSELoss, so the flag does not switch the criterion by itself. |

## 5) Device control

| Flag | What it drives | Notes |
| --- | --- | --- |
| `--use_gpu` | GPU gate | It is parsed as a bool, so `--use_gpu False` is not a safe CPU switch. |
| `--gpu` | Primary GPU id | Also used to set the visible device when GPU mode is active. |
| `--use_multi_gpu` | DataParallel | Only matters when GPU mode is on. |
| `--devices` | Visible device list | Comma-separated ids; the first entry becomes the primary GPU. |

When device control is active, the launcher resets the visible CUDA devices before the model is built.

## 6) Output and prediction

| Flag | What it drives | Notes |
| --- | --- | --- |
| `--checkpoints` | Checkpoint base directory | Best checkpoints land under `checkpoints/<setting>/checkpoint.pth`. |
| `--do_predict` | Future-prediction pass | Runs after test and writes `real_prediction.npy` into the result folder. |

## 7) Gotchas
- `--distil` and `--mix` disable features; the help text is easy to read backwards.
- `--model informerlight(TBD)` is not implemented in this snapshot.
- `--loss` is not a real criterion switch here.
- `--use_gpu False` is not a reliable CPU switch.
- `--s_layers` only matters for `informerstack`.
- Built-in presets may overwrite path, target, and width flags, so inspect the selected dataset before assuming custom values will survive.
