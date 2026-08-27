# Bioacoustics workflows

## Preparation

Use `prepare_dataset.py --config CONFIG` for all four companion steps:
`stats`, `windows`, `spectrograms`, and `splits`. Select a subset with
`--steps stats windows` (one or more choices). Safe order is:

1. `stats`: read the annotation JSON and report sounds, total duration,
   annotation count, and category counts.
2. `windows`: call `build_windows`; choose `sliding`, `balanced`, or a
   separately implemented `customized` builder. With 5-second windows and
   4-second overlap, the hop is 1 second; windows that would exceed a sound's
   duration are omitted.
3. `spectrograms`: map each window to its sound path and call
   `compute_mel_spectrograms_gpu`. This step reads audio and writes missing
   `.npy` files; it may be CPU-only and can be expensive.
4. `splits`: retain rows whose cache exists and create grouped splits. The
   default split settings are test 0.15, validation 0.15, five folds, and
   random state 42. Small datasets may not have enough groups/classes for the
   requested stratification.

Use `--validate-only` to parse and validate a config without reading audio or
writing outputs. The bundled script is a safe adaptation of the public
companion flow and imports the installed package rather than a checkout.

## Training contract

The companion `train.py` flags are:

- data: `--config`, `--train_csv`, `--val_csv`, `--test_csv`, `--root`,
  `--x_col`, `--target_size H W`;
- model: `--num_classes` (2 or greater), `--class_names`, and
  `--backbone {resnet18,resnet34,resnet50}`;
- optimization: `--batch_size`, `--num_workers`, `--lr`, `--weight_decay`,
  `--label_smoothing`, `--epochs`, `--ckpt_path`, `--monitor_metric`, and
  boolean-like `--finetune`;
- preprocessing: boolean-like `--normalize`, `--pcen`;
- binary: `--pos_weight`, `--conf_threshold`, `--temperature`;
- freezing: `--freeze_backbone {none,all,early,layer1,layer2,layer3}` and
  `--backbone_lr_ratio`;
- augmentation: `--use_specaug`, `--mixup_prob`, and `--mixup_alpha`.

The CLI defaults `epochs` to 5, while `TrainingConfig.epochs` defaults to 50;
when a config is supplied, the config value replaces the CLI default. A
config's `training.num_classes > 2` selects multiclass; binary mode uses
`num_classes == 2`. Training uses PyTorch Lightning and the source companion
constructs a GPU trainer with mixed precision, so do not promise a CPU
training run. `--ckpt_path` without `--finetune` tests an existing checkpoint;
with `--finetune` it resumes training. Both are explicit, potentially costly
operations and should be approved separately.

`ResNetClassifier` constructs an ImageNet-initialized torchvision backbone and
replaces its first convolution for the spectrogram channel count. A local
checkpoint does not necessarily eliminate the backbone-weight dependency.
Use an offline/cache-aware plan and stop if a constructor attempts an
unapproved download.

## Inference contract

The adapted `audio_inference.py` preserves these key flags and defaults:
`--config`, `--audios_source`, `--num_classes 2`, `--class_names`,
`--window_size_sec 5.0`, `--overlap_sec 4.0`, `--sample_rate 48000`,
`--n_fft 2048`, `--hop_length 512`, `--n_mels 224`, `--top_db 80.0`,
`--checkpoint`, `--device cuda`, `--batch_size 64`, `--num_workers 1`,
`--temperature 1.0`, `--dataset`, `--normalize`, `--spectrograms_path`, and
`--annotations_json`. It accepts an audio directory, a JSON list of window
records, or a CSV containing a spectrogram path column. `--dry-run` resolves
and validates arguments without reading audio, loading a checkpoint, or
writing results.

Binary output is sorted by descending confidence and has exactly
`audio,start(s),end(s),prediction,probability,confidence`. Multiclass output
has `file_path,audio,start(s),end(s),prediction`, followed by one
`<ClassName>_prob` per class; names with spaces become underscores. Use a
positive temperature to divide logits before sigmoid or softmax. The source
per-second helper is binary-only and writes
`per_second_results.csv` with weighted overlap columns; do not apply that
reducer to multiclass probabilities without defining a class-wise policy.
