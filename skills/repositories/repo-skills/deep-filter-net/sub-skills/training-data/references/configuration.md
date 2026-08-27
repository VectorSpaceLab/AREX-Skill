# DeepFilterNet training configuration

DeepFilterNet training reads `BASE_DIR/config.ini`. If the file is missing, defaults are created as options are first accessed and then saved. Treat `config.ini` as part of the run state; keep it with checkpoints when resuming and change it deliberately for new experiments.

The config reader accepts case-insensitive section/option names and can also read environment variables named like the option in uppercase. Prefer explicit `config.ini` values for reproducible runs.

## Minimal training config shape

A small starting point for a new run:

```ini
[train]
model = deepfilternet3
seed = 43
device = 
batch_size = 4
batch_size_eval = 4
num_workers = 2
max_sample_len_s = 3.0
max_epochs = 2
log_freq = 10
start_eval = false
detect_anomaly = false
validation_criteria = loss
validation_criteria_rule = min
early_stopping_patience = 5
global_ds_sampling_f = 1.0
dataloader_snrs = -5,0,5,10,20,40
dataloader_gains = -6,0,6

[df]
sr = 48000
fft_size = 960
hop_size = 480
nb_erb = 32
nb_df = 96
norm_tau = 1
lsnr_max = 35
lsnr_min = -15
min_nb_erb_freqs = 2
df_order = 5
df_lookahead = 2
pad_mode = output

[distortion]
p_reverb = 0.0
p_bandwidth_ext = 0.0
p_clipping = 0.0
p_zeroing = 0.0
p_air_absorption = 0.0
p_interfer_sp = 0.0

[optim]
lr = 0.001
lr_min = 1e-6
lr_warmup = 1e-4
warmup_epochs = 3
optimizer = adamw
weight_decay = 0.05
weight_decay_end = -1
momentum = 0
```

For a serious training run, increase `max_epochs`, tune batch sizes, and set loss/model sections appropriate to the selected architecture. Do not change `[df]` STFT/sample-rate settings in an existing checkpoint directory unless you are intentionally starting a new incompatible run.

## `[train]` section

| Option | Default observed in source | Role / guidance |
|---|---:|---|
| `seed` | `42` | Manual seed for Python/PyTorch and dataloader reproducibility. |
| `device` | empty | Device selection is handled by DeepFilterNet utilities; an empty value lets the package auto-select. Use only verified values for forced CPU/CUDA behavior. |
| `model` | `deepfilternet3` | Architecture name used by model initialization and the host batch-size key. Common values include `deepfilternet`, `deepfilternet2`, and `deepfilternet3`. |
| `jit` | `false` | Scripts the model with TorchScript after summary logging when enabled. Disable while debugging shape/config issues. |
| `mask_only` | `false` | Initializes/trains with deep-filter path disabled. Mutually exclusive in effect with DF-only training intentions. |
| `df_only` | `false` | Optimizer uses only DF-related parameters. |
| `batch_size` | `1` | Training batch size. Tune against GPU/CPU memory; host helper updates this key. |
| `batch_size_eval` | `0` | Validation/test batch size. `0` means use `batch_size`; host helper updates this key. |
| `num_workers` | `4` | Rust dataloader worker/thread count. Reduce when debugging or on small machines. |
| `num_prefetch_batches` | `32` | Prefetch queue multiplier passed to `PytorchDataLoader`. Large values can increase memory pressure. |
| `max_sample_len_s` | `5.0` | Maximum generated sample length in seconds. Pretrained configs commonly use `3.0`. |
| `overfit` | `false` | Reuses train data for all splits; useful only for debugging. |
| `log_timings` | `false` | Logs dataloader timing diagnostics. |
| `global_ds_sampling_f` | `1.0` | Multiplies every dataset row's sampling factor. |
| `dataloader_snrs` | `-5,0,5,10,20,40` | CSV integer SNR choices for generated mixtures. DeepFilterNet3 examples may include `-100` for noise-only cases. |
| `dataloader_gains` | `-6,0,6` | CSV integer speech gain choices. |
| `batch_size_scheduling` | empty | CSV list like `0/16,2/24,5/32`; first epoch must be `0`. The schedule never exceeds configured `batch_size`. |
| `max_epochs` | `10` | Training duration upper bound. |
| `start_eval` | `false` | Runs validation before the first training epoch when enabled. |
| `validation_criteria` | `loss` | Metric key used for best-checkpoint and early-stopping decisions. Must be present in validation metrics. |
| `validation_criteria_rule` | `min` | `min`/`max`; synonyms like `less`/`more` are normalized. |
| `early_stopping_patience` | `5` | Stops after this many non-improving validation checks. |
| `log_freq` | `100` | Training-loop logging/summaries every N steps. |
| `detect_anomaly` | `false` | Enables PyTorch anomaly detection; useful for NaNs, expensive for normal runs. |
| `cp_blacklist` | empty | CSV substrings of checkpoint keys to ignore while loading. Use only for deliberate partial checkpoint reuse. |
| `n_checkpoint_history` | `3` | Number of recent regular checkpoints retained. Set negative to keep all. |
| `n_best_checkpoint_history` | `5` | Number of best checkpoints retained. Set negative to keep all. |
| `train_autocast` | absent/false | Read by the host batch-size helper only; when true it uses `batch_size_autocast_train` from the host config. Verify actual mixed-precision behavior separately before relying on it. |

