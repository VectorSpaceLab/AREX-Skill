# Troubleshooting direct matcher calls

## `AssertionError: Missing key image0 in data` or `image1`

The top-level matcher input must be exactly a dict containing `image0` and `image1` entries:

```python
out = matcher({"image0": feats0, "image1": feats1})
```

Do not pass a single feature dictionary or a tuple of feature dictionaries.

## Descriptor dimension assertion

The matcher asserts:

```python
assert desc0.shape[-1] == matcher.conf.input_dim
assert desc1.shape[-1] == matcher.conf.input_dim
```

Fixes:

- For supported descriptors, choose the matching preset: `features='superpoint'` for 256-D SuperPoint, `features='disk'`, `'aliked'`, `'sift'`, or `'doghardnet'` for 128-D descriptors.
- For nonstandard precomputed descriptors, instantiate with `features=None, input_dim=D` where `D == descriptors.shape[-1]`.
- Remember that feature presets overwrite `input_dim`; `LightGlue(features='superpoint', input_dim=128)` still expects SuperPoint's preset dimension.

## Unsupported feature preset

`LightGlue(features='bad-name')` raises a value error. Valid matcher preset names are:

```text
superpoint, disk, aliked, raco-aliked, sift, doghardnet
```

Use `features=None` for custom descriptor families, with the untrained/custom-weight caveat from the API reference.

## Missing `image_size` versus `image` tensors

The matcher normalizes keypoints with `image_size` when present. Although extractor-produced dictionaries may carry an `image` tensor, the matcher implementation should not be treated as deriving size from `image` for direct precomputed calls.

Best practice for precomputed features:

```python
feats = {
    "keypoints": keypoints,      # [B, M, 2]
    "descriptors": descriptors,  # [B, M, D]
    "image_size": image_size,    # [B, 2] as width, height
}
```

If `image_size` is omitted, keypoints are normalized from their own coordinate extent. That can change matching behavior and can fail for empty keypoint tensors. Always pass `image_size` when creating feature dictionaries outside the packaged extractors.

## Missing `scales` or `oris` for SIFT/DoGHardNet

The SIFT and DoGHardNet matcher presets set `add_scale_ori=True`. Each image feature dict must include:

```python
"scales": scales,  # [B, M]
"oris": oris,      # [B, M]
```

If your precomputed SIFT-like descriptors do not have scale and orientation, either provide compatible values or use a custom `features=None` configuration with appropriate weights/expectations.

## Optional FlashAttention warning

When `flash=True` but neither an appropriate PyTorch scaled-dot-product attention path nor `flash-attn` is available, LightGlue warns that FlashAttention is unavailable. This is a speed/memory warning, not a correctness failure.

Fixes:

- Ignore it for CPU correctness checks.
- Set `flash=False` to silence optional acceleration warnings.
- Use a compatible PyTorch/CUDA environment or install optional FlashAttention only when speed work requires it.

## Mixed precision constraints

`mp=True` enables a CUDA autocast context inside matcher forward. Use it mainly for CUDA inference after moving the matcher and all input tensors to the same CUDA device.

Common fixes:

- CPU/MPS/default portability: keep `mp=False`.
- CUDA speed path: use `matcher = LightGlue(..., mp=True).eval().cuda()` and move every tensor in `image0` and `image1` to CUDA.
- If a downstream task needs exact reproducibility or full precision, compare with `mp=False`.

## `compile()` and pruning interaction

Calling `matcher.compile()` can emit:

```text
Point pruning is partially disabled for compiled forward.
```

This is expected when `width_confidence != -1`. For calls whose keypoint count fits the configured static buckets, LightGlue pads to a bucket and disables adaptive width pruning. Larger calls fall back to eager mode where pruning can run.

Choices:

- Want maximum accuracy and stable compiled full-depth-like behavior: set `width_confidence=-1` and optionally `depth_confidence=-1`.
- Want adaptive width pruning: avoid `compile()` or ensure your important large-keypoint cases fall outside compiled buckets.
- Want benchmark speed: test both compiled and eager configurations on representative keypoint counts.

## No keypoints in one or both images

If either side has zero keypoints, LightGlue returns no matches:

- `matches0` / `matches1` are filled with `-1` for existing keypoints.
- `matching_scores0` / `matching_scores1` are zeros.
- `matches` and `scores` are empty.

For empty-keypoint direct calls, still provide `image_size` and correctly shaped empty tensors such as `keypoints.shape == [B, 0, 2]` and `descriptors.shape == [B, 0, D]`. Without `image_size`, keypoint normalization cannot infer a size from empty tensors.

## Shape, batch, and device mismatches

All tensors in both feature dictionaries should share batch size `B`, device, and compatible dtype. Keypoints and descriptors must retain the batch dimension even for one image pair. If you remove the batch dimension for downstream indexing, do it after matching, not before direct matcher forward.

## First-use weight downloads fail offline

Preset matchers load feature-specific LightGlue weights on first use. Pretrained extractors can also download their own weights. For offline API validation, use `LightGlue(features=None, ...)` with synthetic descriptors. For production matching with presets, ensure the runtime has network access or a prepared weight cache before instantiating preset models.
