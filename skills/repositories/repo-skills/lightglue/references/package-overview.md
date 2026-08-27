# LightGlue Package Overview

## When to read

Read this for cross-cutting LightGlue facts before choosing a focused sub-skill. It covers package purpose, install/import checks, public entry points, supported feature families, backend expectations, and first-use weight behavior.

## What LightGlue does

LightGlue matches sparse local features across an image pair. A typical workflow extracts keypoints and descriptors from each image, passes both feature dictionaries to `LightGlue`, and reads back mutual matches plus scores, early-stop layer, and pruning diagnostics.

LightGlue in this repository is inference-focused. Training and full benchmark reproduction are outside this package; training is handled by a separate project referenced by the upstream authors, not by this repo skill.

## Install and import

Public install pattern:

```bash
python -m pip install git+https://github.com/cvg/LightGlue.git
```

For local development against a checkout, use editable install from that checkout:

```bash
python -m pip install -e .
```

Runtime dependencies from package metadata are:

- `torch>=1.9.1`
- `torchvision>=0.3`
- `numpy`
- `opencv-python`
- `matplotlib`
- `kornia>=0.6.11`

Minimal import check:

```python
from lightglue import LightGlue, SuperPoint, DISK, SIFT, ALIKED, DoGHardNet, match_pair
from lightglue.utils import load_image, rbd
```

For a download-free API smoke check, run the bundled helper from this skill:

```bash
python scripts/lightglue_smoke.py --device cpu
```

`lightglue_smoke.py` uses `LightGlue(features=None, ...)` with random untrained weights. It validates importability and tensor/output shapes, not pretrained matching quality.

## Public entry points

| Entry point | Purpose | Read next |
|---|---|---|
| `LightGlue(features='superpoint'|'disk'|'aliked'|'sift'|'doghardnet'|'raco-aliked')` | Feature-specific matcher with pretrained weights. | `sub-skills/matcher-configuration/` |
| `LightGlue(features=None, **conf)` | Direct matcher construction for precomputed/custom descriptors or API smoke checks. | `sub-skills/matcher-configuration/` |
| `SuperPoint`, `DISK`, `ALIKED`, `SIFT`, `DoGHardNet` | Local feature extractors compatible with LightGlue presets. | `sub-skills/extractors-and-features/` |
| `match_pair(extractor, matcher, image0, image1, device='cpu', **preprocess)` | Convenience image-pair matching helper. | `sub-skills/image-pair-matching/` |
| `lightglue.utils.load_image`, `rbd`, `batch_to_device` | Image loading, batch removal, and device movement utilities. | `sub-skills/image-pair-matching/` |
| `lightglue.viz2d` | Matplotlib plotting for images, matches, keypoints, pruning colors, and saving plots. | `sub-skills/performance-and-visualization/` |

## Feature families and weight downloads

Supported built-in feature families:

- `superpoint`: 256-D learned features; `SuperPoint` downloads pretrained weights if missing.
- `disk`: 128-D learned features; `DISK` uses Kornia pretrained weights.
- `aliked`: 128-D ALIKED variants except `aliked-t16`; `ALIKED` downloads selected weights if missing.
- `sift`: 128-D SIFT/RootSIFT features; OpenCV SIFT extractor is offline-safe, but `LightGlue(features='sift')` still loads SIFT matcher weights.
- `doghardnet`: 128-D SIFT keypoints plus HardNet descriptors; may download/cache Kornia HardNet weights.
- `raco-aliked`: matcher preset for compatible 128-D RACO-ALIKED-style precomputed features; no exported extractor class.

First-use pretrained components call PyTorch/Kornia download/cache utilities. If a task must run without network, use this skill's smoke scripts, default OpenCV SIFT schema inspection, or ensure weights are already cached before the matching/benchmark task.

## Backend stance

- CPU is sufficient for import checks, schema inspection, SIFT extraction, and small synthetic matcher validation.
- CUDA/MPS are optional accelerators for real image matching and benchmarking.
- FlashAttention or PyTorch scaled-dot-product attention can accelerate CUDA runs, but LightGlue has eager fallbacks.
- `torch.compile` is a performance option, mainly useful on CUDA; it changes pruning behavior for smaller static lengths.
- Optional `pycolmap` SIFT backends and `hloc` SuperGlue comparison are not required for normal LightGlue use.

## Skill routing

- Use `image-pair-matching` for matching two images and saving a result plot.
- Use `extractors-and-features` for choosing extractors, validating feature dictionaries, and handling precomputed descriptors.
- Use `matcher-configuration` for direct `LightGlue` configuration and output interpretation.
- Use `performance-and-visualization` for timing, pruning/compile decisions, and plotting helper usage.