## `[df]` section

`[df]` controls signal-processing parameters used by model features, dataloader FFTs, and summaries.

| Option | Default | Role / guidance |
|---|---:|---|
| `sr` | `48000` | Training sample rate. Align HDF5 attrs, prepare-data `--sr`, and model config. |
| `fft_size` | `960` | STFT FFT size in samples. Used in host batch-size key. |
| `hop_size` | `480` | STFT hop size. |
| `nb_erb` | `32` | Number of ERB bands. |
| `nb_df` | `96` | Number of complex spectrogram bins for deep filtering. |
| `norm_tau` | `1` | Feature normalization decay. |
| `lsnr_max` / `lsnr_min` | `35` / `-15` | Local SNR target clamp range. |
| `min_nb_erb_freqs` | `2` | Minimum bins per ERB band. |
| `df_order` | `5` | Deep filtering order. |
| `df_lookahead` | `0` in code defaults; pretrained configs often use `1` or `2` | Deep filtering lookahead. |
| `pad_mode` | `input` | Padding mode for lookahead; pretrained configs may use `output` or legacy values. |

The config loader migrates some legacy `[clc]`/`deepfilternet]` deep-filter keys into `[df]`. Prefer current `[df]` keys for new configs.

## `[distortion]` section

These probabilities are passed to `libdfdata.PytorchDataLoader` for training-time augmentation:

| Option | Default | Role |
|---|---:|---|
| `p_reverb` | `0.2` in train code; pretrained examples use lower values | Probability of reverberation. If positive and no RIR dataset is available, the dataloader warns. |
| `p_bandwidth_ext` | `0.0` | Bandwidth extension/limiting augmentation. |
| `p_clipping` | `0.0` | Speech clipping distortion probability. |
| `p_zeroing` | `0.0` | Speech time-domain zeroing probability. |
| `p_air_absorption` | `0.0` | Air absorption augmentation probability. |
| `p_interfer_sp` | `0.0` | Interfering speaker probability. Requires enough speech material. |

Some dataloader augmentations can also be controlled with environment variables such as `DF_P_LFILT`, `DF_P_RESAMPLE`, `DF_P_BIQUAD`, `DF_P_CLIPPING`, `DF_P_CLIPPING_NOISE`, `DF_P_ZEROING`, `DF_P_AIR_AUG`, `DF_P_NOISE_GEN`, `DF_REVERB_DRR`, `DF_REVERB_RT60`, and `DF_REVERB_OFFSET_LATE`. Use environment overrides only for documented experiment runs and record them with the job.

