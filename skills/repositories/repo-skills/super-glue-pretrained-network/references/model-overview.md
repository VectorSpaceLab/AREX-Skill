# Model Overview

## What the repository provides

SuperGluePretrainedNetwork combines:

1. **SuperPoint**: a detector and descriptor that extracts sparse local image features from grayscale images.
2. **SuperGlue**: a graph neural network plus optimal transport matching layer that matches two sets of local features.
3. **Matching**: a convenience frontend that runs SuperPoint on each image when keypoints/descriptors are not already supplied, then runs SuperGlue.

The release ships three checkpoint files:

| File | Role |
| --- | --- |
| `models/weights/superpoint_v1.pth` | SuperPoint detector/descriptor weights |
| `models/weights/superglue_indoor.pth` | SuperGlue weights trained for indoor/ScanNet-like scenes |
| `models/weights/superglue_outdoor.pth` | SuperGlue weights trained for outdoor/MegaDepth-like scenes |

## Data flow

```text
grayscale image0, image1
        |
        v
SuperPoint -> keypoints, scores, descriptors for each image
        |
        v
SuperGlue -> mutual matches and matching confidence
        |
        v
match visualizations, .npz outputs, or pose-evaluation metrics
```

`Matching.forward(data)` accepts at least `image0` and `image1`. If the feature keys are missing, it runs SuperPoint internally. It then returns both feature outputs and SuperGlue outputs.

## Input conventions

- Images are processed as grayscale.
- Tensor inputs should be float tensors in `[0, 1]` with shape `1x1xHxW` for the common single-pair path.
- The utilities resize images before inference. Resize can be exact width/height, max-dimension only, or disabled with `-1`.
- Very small resolutions can lose useful features; very large resolutions increase runtime and memory.

## Matching outputs

The core matching outputs are:

| Output | Meaning |
| --- | --- |
| `keypoints0`, `keypoints1` | Detected keypoints in `(x, y)` pixel coordinates |
| `scores0`, `scores1` | SuperPoint confidence scores |
| `descriptors0`, `descriptors1` | SuperPoint descriptors |
| `matches0`, `matches1` | Matched keypoint indices, with `-1` for unmatched points |
| `matching_scores0`, `matching_scores1` | Match confidence values, zero for unmatched points |

For `matches0`, `matches0[i] = j` means keypoint `i` in image0 matches keypoint `j` in image1. `-1` means no accepted match.

## Configuration knobs

Common SuperPoint knobs:

- `max_keypoints`: cap keypoints; `-1` keeps all detected keypoints.
- `keypoint_threshold`: lower values produce more keypoints.
- `nms_radius`: lower values keep denser local detections.

Common SuperGlue knobs:

- `weights`: `indoor` or `outdoor`.
- `sinkhorn_iterations`: more iterations cost more runtime.
- `match_threshold`: lower values accept more matches; higher values filter aggressively.

## Indoor vs outdoor profiles

- Use `indoor` for ScanNet-style indoor image pairs. Defaults usually start here.
- Use `outdoor` for Phototourism/YFCC/MegaDepth-style outdoor or wide-baseline image pairs. The README recommends larger resize values, more keypoints, lower NMS radius, and `resize_float` for outdoor pair matching.

## Evaluation model

`match_pairs.py --eval` estimates relative pose from matches and ground-truth intrinsics/relative pose in the pair manifest. It reports:

- `AUC@5`, `AUC@10`, `AUC@20`
- precision (`Prec`)
- matching score (`MScore`)

Evaluation is meaningful only when every pair row has the 38-token ground-truth schema. Use the pair-matching sub-skill for schema and output details.

## What is not included

- No training code.
- No SIFT-based SuperGlue model.
- No homography SuperGlue model.
- No full public image data for paper-scale ScanNet, YFCC, or Phototourism evaluation; the repo provides manifests and small samples, while full reproduction requires external datasets or benchmark submission.
