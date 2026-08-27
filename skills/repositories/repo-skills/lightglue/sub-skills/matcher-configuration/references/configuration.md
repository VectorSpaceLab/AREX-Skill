# Configuration decisions

`LightGlue(features="...", **conf)` merges caller configuration with matcher defaults, then applies feature-preset overrides when `features` is not `None`.

## Defaults

| Field | Default | Decision guidance |
|---|---:|---|
| `name` | `'lightglue'` | Interface label only. |
| `input_dim` | `256` | Descriptor input width. Presets overwrite it; for `features=None`, set it to `descriptors.shape[-1]`. |
| `descriptor_dim` | `256` | Internal transformer width. Must be divisible by `num_heads`; if different from `input_dim`, LightGlue inserts a learned linear projection. |
| `add_scale_ori` | `False` | Presets for SIFT and DoGHardNet set this `True` and require `scales` and `oris` in each feature dict. |
| `n_layers` | `9` | Maximum number of self+cross attention layers. Reducing it speeds inference but can reduce accuracy. |
| `num_heads` | `4` | Attention heads. Keep `descriptor_dim % num_heads == 0`. |
| `flash` | `True` | Allows FlashAttention / scaled-dot-product attention speed paths when available. Safe to leave on; warning means optional acceleration is missing. |
| `mp` | `False` | Enables CUDA autocast mixed precision around matcher forward. Use mainly on CUDA. |
| `depth_confidence` | `0.95` | Adaptive depth early stopping threshold. Lower values stop earlier more often; `-1` disables early stopping. |
| `width_confidence` | `0.99` | Adaptive width point-pruning threshold. Lower values prune earlier; `-1` disables point pruning. |
| `filter_threshold` | `0.1` | Final match confidence threshold. Higher gives fewer, stronger matches. |
| `weights` | `None` | Presets set pretrained LightGlue weight names and may download on first use. |

## Preset versus custom descriptors

- Use `LightGlue(features='superpoint'|'disk'|'aliked'|'sift'|'doghardnet')` for descriptors from those supported feature families. This selects descriptor width and pretrained matcher weights.
- Use `LightGlue(features=None, input_dim=D, ...)` for custom or synthetic descriptors. This avoids preset weight downloads by default, but also means there is no pretrained matching knowledge unless compatible weights are supplied by the installed package.
- If using SIFT or DoGHardNet presets, include `scales` and `oris`; those presets augment positional encoding with scale and orientation.

## Speed/accuracy recipes

### Maximum accuracy / deterministic full-depth matching

```python
matcher = LightGlue(
    features="superpoint",
    depth_confidence=-1,
    width_confidence=-1,
).eval().to(device)
```

Pair this with an extractor configuration that keeps all keypoints needed by the application. Disabling both adaptive mechanisms forces all configured layers and avoids point pruning. It does not prevent final filtering; tune `filter_threshold` separately.

### Faster adaptive matching

```python
matcher = LightGlue(
    features="superpoint",
    depth_confidence=0.9,
    width_confidence=0.95,
    flash=True,
).eval().to(device)
```

Lower `depth_confidence` stops at earlier layers more often. Lower `width_confidence` prunes more points earlier. Validate accuracy on the target data before adopting aggressive settings.

### CUDA-oriented fast path

```python
matcher = LightGlue(features="superpoint", flash=True, mp=True).eval().cuda()
```

`flash=True` uses PyTorch scaled-dot-product attention or `flash-attn` when available on CUDA. `mp=True` wraps forward in CUDA autocast and can improve speed/memory on compatible GPUs. Keep it off for CPU-only runs unless you have tested the runtime behavior.

## Adaptive depth

Adaptive depth is enabled when `depth_confidence > 0`. After each non-final layer, LightGlue estimates token confidence and stops when the confident-token ratio is greater than `depth_confidence`. The returned `stop` value reports how many layers were executed. Disable with `depth_confidence=-1` when exact full-depth behavior is preferred.

## Adaptive width and pruning thresholds

Adaptive width is enabled when `width_confidence > 0` and the current call is not using the compiled padded path. The matcher prunes points using per-layer matchability and confidence estimates.

Default minimum keypoint thresholds before pruning is attempted:

| Device/path | Threshold | Meaning |
|---|---:|---|
| `cpu` | `-1` | Any non-empty keypoint count is above this threshold. |
| `mps` | `-1` | Any non-empty keypoint count is above this threshold. |
| `cuda` without FlashAttention path | `1024` | Pruning is attempted only when the side has more than 1024 keypoints. |
| `cuda` with FlashAttention path | `1536` | Pruning is attempted only when the side has more than 1536 keypoints. |

To disable point pruning, set `width_confidence=-1`; do not rely on editing thresholds. A threshold of `-1` means the minimum-count gate is effectively removed, not that pruning is disabled.

## Final filtering

`filter_threshold` controls the final mutual-match acceptance threshold. The implementation keeps only mutual assignments whose confidence is strictly greater than the threshold.

- Increase it for fewer, cleaner correspondences.
- Decrease it when downstream geometry can reject outliers and more tentative matches are useful.
- Use `matches0`/`matches1` for dense per-keypoint mapping and `matches`/`scores` for compact accepted pairs.

## `compile()` behavior

`matcher.compile(mode='reduce-overhead', static_lengths=[256, 512, 768, 1024, 1280, 1536])` compiles the padded `masked_forward` of each transformer layer with `torch.compile` and records the static bucket lengths.

Operational consequences:

1. Call `compile()` after `matcher.eval().to(device)` and before repeated inference.
2. If the maximum side length `max(M, N)` is less than or equal to the largest `static_lengths` entry, descriptors and keypoints are padded to the next bucket and the compiled path is used.
3. Point pruning is disabled on compiled padded calls, even when `width_confidence > 0`; LightGlue warns that point pruning is partially disabled.
4. If `max(M, N)` is greater than the largest static length, the call falls back to eager execution and point pruning can run normally.
5. Adaptive depth remains supported for both compiled and eager paths.

Use `compile()` for repeated same-range inference where compile overhead is amortized. Avoid it for one-off calls, highly variable shapes, or cases where adaptive width pruning is more important than compile speed.
