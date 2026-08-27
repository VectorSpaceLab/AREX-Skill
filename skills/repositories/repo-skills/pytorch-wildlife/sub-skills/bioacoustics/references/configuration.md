# Configuration reference

`load_config(config_path)` returns a `DomainConfig` built from YAML. All keys
are optional at the Python dataclass level, but a usable run should set the
three root paths and the domain/class metadata. `${NAME}` environment variables
are expanded recursively before nested dataclasses are constructed. `PathConfig`
also expands its three path fields during initialization. `save_config` writes
the nested dataclasses back to YAML.

## Exact schema and defaults

| YAML section | Key | Default |
|---|---|---:|
| root | `name` | `""` |
| root | `datasets` | `[]` |
| root | `class_names` | `{}` |
| paths | `data_root` | `""` |
| paths | `output_root` | `""` |
| paths | `spectrograms_dir` | `""` |
| paths | `annotations_file` | `annotations.json` |
| paths | `windows_json` | `windows_annotations.json` |
| audio | `sample_rate` | `48000` |
| audio | `window_size_sec` | `5.0` |
| audio | `overlap_sec` | `4.0` |
| audio | `window_strategy` | `sliding` |
| audio | `negative_proportion` | `0.5` |
| audio | `windows_csv` | `""` |
| audio | `windows_json` | `""` |
| audio | `multiclass` | `false` |
| audio | `min_overlap_sec` | `0` |
| spectrogram | `n_fft` | `2048` |
| spectrogram | `hop_length` | `512` |
| spectrogram | `n_mels` | `224` |
| spectrogram | `top_db` | `80.0` |
| spectrogram | `f_min` | `0.0` |
| spectrogram | `mono_channel` | `left` |
| spectrogram | `fill_highfreq` | `true` |
| spectrogram | `fill_mean_below_sr` | `false` |
| spectrogram | `noise_db_std` | `3.0` |
| spectrogram | `storage_dtype` | `float32` |
| training | `batch_size` | `32` |
| training | `num_workers` | `4` |
| training | `lr` | `1e-4` |
| training | `weight_decay` | `1e-4` |
| training | `epochs` | `50` |
| training | `backbone` | `resnet18` |
| training | `num_classes` | `2` |
| training | `label_smoothing` | `0.0` |
| training | `target_size` | `[224, 469]` |
| training | `x_col` | `spec_name` |
| training | `y_col` | `label` |
| training | `normalize` | `true` |
| training | `use_specaug` | `false` |
| training | `pos_weight` | `1.0` |
| training | `conf_threshold` | `0.5` |
| training | `freeze_backbone` | `none` |
| training | `backbone_lr_ratio` | `1.0` |
| splits | `test_size` | `0.15` |
| splits | `val_size` | `0.15` |
| splits | `n_splits` | `5` |
| splits | `random_state` | `42` |
| splits | `custom_splits_folder` | `null` |

`DomainConfig.is_binary` is true only when `training.num_classes == 2`.
`AudioConfig.hop_size_sec` is `window_size_sec - overlap_sec`; the source
schema does not guard against zero or negative hop values, so callers must.
When `audio.windows_json` is set and `paths.windows_json` was not supplied,
`load_config` propagates the audio value into `paths.windows_json`.

## Preflight validation

Before creating anything, require nonempty, user-owned `data_root`,
`output_root`, and `spectrograms_dir`; resolve relative paths intentionally.
Require `sample_rate`, `n_fft`, `hop_length`, and `n_mels` to be positive;
`mono_channel` must be `left`, `right`, or `mean`; and `storage_dtype` must be
`float16` or `float32`. Require `window_size_sec > 0` and
`0 <= overlap_sec < window_size_sec`. For balanced windows require
`0 <= negative_proportion < 1`. `customized` requires a callable
`custom_builder`, and `windows_csv` is only meaningful for a caller-defined
builder.

For a classifier, accept only `num_classes == 2` or `num_classes > 2`.
Multiclass labels must be integer ids in `0..num_classes-1`; if names are
provided, use exactly one name for each class and preserve YAML insertion
order when passing them to the model. `resnet18`, `resnet34`, and `resnet50`
are the supported backbones. `freeze_backbone` accepts `none`, `all`, `early`,
`layer1`, `layer2`, or `layer3`.
