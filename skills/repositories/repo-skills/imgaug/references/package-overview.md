# imgaug package overview

Read this reference when routing a task or deciding which part of the package owns a behavior.

## Package contract

`imgaug` 0.4.0 is a CPU-oriented NumPy image-augmentation library. Its public import surface re-exports core helpers, augmentables, augmenters, parameter distributions, dtype helpers, and bundled sample data:

```python
import imgaug as ia
import imgaug.augmenters as iaa
import imgaug.parameters as iap
```

The package accepts image arrays or lists of arrays and can transform images together with keypoints, bounding boxes, polygons, line strings, heatmaps, and segmentation maps. It also provides batch normalization and multiprocessing helpers.

## Compatibility and install facts

- The package metadata declares `numpy>=1.15`, SciPy, Pillow, Matplotlib, scikit-image, OpenCV, imageio, Shapely, and six.
- Current NumPy 2.x removes `np.sctypes`, which imgaug 0.4.0 reads during import. Use `numpy<2` for this release.
- OpenCV packages are alternatives. A headless installation is appropriate for servers and CI: `opencv-python-headless<4.12` is a conservative current choice with NumPy 1.x.
- `numba` is optional in the implementation; segmentation and corruption-like paths have a NumPy/Python fallback when it is absent.
- `imagecorruptions` is optional and only needed for the `imgcorruptlike` augmentation family/tests.
- There is no package CLI or required accelerator backend. Installation and API smoke checks are the primary health checks.

## Public surface map

| Surface | Main modules | Use it for |
| --- | --- | --- |
| Pipeline composition and augmenters | `imgaug.augmenters`, especially `meta`, `geometric`, `size`, `arithmetic`, `blur`, `color`, `contrast`, `blend`, `segmentation`, `weather`, `pillike` | Transform images and aligned data. |
| Coordinate augmentables | `imgaug.augmentables.kps`, `bbs`, `polys`, `lines` | Keypoints, boxes, polygons, and line strings with image shape metadata. |
| Dense augmentables | `imgaug.augmentables.heatmaps`, `segmaps` | Continuous heatmaps and categorical segmentation maps at matching or lower resolution. |
| Batch normalization | `imgaug.augmentables.batches`, `normalization` | Convert flexible Python inputs into normalized `Batch` objects and restore output types. |
| Randomness and distributions | `imgaug.random`, `imgaug.parameters` | Reproducible sampling, tuple/list shortcuts, and composed distributions. |
| Dtype and array helpers | `imgaug.dtypes`, `imgaug.imgaug` | Range-aware conversion, resize/pooling, grids, drawing, and hooks. |
| Example data | `imgaug.data` | Quokka image and aligned heatmap/segmentation/keypoint/box/polygon fixtures. |
| Background execution | `imgaug.multicore`, `Augmenter.pool`, `Augmenter.augment_batches` | Process or thread-backed batch augmentation. |

## Source-artifact replacement map

The runtime skill intentionally replaces repository-bound examples and checks with bundled helpers:

| Source artifact concept | Bundled replacement |
| --- | --- |
| README/check examples for simple image and aligned-data augmentation | `scripts/smoke_imgaug_workflows.py` |
| Manual visual augmenter catalogue | `sub-skills/augmentation-pipelines/scripts/generate_augmentation_contact_sheet.py` |
| Manual background/pool checks | `sub-skills/multicore-and-diagnostics/scripts/tiny_multicore_smoke.py` |
| Parameter/data/dtype check snippets | `sub-skills/parameters-random-and-utilities/scripts/smoke_parameters_and_data.py` |
| Annotation construction and shape checks | `sub-skills/augmentables-and-batches/scripts/smoke_aligned_augmentables.py` |

The original repository's test suite remains ground-truth evidence, not a runtime dependency of this skill. Use focused native tests only during separate skill verification.
