# Workflows

## Public package recipe

The README-style flow is the default mental model for this sub-skill:

```python
import torch
from lightglue import LightGlue, SuperPoint, match_pair
from lightglue.utils import load_image, rbd

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
extractor = SuperPoint(max_num_keypoints=2048).eval().to(device)
matcher = LightGlue(features="superpoint").eval().to(device)

image0 = load_image("/path/to/image0.jpg").to(device)
image1 = load_image("/path/to/image1.jpg").to(device)

# Compact helper: returns batch-stripped feature/result dicts.
feats0, feats1, matches01 = match_pair(
    extractor, matcher, image0, image1, device=device, resize=1024
)

matches = matches01["matches"]
points0 = feats0["keypoints"][matches[:, 0]]
points1 = feats1["keypoints"][matches[:, 1]]
```

If you want the explicit notebook-style flow, keep `rbd` visible:

```python
feats0 = extractor.extract(image0, resize=1024)
feats1 = extractor.extract(image1, resize=1024)
matches01 = matcher({"image0": feats0, "image1": feats1})
feats0, feats1, matches01 = [rbd(x) for x in (feats0, feats1, matches01)]
```

## Demo notebook recipe

The demo notebook adds a visualization overlay after matching:

```python
from lightglue import viz2d

axes = viz2d.plot_images([image0, image1])
viz2d.plot_matches(points0, points1, color="lime", lw=0.2)
viz2d.add_text(0, f"Stop after {matches01['stop']} layers")
viz2d.save_plot("/path/to/matches.png")
```

For the pruning-colored notebook look, the demo also uses the returned pruning arrays:

```python
kpc0 = viz2d.cm_prune(matches01["prune0"])
kpc1 = viz2d.cm_prune(matches01["prune1"])
viz2d.plot_images([image0, image1])
viz2d.plot_keypoints([feats0["keypoints"], feats1["keypoints"]], colors=[kpc0, kpc1], ps=6)
```

## CLI recipe

The bundled script is the preferred no-repo-assets path:

```bash
python scripts/match_image_pair.py \
  --image0 /path/to/image0.jpg \
  --image1 /path/to/image1.jpg \
  --features superpoint \
  --device auto \
  --output matches.png
```

Use the OpenCV SIFT path when you want to avoid neural extractor downloads:

```bash
python scripts/match_image_pair.py \
  --image0 /path/to/image0.jpg \
  --image1 /path/to/image1.jpg \
  --features sift \
  --device cpu \
  --max-keypoints 2048 \
  --output sift-matches.png
```

For headless runs, add `--no-viz` and rely on the output PNG.

## Device choice

- `auto`: prefers CUDA, then MPS, then CPU.
- `cuda`: fastest when available; report clearly if CUDA is missing.
- `mps`: Apple Silicon path when supported.
- `cpu`: safest fallback and the least surprising for automation.

## Feature and matcher pairing

Keep the extractor and LightGlue feature name aligned:

- `superpoint` -> `SuperPoint(...)` + `LightGlue(features="superpoint")`
- `disk` -> `DISK(...)` + `LightGlue(features="disk")`
- `aliked` -> `ALIKED(...)` + `LightGlue(features="aliked")`
- `sift` -> `SIFT(backend="opencv")` + `LightGlue(features="sift")`
- `doghardnet` -> `DoGHardNet(...)` + `LightGlue(features="doghardnet")`

## Validation signals

A successful run usually prints:
- the selected device,
- the chosen feature family,
- keypoint counts for both images,
- the match count,
- the final `stop` layer,
- and the saved PNG path when `--output` is set.

A saved image file plus a non-empty `matches` tensor is the main end-to-end success signal.

## No-checkout path

This sub-skill is self-contained once the package imports successfully. Use your own image paths; no bundled demo assets or notebook state are required.
