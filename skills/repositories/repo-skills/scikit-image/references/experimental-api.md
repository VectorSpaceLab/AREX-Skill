# Experimental `skimage2` API

## Status in this skill snapshot

The public `skimage` namespace is the stable runtime surface covered by this skill. The source snapshot also contains `skimage2`, an opt-in experimental v2 namespace. Its API reference states that it is subject to change without notice, and importing it can emit a warning that it is unstable.

Do not silently replace `skimage` imports with `skimage2` in production code. Treat a `skimage2` request as a version-specific migration or evaluation task and verify the installed API directly.

## How to route `skimage2` questions

`skimage2` does not need a separate leaf because the user workflow still determines the right guidance:

| Task | Route |
| --- | --- |
| Sample data, image files, array conventions, dtype/range conversion | `../sub-skills/data-io/SKILL.md` |
| Color, exposure, filtering, thresholding, denoising, restoration | `../sub-skills/enhancement/SKILL.md` |
| Features, measurements, contours, surfaces, metrics | `../sub-skills/analysis/SKILL.md` |
| Drawing, masks, morphology, labels, segmentation, region graphs | `../sub-skills/segmentation-and-shapes/SKILL.md` |
| Geometric transforms, warps, pyramids, registration, optical flow | `../sub-skills/transform-registration/SKILL.md` |

Use the routed leaf for conceptual and workflow guidance, but confirm every `skimage2` import path, signature, default, return value, and warning against the active environment.

## Safe evaluation procedure

1. Record the installed distribution and interpreter:

   ```bash
   python -c "import sys, skimage; print(sys.executable); print(skimage.__version__)"
   ```

2. Import `skimage2` without suppressing warnings. Capture the warning as compatibility evidence.
3. Inspect the exact live object rather than assuming a stable-namespace signature:

   ```python
   import inspect
   import skimage2

   # Import the specific public function, then inspect it.
   print(inspect.signature(function))
   print(function.__module__)
   ```

4. Reproduce behavior with a tiny array or bundled input.
5. If migrating, run the stable and experimental calls side by side and compare shape, dtype, range, return structure, and warnings.
6. Pin the tested scikit-image version if experimental behavior is required by deployed code.

## Migration cautions

- Matching function names do not guarantee matching parameters, defaults, range rules, or return values.
- Experimental functions may be missing even when their stable counterparts exist.
- The source tree may implement experimental functionality internally under `_skimage2`; this is a private implementation namespace, not a user-facing import contract.
- Backend dispatch support documented for `skimage` does not imply equivalent support for `skimage2`.
- A warning-free stable call and a warning-producing experimental call are not interchangeable merely because their numeric output matches on one sample.
- Do not write compatibility code that imports `_skimage2` directly or depends on its file layout.

## When to fall back to `skimage`

Prefer the stable namespace when the user needs production reliability, published API compatibility, third-party ecosystem support, or a solution that should survive routine upgrades. Use `skimage2` only when the user explicitly requests the experimental API, is testing migration behavior, or needs a feature confirmed to exist only there.

If the experimental import or call fails, first determine whether the task can be completed with the corresponding stable `skimage` route. If exact experimental behavior is mandatory, report the tested version and failure instead of inventing a compatibility mapping.