## `[optim]` section

| Option | Default | Role |
|---|---:|---|
| `optimizer` | `adamw` | One of `adam`, `adamw`, `sgd`, `rmsprop`. Unsupported names raise. |
| `lr` | `5e-4` in code default; pretrained configs commonly use `0.001` | Base learning rate. Required for scheduler setup after config materialization. |
| `opt_betas` | `0.9,0.999` | Adam/AdamW betas as CSV floats. |
| `momentum` | `0` | Used by SGD/RMSprop. |
| `weight_decay` | `0.05` | Initial weight decay. |
| `weight_decay_end` | `-1` | If not `-1`, cosine weight-decay schedule is used. If schedule requested while initial weight decay is `0`, code raises it to a tiny positive value and records a warning. |
| `lr_min` | `1e-6` | Minimum learning rate for cosine schedule. |
| `lr_warmup` | `1e-4` | Warmup starting value; must be smaller than `lr`. |
| `warmup_epochs` | `3` | Warmup duration. |
| `lr_cycle_mul` | `1.0` | Cosine cycle length multiplier. |
| `lr_cycle_decay` | `0.5` | Cycle amplitude decay. |
| `lr_cycle_epochs` | `-1` | Initial cycle length; negative uses scheduler default behavior. |

## Model architecture sections

Architecture-specific sections such as `[deepfilternet]` provide channel counts, GRU dimensions, grouped-linear options, convolution kernels, DF iterations, and post-filter defaults. Keep these consistent with `train.model` and any checkpoint you resume from.

Common DeepFilterNet3-style keys include:

```ini
[deepfilternet]
conv_lookahead = 2
conv_ch = 64
conv_depthwise = True
emb_hidden_dim = 256
emb_num_layers = 3
df_hidden_dim = 256
df_num_layers = 2
dfop_method = df
df_gru_skip = groupedlinear
df_pathway_kernel_size_t = 5
df_n_iter = 1
enc_concat = False
conv_kernel = 1,3
conv_kernel_inp = 3,3
convt_kernel = 1,3
mask_pf = False
pf_beta = 0.02
```

If a model checkpoint reports missing/unexpected keys or tensor size mismatches, first verify `train.model`, the architecture section, `[df]` values, and `cp_blacklist` before attempting partial loading.

## Loss sections

The train loop constructs loss objects that read factors from sections such as:

- `[MaskLoss]`: `factor`, `mask`, `gamma`, `gamma_pred`, `f_under`, `max_freq`.
- `[SpectralLoss]`: `factor_magnitude`, `factor_complex`, `factor_under`, `gamma`.
- `[MultiResSpecLoss]`: `factor`, `factor_complex`, `gamma`, `fft_sizes`.
- `[SdrLoss]`: `factor`, `segmental_ws`.
- `[LocalSnrLoss]`: `factor`.
- `[ASRLoss]`: `factor`, `factor_lm`, `loss_lm`, `model`.

Set unused loss factors to `0`. ASR-related loss options can introduce extra model/dependency requirements; avoid enabling them unless the environment and data are prepared.

## Batch-size config file

The host batch-size helper uses a separate INI file with host-key sections:

```ini
[myhost_deepfilternet3_960]
batch_size_train = 32
batch_size_eval = 64
batch_size_autocast_train = 64
```

- `batch_size_eval` maps to `[train] batch_size_eval`.
- `batch_size_train` maps to `[train] batch_size` when `[train] train_autocast` is false/absent.
- `batch_size_autocast_train` maps to `[train] batch_size` when `[train] train_autocast = true`.

Use [`../scripts/set_batch_size.py`](../scripts/set_batch_size.py) from this sub-skill to update only those keys.
