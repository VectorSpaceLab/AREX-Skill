---
name: features-and-matching
description: "Use when extracting Kornia local features, descriptors, LAFs,
  learned matchers, or descriptor correspondences."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kornia features and matching

Use this sub-skill for local feature detectors/descriptors, local affine frames (LAFs), descriptor matching, learned matching models, and the handoff from correspondences to geometry.

## Read first

- Read `references/api-reference.md` to choose between classical descriptors, learned feature modules, and matcher APIs.
- Read `references/matching-outputs.md` before interpreting distance tensors, index pairs, empty matches, or thresholded matching results.
- Read `references/workflows.md` for descriptor matching, learned matcher, and geometry-handoff recipes.
- Read `references/troubleshooting.md` when pretrained weights, optional dependencies, descriptor shapes, or CUDA/half precision fail.
- Run `scripts/matching_smoke.py` for a no-download descriptor matching check.

## Scope

This route owns:

- Detector/response APIs such as Harris, GFTT, Hessian, DoG, scale-space detectors, KeyNet, and local feature wrappers.
- Descriptor APIs such as SIFT, DenseSIFT, HardNet, HyNet, TFeat, SOSNet, MKD, and LAF descriptors.
- LAF utilities for center/scale/orientation, normalization, orientation, affine shape, patches, and boundary conversion.
- Matching APIs: `match_nn`, `match_mnn`, `match_snn`, `match_smnn`, `match_fginn`, `match_adalam`, `DescriptorMatcher`, `GeometryAwareDescriptorMatcher`, `LocalFeatureMatcher`, and steered matchers.
- Learned feature/matching modules including DISK, DeDoDe, ALIKED, XFeat, LoFTR, LightGlue, and ONNX LightGlue when optional dependencies are installed.

Route elsewhere:

- Homography estimation, camera geometry, pose, epipolar, depth, and warping after matches are selected: `../geometry-vision/SKILL.md`.
- General model deployment, ONNX chains, or model-builder questions: `../models-and-deployment/SKILL.md`.
- Image preprocessing before extracting features: `../image-processing/SKILL.md`.

## Operating workflow

1. Decide whether the user needs deterministic tensor matching or a learned/pretrained model.
   - For known descriptors already in tensors, use `match_nn`/`match_mnn`/`DescriptorMatcher` first.
   - For image-to-image learned correspondences, check whether the model can run without downloads; do not trigger pretrained weight downloads by default.
2. Validate tensor contracts before matching.
   - Descriptor tensors use shape `(N, D)` for one image or feature set.
   - Matching outputs are distances `(M, 1)` and long index pairs `(M, 2)` unless the chosen API documents a richer structure.
3. Handle no-match cases explicitly. Thresholded matchers can return zero rows; this is a valid result, not necessarily an exception.
4. Only hand off to geometry after you know which source and destination keypoints correspond to each index column.
5. Keep optional dependency and weight-cache requirements visible in the plan or final answer.

## Common workflows

- Extract descriptors or LAFs from a grayscale or feature-ready tensor, then match them with `match_nn` or `match_mnn` first.
- Use learned matchers only when the task explicitly needs them and the required weights/cache are available or authorized.
- Convert match indices into matched point arrays before handing the result to geometry.
- Treat empty outputs as a valid thresholded result rather than a failure.

## Pitfalls

- The most common bug is swapping the two index columns or treating distances as scores without checking the matcher contract.
- Another common issue is trying to run pretrained LoFTR/LightGlue/DISK/DeDoDe paths in a no-network environment.
- If a downstream geometry step fails, the problem may be the point order or coordinate system, not the matcher itself.

## Quick validation habits

- Match on the simplest descriptor pair first; only move to learned matchers if the task truly needs them.
- Keep LAF and keypoint tensors on the same device and dtype as the descriptors.
- Treat no-match output as a valid branch, not an exception to hide.
- Convert matches into point arrays immediately before the geometry handoff so the index mapping stays obvious.

## Quick validation habits

- Start with a deterministic tensor matcher before trying learned matchers.
- If a learned matcher is involved, state the weight/cache requirement before you hand the task back.

## Quick smoke

```bash
python scripts/matching_smoke.py --device auto
```

Expected terminal signal: `matching-smoke-ok`.

## Native evidence candidates

Future verification can target descriptor matching, LAF, SIFT descriptor, and local-feature tests. Pretrained LoFTR, LightGlue, DISK, DeDoDe, or model-weight cases are optional and should be marked network/cache/slow unless explicitly requested.
