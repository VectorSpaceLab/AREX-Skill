# Feature and matching workflows

## Match existing descriptor tensors

```python
import torch
from kornia.feature import match_mnn

desc1 = torch.rand(128, 64)
desc2 = torch.rand(96, 64)
dists, idxs = match_mnn(desc1, desc2)
if idxs.numel() == 0:
    raise RuntimeError("No mutual nearest-neighbor matches")
```

After matching, use `idxs[:, 0]` for the first descriptor/keypoint array and `idxs[:, 1]` for the second.

## Extract local features, then match

For image inputs, normalize layout and range before invoking feature modules.

```python
import torch
from kornia.feature import SIFTFeature, DescriptorMatcher

image = torch.rand(1, 1, 128, 128)  # grayscale BCHW
feature = SIFTFeature(num_features=256)
matcher = DescriptorMatcher("mnn")

lafs1, responses1, desc1 = feature(image)
lafs2, responses2, desc2 = feature(image)
dists, idxs = matcher(desc1[0], desc2[0])
```

When a feature extractor returns batched descriptors, index or reshape deliberately; matcher functions expect two-dimensional descriptor matrices.

## Use learned matchers without accidental downloads

- Prefer non-pretrained constructors or user-supplied checkpoint paths for smoke tests.
- If the user asks for `LoFTR("outdoor")`, `LoFTR("indoor")`, DISK, DeDoDe, or LightGlue pretrained behavior, state that weights may be downloaded or must exist in the framework cache.
- For environments without network access, validate the preprocessing and matching route with synthetic descriptors and leave pretrained quality as unverified.

## Handoff to geometry

Descriptor matchers identify correspondences; they do not solve camera geometry by themselves. Convert match indices to matched point arrays, then use the geometry route for homography, fundamental/essential matrix, PnP, triangulation, or warping.

```python
pts1_m = pts1[idxs[:, 0]]
pts2_m = pts2[idxs[:, 1]]
# Hand off to geometry-vision for robust estimation.
```

Record whether points are in pixel coordinates or normalized camera coordinates before handoff.

## Validation checklist

- Descriptor matrices have the same feature dimension `D`.
- Descriptors, LAFs, and images are on compatible devices and dtypes.
- Empty match results are handled before indexing.
- Optional weight/cache requirements are visible before constructing pretrained models.
- Match index columns are mapped to the correct source and destination feature sets.
