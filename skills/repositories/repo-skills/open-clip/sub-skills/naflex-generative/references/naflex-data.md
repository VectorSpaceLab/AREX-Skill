# NaFlex Data, Flags, and Patch Batches

## Main-Branch Context

The current open_clip main branch uses the post-refactor training stack by default: `TrainingTask` wrappers, dict-based batches, FSDP2 support, NaFlex image/audio pipelines, and torch.compile strategies. NaFlex is experimental and opt-in for variable-resolution/aspect image towers, variable-duration audio, and generative GenLIP/GenLAP models.

## CLI Flags

Use these flags when building or explaining NaFlex training/eval commands:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--use-naflex` | Enable NaFlex WebDataset/CSV train batching and NaFlex patchified validation/zero-shot loaders. | Also sets `aug_cfg.use_timm=True` and `aug_cfg.naflex=True`; for ordinary image models it implies `force_naflex_vision`. |
| `--force-naflex-vision` | Convert a compatible dense native/timm vision tower to NaFlex without enabling the data pipeline. | Useful for model construction/conversion checks; not the same as `--use-naflex`. |
| `--naflex-num-train-image-tokens` | Build the training schedule from total image tokens instead of sample count. | Mutually exclusive with `--train-num-samples` for WebDataset NaFlex train. Ignored unless `--use-naflex` is set. |
| `--naflex-patch-sizes` | Patch sizes sampled during train. | Eval uses the first value unless an explicit eval config overrides. Defaults to `16` when omitted. |
| `--naflex-patch-size-probs` | Sampling probabilities for patch sizes. | Must match patch-size count, be non-negative, and sum positive; normalized internally. |
| `--naflex-seq-lens` | Per-batch image/audio sequence-length buckets. | Defaults to `128 256 576 784 1024`; eval uses the largest train length unless a model eval length is supplied. |
| `--naflex-seq-len-probs` | Sampling weights for sequence-length buckets. | Must match sequence-length count/order, be non-negative, and sum positive; weights are per batch, not per sample. |
| `--naflex-max-tokens-per-batch` | Local batch token budget. | Image-only counts image tokens; GenLIP adds caption cap to each row cost. Default is `4096 * 4`. |
| `--naflex-max-text-tokens` | GenLIP caption token cap and row-cost component. | Defaults to model `text_cfg.context_length` when omitted. It truncates captions and affects batch sizing. |
| `--naflex-batch-divisor` | Divisibility constraint for scheduled batch sizes. | Default `8`; must be positive. |
| `--naflex-loss-scale` | Scale NaFlex loss by actual batch size vs `--batch-size`. | Choices: `none`, `linear`, `sqrt`. Only applies to dict NaFlex batches. |
| `--length-bucketing` | Reorder train stream by sequence length to reduce padding. | GenLIP keys on caption length; GenLAP keys on audio+caption; NaFlexCLAP keys on audio. |
| `--naflex-pad-multiple` | NaFlex audio padding multiple. | Bounds audio patch shape variety for compile; must be positive when set. |
| `--text-pad-multiple` | Variable-text padding multiple. | Bounds caption shape variety for compile; must be positive when set. |

Parser side effects:

- Model names containing `genlip` set `args.genlip=True`, force `args.use_naflex=True`, and reject `--accum-freq > 1`.
- Model names containing `genlap` set `args.genlap=True`, force `args.use_naflex=True`, and reject `--accum-freq > 1`.
- Model names containing `naflexclap` set `args.naflexclap=True` and force `args.use_naflex=True`.
- `args.use_naflex` sets `args.force_naflex_vision = not (args.genlip or args.genlap or args.naflexclap)` and injects NaFlex timm augmentation flags.

## `NaFlexDataConfig`

`NaFlexDataConfig.resolve(...)` normalizes and validates the schedule:

- `train_patch_sizes`: tuple of `(height, width)` patch-size pairs; non-empty and positive.
- `train_patch_size_probs`: optional normalized probability tuple; same length as patch sizes.
- `train_seq_lens`: tuple of positive sequence lengths; default `(128, 256, 576, 784, 1024)`.
- `train_seq_len_probs`: optional normalized probability tuple; aligned to user-supplied `train_seq_lens`, then preserved after scheduler sorting.
- `train_num_image_tokens`: optional positive total image-token target for train schedule creation.
- `max_tokens_per_batch`: positive local token budget; default `16384`.
- `batch_divisor`: positive scheduled batch-size divisor; default `8`.
- `eval_patch_size`: explicit eval patch size or first train patch size.
- `eval_seq_len`: explicit eval sequence length, model eval length from `create_naflex_data_config_from_args`, or max train sequence length.

Validation failures to surface clearly:

- Empty or non-positive patch sizes: `NaFlex patch sizes must contain at least one value` / `must be positive`.
- Empty or non-positive sequence lengths: `NaFlex sequence lengths must contain at least one value` / `must be positive`.
- Probability length mismatch: `must match patch sizes length` or `must match seq-lens length`.
- Negative probabilities or zero probability sum: `must be non-negative` / `must sum to a positive value`.
- Non-positive token budgets, batch divisors, eval patch sizes, or eval sequence lengths.

`create_naflex_data_config_from_args(args, default_patch_size=None, default_eval_seq_len=None)` reads parser-style attributes and uses model-derived defaults when available. If `args.naflex_patch_sizes` is missing and `default_patch_size` is provided, that model patch size becomes the train/eval patch size. If `args.naflex_seq_lens` is missing and `default_eval_seq_len` is provided, the train sequence defaults remain `(128, 256, 576, 784, 1024)` while eval uses the model length.

## Image Patch Dict Contract

NaFlex image transforms and batchers emit dictionaries instead of dense image tensors:

```python
{
    "patches": FloatTensor[B, N, C * patch_h * patch_w],
    "patch_coord": LongTensor[B, N, 2],  # image coordinates (h, w)
    "patch_valid": BoolTensor[B, N],
    "seq_len": Optional[int],            # present in scheduled train batches
}
```

Single-sample eval transforms emit the same keys without batch dimension and without `seq_len`. `collate_naflex_tuples` and `collate_naflex_dicts` pad/crop to the requested max sequence length.

Use these schemas when debugging downstream code:

- Contrastive NaFlex CLIP still accepts dense image tensors through the model forward for compatibility, but dataloaders under `--use-naflex` emit patch dicts.
- `NaFlexBatcher` returns dict batches such as `{"image": patch_dict, "text": text}`.
- `patch_valid` marks real patches; padding remains in `patches` and must be masked.
- Distributed schedules may pad scheduled steps/samples to rank or worker counts. Do not equate raw dataset rows with final scheduled rows without checking `num_batches`/`num_samples`.

## Audio Patch Dict Contract

NaFlex audio uses the same shape idea under `audio`:

```python
{
    "patches": FloatTensor[B, N, in_chans * patch_freq * patch_time],
    "patch_coord": LongTensor[B, N, 2],  # (freq_idx, time_idx)
    "patch_valid": BoolTensor[B, N],
}
```

`AudioNaFlexCfg` controls mel extraction and patch geometry:

- `sample_rate`, `window_size`, `hop_size`, `fmin`, `fmax`, `n_mels` mirror CLAP mel fields.
- `patch_freq` and `patch_time` define spectrogram patch geometry.
- `patch_freq == n_mels` yields full-height strips and a 1-D time sequence.
- `patch_freq < n_mels` yields multi-row `(freq, time)` patches for 2-D axial/MRoPE layouts.
- `patch_pad_mode` controls final partial time patch fill: `floor`, `silence`, or `repeat`.

Audio patchification rounds time up to a whole patch count and keeps at least one patch for very short clips. If `max_audio_tokens` is set, it caps by whole time columns so all frequency rows remain intact.

## Eval Transform Requirements

`create_naflex_eval_transform(transform_factory, config)` requires the transform factory to declare `is_naflex_eval_transform_factory`. The common route is `create_model_and_transforms(..., aug_cfg={"use_timm": True, "naflex": True})` or CLI `--use-naflex`.

If the factory is dense/non-NaFlex, the helper raises:

```text
NaFlex eval requires `--aug-cfg use_timm=True naflex=True`.
```

If timm does not provide NaFlex data support, `require_naflex()` raises a clear runtime error asking for `timm>=1.0.16` or a recent timm main checkout.

## Variable Text

Variable text pads captions to each batch max and emits `text_valid`:

```python
{"image": patch_dict, "text": text_ids, "text_valid": text_ids != pad_id}
```

Important caveats:

- GenLIP and GenLAP always need variable caption handling because their LM loss masks padded caption positions.
- `text_valid` is required when captions are padded/truncated in ways that cannot be inferred reliably by the model caller.
- Variable text requires a tokenizer with a reserved `pad_token_id`; the code fails fast when one is absent.
- `--text-pad-multiple` can round caption length up to reduce distinct compile shapes, but it must be positive.

## Loss Scaling

`get_naflex_loss_scale(batch, args, task)` only scales NaFlex dict batches. Dense image tensors return `1.0` regardless of `--naflex-loss-scale`.

- `none`: `1.0`.
- `linear`: `actual_local_batch_size / args.batch_size`.
- `sqrt`: square root of the linear ratio.

Use loss scaling only when the training design intentionally wants token-budget batches to preserve a chosen loss magnitude as row counts vary. Otherwise leave `none`.

## Safe Config Check

Use the bundled validator before running expensive jobs:

```bash
python scripts/naflex_config_report.py \
  --patch-sizes 16 32 \
  --seq-lens 128 256 576 \
  --max-tokens-per-batch 16384 \
  --batch-divisor 8 \
  --loss-scale sqrt
```

The script validates values and reports normalized config/schedule estimates without importing open_clip, timm, torch, or loading data.
