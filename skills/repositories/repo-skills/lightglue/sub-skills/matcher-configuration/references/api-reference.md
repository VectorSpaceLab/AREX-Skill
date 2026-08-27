# Direct matcher API reference

This reference is for calling `lightglue.LightGlue` directly on two feature dictionaries. It assumes feature extraction has already happened, or that the caller is deliberately using synthetic/precomputed descriptors.

## Public matcher signatures

```python
from lightglue import LightGlue

matcher = LightGlue(features="superpoint", **conf)
out = matcher({"image0": feats0, "image1": feats1})

# PyTorch 2.x compile helper; call after moving to eval/device.
matcher.compile(mode="reduce-overhead", static_lengths=[256, 512, 768, 1024, 1280, 1536])
```

`LightGlue` is a `torch.nn.Module`. Use normal PyTorch patterns:

```python
matcher = LightGlue(features="superpoint").eval().to(device)
with torch.inference_mode():
    out = matcher({"image0": feats0, "image1": feats1})
```

Feature-specific matchers and pretrained extractors can download weights on first use. `features=None` does not select or download a preset matcher weight unless a compatible weight is explicitly configured by the installed package.

## Feature presets

| `features` value | Descriptor input dim | Extra feature fields | Matcher weight name | Notes |
|---|---:|---|---|---|
| `'superpoint'` | 256 | none | `superpoint_lightglue` | Public `SuperPoint` extractor pairs with this preset. |
| `'disk'` | 128 | none | `disk_lightglue` | Public `DISK` extractor pairs with this preset. |
| `'aliked'` | 128 | none | `aliked_lightglue` | Public `ALIKED` extractor pairs with this preset. |
| `'raco-aliked'` | 128 | none | `raco_aliked_lightglue` | Matcher preset exists; extractor choice must produce compatible ALIKED-style descriptors. |
| `'sift'` | 128 | `scales`, `oris` | `sift_lightglue` | `add_scale_ori=True`; feature dicts must include scale and orientation tensors. |
| `'doghardnet'` | 128 | `scales`, `oris` | `doghardnet_lightglue` | `add_scale_ori=True`; feature dicts must include scale and orientation tensors. |
| `None` | `conf.input_dim` (default 256) | caller-defined; usually none | none by default | For precomputed/custom descriptors. Set `input_dim` to descriptor width. |

When `features` is not `None`, the preset overwrites `input_dim`, selected `weights`, and `add_scale_ori` where applicable. Passing `input_dim=...` while also using a preset will not change the preset descriptor dimension.

## Input dictionary schema

Top-level input:

```python
data = {
    "image0": feats0,
    "image1": feats1,
}
out = matcher(data)
```

Each feature dictionary should contain tensors on the same device as the matcher:

| Key | Shape | Required | Meaning |
|---|---:|---|---|
| `keypoints` | `[B, M, 2]` for `image0`, `[B, N, 2]` for `image1` | yes | Pixel-space keypoints in `(x, y)` order. Use floating point tensors. |
| `descriptors` | `[B, M, D]` / `[B, N, D]` | yes | Descriptor width `D` must equal `matcher.conf.input_dim`. |
| `image_size` | `[B, 2]` | strongly recommended | Image size in `(width, height)` order, used to normalize keypoints. Required for robust empty-keypoint handling. |
| `image` | `[B, C, H, W]` | optional carrier | Accepted in extractor-produced dicts, but the matcher implementation uses `image_size` when present. Do not rely on `image` as a substitute for `image_size`. |
| `scales` | `[B, M]` / `[B, N]` | SIFT/DoGHardNet only | Required when `matcher.conf.add_scale_ori=True`. |
| `oris` | `[B, M]` / `[B, N]` | SIFT/DoGHardNet only | Required when `matcher.conf.add_scale_ori=True`. |

Other extractor keys such as detection `scores` may be carried in the dict, but the matcher does not need them.

## Output dictionary schema

| Key | Shape / type | Interpretation |
|---|---|---|
| `matches0` | Long tensor `[B, M]` | Dense mapping from each keypoint in image0 to an index in image1, or `-1` if unmatched. |
| `matches1` | Long tensor `[B, N]` | Dense reverse mapping from each keypoint in image1 to an index in image0, or `-1` if unmatched. |
| `matching_scores0` | Tensor `[B, M]` | Confidence for each image0 keypoint match; zero where unmatched. |
| `matching_scores1` | Tensor `[B, N]` | Confidence for each image1 keypoint match; zero where unmatched. |
| `matches` | Usually list length `B` of long tensors `[Si, 2]` | Compact valid pairs `(index_in_image0, index_in_image1)`. With no keypoints, the implementation returns an empty batched tensor. |
| `scores` | Usually list length `B` of tensors `[Si]` | Compact scores aligned with `matches`. With no keypoints, the implementation returns an empty batched tensor. |
| `stop` | integer | Number of transformer layers actually executed; can be less than `n_layers` when adaptive depth stops early. |
| `prune0` | Tensor `[B, M]` | Per-keypoint layer-survival/pruning trace for image0. All entries equal `n_layers` when point pruning is disabled. |
| `prune1` | Tensor `[B, N]` | Per-keypoint layer-survival/pruning trace for image1. All entries equal `n_layers` when point pruning is disabled. |

`filter_threshold` is applied after mutual nearest assignment. Raising it gives fewer, stronger matches. The compact `matches` entries are remapped back to original keypoint indices even when adaptive width pruned points internally.

## Supported precomputed-descriptor patterns

### Supported extractor descriptors, already computed

If the descriptors come from a supported extractor, instantiate the matching preset even if extraction happened elsewhere:

```python
matcher = LightGlue(features="superpoint").eval().to(device)
out = matcher({"image0": feats0, "image1": feats1})
```

This selects the correct descriptor dimension and pretrained matcher weights. It may download the preset LightGlue weights on first use.

### Nonstandard or synthetic descriptors

Use `features=None` when descriptor width or semantics do not match a preset. Always set `input_dim` explicitly. Choose a `descriptor_dim` divisible by `num_heads`.

```python
import torch
from lightglue import LightGlue

B, M, N, D = 1, 6, 5, 8
device = "cpu"

torch.manual_seed(0)
kpts0 = torch.rand(B, M, 2, device=device) * torch.tensor([640.0, 480.0])
kpts1 = torch.rand(B, N, 2, device=device) * torch.tensor([640.0, 480.0])
desc0 = torch.randn(B, M, D, device=device)
desc1 = torch.randn(B, N, D, device=device)
size = torch.tensor([[640.0, 480.0]], device=device)

matcher = LightGlue(
    features=None,
    input_dim=D,
    descriptor_dim=8,
    n_layers=1,
    num_heads=2,
    flash=False,
    depth_confidence=-1,
    width_confidence=-1,
    filter_threshold=0.0,
).eval().to(device)

with torch.inference_mode():
    out = matcher({
        "image0": {"keypoints": kpts0, "descriptors": desc0, "image_size": size},
        "image1": {"keypoints": kpts1, "descriptors": desc1, "image_size": size},
    })

assert out["matches0"].shape == (B, M)
assert out["matches1"].shape == (B, N)
assert "matches" in out and "scores" in out
```

This pattern is deterministic for API validation, but it is not evidence of meaningful matching quality unless the installed package provides compatible trained weights for the custom descriptor family.
