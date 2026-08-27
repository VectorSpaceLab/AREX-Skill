---
name: image-preprocessing
description: "Use TIAToolbox for tissue masking, stain
  normalization/extraction/augmentation, patch extraction, tile pyramids, and
  preprocessing validation before inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Image Preprocessing

Use this sub-skill when a task needs to prepare pathology images or WSIs before analysis: build tissue masks, normalize stain appearance, augment stain variation, extract fixed or point-centered patches, generate tile pyramids, or validate preprocessing choices before model inference.

## Route Here For

- Tissue mask generation with `OtsuTissueMasker`, `MorphologicalMasker`, or the `tissue-mask` command.
- Stain normalization with `get_normalizer(...)`, custom stain matrices, target images, or the `stain-norm` command.
- Stain extraction and augmentation with `RuifrokExtractor`, `MacenkoExtractor`, `VahadaneExtractor`, `CustomExtractor`, and `StainAugmentor`.
- Patch extraction from arrays, image files, WSI readers, masks, annotation stores, points, or sliding windows.
- Tile pyramid generation with `TilePyramidGenerator`, `ZoomifyGenerator`, and `AnnotationTileGenerator`.
- Lightweight sanity checks for preprocessing parameters before starting expensive model inference.

## Route Elsewhere

- Use `wsi-io` for WSI opening, metadata, slide dimensions, thumbnails, `read_rect`, `read_bounds`, and coordinate-space questions.
- Use `model-inference` for patch prediction, semantic segmentation, nucleus detection, feature extraction, and inference engine batching.
- Use `cli-and-configuration` for complete CLI syntax, shared Click options, file discovery behavior, logging flags, and command orchestration.

## References

- `references/api-reference.md` summarizes APIs, required arguments, defaults, and decision points.
- `references/workflows.md` gives copyable recipes for masks, stain workflows, patches, pyramids, and preprocessing validation.
- `references/troubleshooting.md` maps common preprocessing failures to concrete checks and fixes.
- `scripts/preprocessing_smoke.py` provides tiny in-memory checks for importability, maskers, patch coordinates/filtering, stain normalizer construction, and stain augmentor construction.

## Fast Start

```python
import numpy as np
from tiatoolbox.tools.tissuemask import MorphologicalMasker
from tiatoolbox.tools.stainnorm import get_normalizer
from tiatoolbox.tools.patchextraction import get_patch_extractor

thumbnail = np.zeros((1, 128, 128, 3), dtype=np.uint8)
thumbnail[:, 24:96, 24:96] = [120, 45, 90]
mask = MorphologicalMasker(kernel_size=3).fit_transform(thumbnail)[0]

normalizer = get_normalizer("reinhard")
normalizer.fit(thumbnail[0])
normalized = normalizer.transform(thumbnail[0])

extractor = get_patch_extractor(
    "slidingwindow",
    input_img=normalized,
    patch_size=(32, 32),
    stride=(32, 32),
    input_mask=mask,
    min_mask_ratio=0.1,
)
patches = list(extractor)
```

Before running a model, confirm that image and mask resolutions align, `patch_size` and `stride` are intentional, stain normalization has a fitted target, and patch counts are plausible for the tissue area.
