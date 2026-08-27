# Workflow patterns

## 1. Minimal pair matcher

Use this when you want one concise Python function that matches two grayscale images.

1. Pick a device: CPU for portability, CUDA if `torch.cuda.is_available()` and you want speed.
2. Create `Matching` with nested `superpoint` and `superglue` config dictionaries.
3. Convert both images to grayscale float tensors shaped `1x1xHxW`.
4. Call `model.eval()` and wrap inference in `torch.no_grad()`.
5. Run one image pair at a time unless the local-feature lengths already match across the batch.
6. Read `matches0[0]`, `keypoints0[0]`, `keypoints1[0]`, and `matching_scores0[0]`.

```python
import torch
from models.matching import Matching
from models.utils import frame2tensor

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = Matching({
    "superpoint": {"max_keypoints": 1024},
    "superglue": {"weights": "indoor", "match_threshold": 0.2},
}).eval().to(device)

image0 = frame2tensor(gray0, device)
image1 = frame2tensor(gray1, device)

with torch.no_grad():
    pred = model({"image0": image0, "image1": image1})

matches0 = pred["matches0"][0]
valid = matches0 > -1
mkpts0 = pred["keypoints0"][0][valid]
mkpts1 = pred["keypoints1"][0][matches0[valid]]
conf = pred["matching_scores0"][0][valid]
```

## 2. Split extractor and matcher

Use this when you want to cache local features or inspect the detector output before matching.

1. Run `SuperPoint` once per image.
2. Stack the per-image sequences before calling `SuperGlue` directly.
3. Keep the batch size at one unless every feature tensor already has the same length.

```python
import torch
from models.superpoint import SuperPoint
from models.superglue import SuperGlue

sp = SuperPoint({"max_keypoints": 1024}).eval().to(device)
sg = SuperGlue({"weights": "outdoor", "match_threshold": 0.2}).eval().to(device)

with torch.no_grad():
    feats0 = sp({"image": image0})
    feats1 = sp({"image": image1})

    data = {
        "image0": image0,
        "image1": image1,
        "keypoints0": torch.stack(feats0["keypoints"]),
        "scores0": torch.stack(feats0["scores"]),
        "descriptors0": torch.stack(feats0["descriptors"]),
        "keypoints1": torch.stack(feats1["keypoints"]),
        "scores1": torch.stack(feats1["scores"]),
        "descriptors1": torch.stack(feats1["descriptors"]),
    }
    pred = sg(data)
```

## 3. Geometry check

Use this when you need a quick pose summary from the matched points.

1. Convert tensors to NumPy arrays on CPU.
2. Filter `matches0 >= 0` and extract the matched coordinates.
3. Call `estimate_pose` with `K0`, `K1`, and the ground-truth relative pose.
4. Summarize errors with `compute_pose_error` and `pose_auc`.

```python
from models.utils import estimate_pose, compute_pose_error, pose_auc

valid = matches0 >= 0
mkpts0 = kpts0[valid]
mkpts1 = kpts1[matches0[valid]]
pose = estimate_pose(mkpts0, mkpts1, K0, K1, thresh=1.0)
if pose is not None:
    R, t, inliers = pose
    err_t, err_R = compute_pose_error(T_0to1, R, t)
```

## 4. Configuration advice

- Indoor scenes: start with `weights="indoor"`, `max_keypoints=1024`, and `nms_radius=4`.
- Outdoor scenes: start with `weights="outdoor"`, `max_keypoints=2048`, `nms_radius=3`, and `resize_float=True` when loading large images.
- To reduce empty matches, lower `keypoint_threshold` first, then lower `match_threshold` if needed.
- Keep `descriptor_dim=256`, `keypoint_encoder`, and `GNN_layers` aligned with the shipped checkpoints.
- If you want CPU even when CUDA exists, choose `torch.device("cpu")` explicitly.

## 5. Bundled helper checks

- `python scripts/inspect_superglue_api.py --repo-root <repo-root>`
- `python scripts/run_matching_api_smoke.py --repo-root <repo-root> --device auto`

## 6. Routing reminder

If your task is really a batch pair-file run or a live demo session, switch to the sibling sub-skill instead of extending this one.
