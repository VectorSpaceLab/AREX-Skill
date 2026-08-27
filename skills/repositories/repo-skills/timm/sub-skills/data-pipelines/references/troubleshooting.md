# Data Pipeline Troubleshooting

## CPU-Only Loader Fails With CUDA Errors

Symptom: constructing or iterating a loader raises a CUDA/device error even though the model is on CPU.

Cause: `create_loader` and `create_naflex_loader` default `device=torch.device('cuda')` when `use_prefetcher=True`.

Fix one of these:

```python
loader = create_loader(dataset, **data_config, batch_size=8, device=torch.device('cpu'))
```

```python
loader = create_loader(dataset, **data_config, batch_size=8, use_prefetcher=False)
```

Also keep `img_dtype=torch.float32` for CPU unless the caller has verified lower-precision CPU support.

## Poor Accuracy or Different Logits Than Expected

Likely causes:

- Used generic `create_transform((3, 224, 224))` instead of a model-aligned `resolve_data_config` result.
- Overrode `input_size` but accidentally changed `mean`, `std`, `interpolation`, `crop_pct`, or `crop_mode`.
- Used train transforms for eval/inference or eval transforms for training.
- Enabled `tf_preprocessing` for a model that was not ported from a TF-style preprocessing recipe.
- Used `use_test_size=False` when the pretrained config has separate test-time size/crop settings needed for validation.

Debug with `scripts/data_config_probe.py --model MODEL_NAME` and compare the resolved config with the expected pretrained recipe.

## Dataset Root or Split Not Found

Checklist:

- For folder datasets, pass `root` as either the dataset root plus `split`, or the exact split directory with `search_split=False`.
- `search_split=True` searches direct child directories such as `train`, `training`, `val`, `valid`, `validation`, `eval`, and `evaluation`.
- `create_dataset(name='', root=..., split=...)` uses timm's `ImageDataset`; `create_dataset(name='torch/image_folder', ...)` uses TorchVision `ImageFolder`.
- For `torch/imagenet`, eval-like splits are mapped to `val` and `download` is not forwarded.
- For HF/TFDS/WDS readers, the split string may be interpreted by the backend reader, not by folder search.

## Class Map Errors

Common messages and fixes:

| Message | Likely fix |
| --- | --- |
| `Cannot locate specified class map file` | Use an absolute/working-directory path or put the file under dataset root |
| `Unsupported class map file extension` | Use `.txt` or `.pkl` only |
| `Invalid class map file, expected a dict` | Ensure pickle contains a plain `{class_name: index}` dict |
| Missing labels or wrong indices | Confirm dataset folder names/labels exactly match map keys |

A `.txt` class map is easiest to audit: one class name per line, zero-based line number as class index.

## Hugging Face Dataset Issues

For `hfds/...` and `hfids/...`:

- Pass `trust_remote_code=True` only when the dataset requires custom dataset code and the caller accepts that trust boundary.
- Use `download=True` where supported if the dataset is absent locally.
- For streaming/iterable datasets, set `batch_size`, `num_samples`, `seed`, and `repeats` intentionally.
- Check `input_key` and `target_key` if examples do not use default image/label column names.
- Avoid assuming `filename(index)` works for iterable datasets; use reader-supported filename listing if available.

## PIL, NumPy, and TorchVision Import Problems

Symptoms include import failures before any dataset is read, image open/convert errors, or transform construction failures.

Actions:

- Confirm Pillow is installed and can open the image formats in the dataset.
- Confirm TorchVision imports cleanly and matches the installed PyTorch version.
- Confirm NumPy is compatible with the current PyTorch/TorchVision stack.
- If transform construction fails around interpolation or antialias behavior, reduce to a minimal `create_transform(**resolve_data_config(model=model))` probe first.

## Prefetcher, Dtype, and Device Mismatches

The standard prefetcher changes where normalization and device transfer happen:

- With `use_prefetcher=True`, transforms avoid tensor conversion/normalization that the prefetcher handles later.
- `device` controls where images and targets are moved.
- `img_dtype` controls the image dtype after prefetching.
- Random erasing may run inside the prefetcher path for training.

If a downstream consumer expects CPU tensors already normalized by transforms, set `use_prefetcher=False`.

## Mixup / CutMix Problems

- Standard `Mixup` is applied after batches are produced; `FastCollateMixup` is used as a collate function in fast prefetch paths.
- Do not combine collate-time mixup with augmentation split modes unless the training script explicitly supports it.
- When mixup is active, labels become soft targets; use a compatible loss from the training-workflows sub-skill.
- `mixup_off_epoch` style behavior toggles `mixup_enabled` on the loader/collate function or mixup object; it is not a dataset setting.

## Random Erasing Surprises

- `re_prob=0` fully disables random erasing.
- `re_split=True` erases only part of a batch when augmentation splits are in use.
- With a prefetcher, random erasing happens after data transfer and normalization choices differ from pure transform paths.
- NaFlex uses patch-level random erasing in its loader/prefetch path.

## NaFlex Model/Loader Mismatch

Symptoms: model forward rejects dict inputs, missing patch metadata, shape mismatch in patch tensors, or assertions around sequence length.

Checklist:

- Confirm the model is NaFlex-compatible or was created with the appropriate model-library option.
- Use `create_naflex_loader` rather than `create_loader` for loader-managed NaFlex batches.
- Align `patch_size` with the model's patch size when available.
- Align `max_seq_len` with the validation/eval setting expected by the model or checkpoint.
- Use `patchify_channels_last=True` unless the target model path expects channels-first flat patches.
- Do not use iterable datasets with NaFlex training mode; the wrapper asserts that iterable support is WIP.
- If using `patch_size_choices`, provide matching `patch_size_choice_probs` length or omit probabilities.

## Non-Default Input Size Mismatch

When adapting a pretrained model to a new image size:

1. Override only `input_size` or `img_size` in `resolve_data_config(args=..., model=model)`.
2. Keep pretrained `mean`, `std`, `interpolation`, `crop_pct`, and `crop_mode` unless the new recipe demands otherwise.
3. For ViT-like models, confirm positional embedding or dynamic image-size handling in the model-library sub-skill.
4. Rebuild transforms and loaders after changing config; `create_loader` mutates `dataset.transform`.

## Loader Appears to Ignore a Transform

`create_loader` assigns `dataset.transform = create_transform(...)`. If a dataset already had a transform, it is replaced. Build custom transforms after loader creation only if you intentionally override timm's pipeline, or pass `use_prefetcher` and transform args so timm creates the intended path.
