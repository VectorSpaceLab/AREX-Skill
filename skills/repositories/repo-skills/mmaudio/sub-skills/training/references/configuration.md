# Training Configuration Reference

## Hydra layers

- `config/base_config.yaml` supplies the shared model, EMA, sampling, and external-weight defaults.
- `config/train_config.yaml` adds the training-only schedule, save intervals, and smoke/debug knobs.
- `config/data/base.yaml` supplies the training, validation, and example data paths.

## Supported model variants

| Model | Training support | Training sample rate | Sequence-length notes |
| --- | --- | --- | --- |
| `small_16k` | Yes | 16 kHz | `latent_seq_len=250`, `clip_seq_len=64`, `sync_seq_len=192`. Best fit for the bundled smoke fixtures. |
| `small_44k` | Yes | 44.1 kHz | `latent_seq_len=345`, `clip_seq_len=64`, `sync_seq_len=192`. |
| `medium_44k` | Yes | 44.1 kHz | Same sequence lengths as `small_44k`, with a wider model. |
| `large_44k` | Yes | 44.1 kHz | Same sequence lengths as `small_44k`, with a deeper model. |
| `large_44k_v2` | No | 44.1 kHz | The current training code rejects this name because the selector only accepts names ending in `16k` or `44k`. |

`train.py` patches `cfg.data_dim.latent_seq_len`, `cfg.data_dim.clip_seq_len`, and `cfg.data_dim.sync_seq_len` from the selected model, so those lengths are not usually something to hand-edit.

## Key training knobs

| Key | Meaning | Default / note |
| --- | --- | --- |
| `exp_id` | Run name and output-directory suffix. | Writes to `output/<exp_id>`. |
| `debug` | Makes logging more aggressive and skips the final save step inside the training loop. | Does not suppress the final sample call. |
| `compile` | Enables `torch.compile` for the train/val functions and feature extractors. | Turn it off for smoke or environment debugging. |
| `amp` | Enables CUDA autocast in BF16 mode. | Default `True`. |
| `enable_grad_scaler` | Turns on GradScaler. | Default `False`; the repo disabled it for stability. |
| `batch_size` | Total training batch size before the runtime split across GPUs. | Must be compatible with the world size. |
| `eval_batch_size` | Per-GPU batch size for the validation loader. | Separate from `batch_size`. |
| `num_iterations` | Total optimization steps. | Default `300000`. |
| `val_interval` | Validation cadence during training. | Default `5000`. |
| `eval_interval` | Periodic evaluation cadence during training. | Default `20000`. |
| `save_eval_interval` | Controls whether periodic eval outputs are tagged as saved-eval or cache-like outputs. | Default `40000`. |
| `save_weights_interval` | Weight snapshot cadence. | Default `10000`. |
| `save_checkpoint_interval` | Full checkpoint cadence. | Default `10000`. |
| `save_copy_iterations` | Extra snapshot steps for curated copies. | Optional list. |
| `vgg_oversample_rate` | Oversamples VGGSound relative to the audio-text corpora. | Default `5`; use `3` for medium/large models. |
| `cudnn_benchmark` | Enables cuDNN autotuning. | Default `True`. |
| `num_workers` | DataLoader workers per GPU. | Default `10`. |
| `pin_memory` | Dataloader pin-memory flag. | Default `False`. |
| `learning_rate`, `linear_warmup_steps`, `lr_schedule`, `lr_schedule_steps`, `lr_schedule_gamma`, `clip_grad_norm`, `weight_decay` | Optimizer and schedule settings. | Follow `config/train_config.yaml` unless you are intentionally tuning. |

## Resume and weight-loading semantics

| Key | Meaning | Caveat |
| --- | --- | --- |
| `checkpoint` | Full training-state resume. | Loads model weights, optimizer, scheduler, and EMA state. |
| `weights` | Model-weight initialization only. | Loads only the network weights, not optimizer state. |
| Existing `output/<exp_id>/<exp_id>_ckpt_last.pth` | Automatic resume fallback. | It shadows `weights` if present, so a reused `exp_id` can silently resume an older run. |

Rule of thumb: use `checkpoint=` when you want to continue the same run, and use a fresh `exp_id` when you want to start a new run from pretrained weights.

## EMA settings

| Key | Meaning |
| --- | --- |
| `ema.enable` | Enables EMA bookkeeping during training. |
| `ema.sigma_rels` | Sigma schedule for post-hoc EMA synthesis. |
| `ema.update_every` | How often the EMA state updates. |
| `ema.checkpoint_every` | How often intermediate EMA checkpoints are written. |
| `ema.checkpoint_folder` | Defaults to `output/<exp_id>/ema_ckpts`. |
| `ema.default_output_sigma` | Sigma used when synthesizing the final EMA state. |

The final synthesized EMA file is written as `output/<exp_id>/<exp_id>_ema_final.pth`.

## Data-path matrix

| Config path | Schema / role | Notes |
| --- | --- | --- |
| `data.ExtractedVGG` | `id`, `label`, memmap directory | Main video training data. |
| `data.ExtractedVGG_val` | validation cache + `gt_cache` | Used for the in-loop validation pass. |
| `data.ExtractedVGG_test` | test cache + `gt_cache` | Used by the built-in post-training sample path. |
| `data.AudioCaps`, `data.AudioSetSL`, `data.BBCSound`, `data.FreeSound`, `data.Clotho` | `id`, `caption`, memmap directory | Audio-text corpora mixed into training. |
| `data.Example_video` | smoke fixture cache | Used when `example_train=True`. |
| `data.Example_audio` | smoke fixture cache | Used when `example_train=True`. |

## External asset matrix

| Asset | Default path | Needed for |
| --- | --- | --- |
| Empty-string encoding | `ext_weights/empty_string.pth` | Every training run. `Runner` loads it at startup. |
| 16k VAE | `ext_weights/v1-16.pth` | `small_16k` training and the 16k feature path. |
| 44k VAE | `ext_weights/v1-44.pth` | 44k training variants. |
| 16k vocoder | `ext_weights/best_netG.pt` | 16k training path. |
| Synchformer weights | `ext_weights/synchformer_state_dict.pth` | Every training run. |

The 44k vocoder is handled by the repo's feature utilities rather than by the same explicit 16k asset path.

## Path conventions

- `output/<exp_id>` is the training run directory.
- Hydra writes its snapshot subdirectory under the same run directory.
- `train.py` saves checkpoints and weights directly under `output/<exp_id>`.
- The post-training sample path appends `output_name` only to its output tag; it does not switch the underlying extracted test cache.

## Quirks to remember

- `mini_train` is present in the config but is not a reliable standalone smoke switch in the current loader logic.
- Training-side `batch_size` and sample-side `batch_size` do not mean the same thing; the training code splits the former across GPUs, while the sample path uses the value as given.
- The built-in post-training sample is not a generic batch-eval switch. It uses the extracted VGGSound test path wired into the config.

## Evidence labels

`config/base_config.yaml`, `config/train_config.yaml`, `config/data/base.yaml`, `train.py`, `mmaudio/runner.py`, `mmaudio/sample.py`, `mmaudio/data/data_setup.py`, `mmaudio/model/sequence_config.py`.
