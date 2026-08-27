---
name: scikit-image
description: "Route scikit-image tasks across image I/O, enhancement, analysis,
  segmentation, geometric transforms, and registration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# scikit-image

Use this repo skill for user-facing image-processing work with the `scikit-image` distribution and its stable `skimage` namespace. It routes tasks by workflow rather than by source module. The experimental `skimage2` namespace is not a separate route; read `references/experimental-api.md` before using it.

## Start here

For a normal runtime installation:

```bash
python -m pip install scikit-image
python -c "import skimage; print(skimage.__version__)"
```

When working from a source checkout, follow that checkout's build instructions instead of assuming an editable pure-Python install; scikit-image contains compiled extensions. Read `references/troubleshooting.md` for import/build failures, optional dependencies, dtype/range mistakes, channel-axis errors, and data-download issues. Read `references/repo-provenance.md` before deciding whether this skill is stale for a newer checkout or release.

For a safe import and temporary image round-trip check, run from this skill directory:

```bash
python sub-skills/data-io/scripts/check_install.py
```

## Route by task

| User task | Read |
| --- | --- |
| Load or save images; use bundled sample data; manage collections or multi-frame images; convert dtypes/ranges; reason about NumPy image shape and channel conventions | `sub-skills/data-io/SKILL.md` |
| Convert color spaces; adjust exposure or contrast; filter, threshold, denoise, restore, deblur, inpaint, unwrap phase, or remove backgrounds | `sub-skills/enhancement/SKILL.md` |
| Detect and match features; measure labeled regions; trace contours or surfaces; extract line profiles; compare images, masks, or segmentations with metrics | `sub-skills/analysis/SKILL.md` |
| Draw masks or shapes; apply morphology; create or clean labels; run watershed, random walker, superpixels, graph segmentation, or active contours | `sub-skills/segmentation-and-shapes/SKILL.md` |
| Resize, rotate, rescale, warp, or build pyramids; estimate geometric transforms; use Radon/Hough helpers; register images or estimate optical flow | `sub-skills/transform-registration/SKILL.md` |

## Common routing decisions

- Route by the task's requested output, not merely by the first function imported.
- Loading and dtype conversion start in `data-io`; route onward once the image is a well-formed NumPy array.
- Threshold selection is enhancement. Turning a thresholded mask into objects, labels, boundaries, or segments is segmentation.
- Creating labels is segmentation. Measuring existing labels with `regionprops` or segmentation metrics is analysis.
- Detecting keypoints and matching descriptors is analysis. Estimating or applying a geometric transform from the matched coordinates is transform/registration.
- Appearance-changing operations belong to enhancement; coordinate- or geometry-changing operations belong to transform/registration.
- A pipeline may cross routes. Read the relevant leaves in execution order instead of forcing the whole workflow into one sub-skill.

## Package-wide rules

1. Inspect an image's `shape`, `dtype`, value range, and channel layout before processing it.
2. Use an explicit `channel_axis` whenever an API offers it; use `None` for grayscale or scalar images.
3. Do not use a bare `astype` when the intent is image-range conversion. Use `skimage.util.img_as_*` and preserve the intended numeric semantics.
4. Pass `preserve_range=True` when an operation must retain native intensity units and the API supports it.
5. Use nearest-neighbor interpolation (`order=0`) for masks or labels unless interpolation of class IDs is explicitly intended.
6. Pass physical `spacing` where measurements or 3-D geometry must use real-world units.
7. Prefer tiny local arrays or bundled data for smoke checks. Network downloads, GUI behavior, and optional solvers should be treated as separate environment concerns.
8. Prefer the stable `skimage` namespace for production work. `skimage2` is experimental, can change without notice, and may differ in signatures or behavior.

## Cross-route pipeline

A typical multi-stage workflow is:

1. `data-io`: load an image and normalize its array representation.
2. `enhancement`: convert color, denoise, adjust exposure, or choose a threshold.
3. `segmentation-and-shapes`: create masks and labels or partition the image.
4. `analysis`: compute region properties, features, contours, or quality metrics.
5. `transform-registration`: align images or apply a coordinate transform when geometry is involved.

Only read the stages needed by the task. Each leaf contains focused workflows and troubleshooting guidance.

## Root references and bundled helper

- `references/troubleshooting.md` — package-wide install, import, compiled-extension, dtype/range, channel-axis, optional-dependency, and data issues.
- `references/experimental-api.md` — the `skimage2` status, safe routing, and migration cautions.
- `references/repo-provenance.md` — source snapshot and refresh baseline.
- `sub-skills/data-io/scripts/check_install.py` — safe import and local temporary-file smoke helper.

## Scope boundaries

This skill covers public runtime image-processing workflows. It does not cover repository release engineering, CI configuration, benchmarks, Cython/Meson maintainer internals, gallery generation, or domain-specific computer-vision models outside scikit-image. Optional external packages and interactive viewers are supported only as dependencies of a routed workflow, not as independent skill areas.
