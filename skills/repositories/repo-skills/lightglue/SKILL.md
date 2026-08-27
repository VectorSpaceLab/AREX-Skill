---
name: lightglue
description: "Use LightGlue for local feature matching, extractor selection,
  matcher configuration, visualization, and benchmarking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightGlue

Use this repo skill when a task involves LightGlue local feature matching: matching two images, choosing a supported feature extractor, validating feature dictionaries, configuring the matcher, plotting matches/pruning, or benchmarking latency.

LightGlue is an inference package for sparse local feature matching. It extracts or consumes keypoints/descriptors for two images and returns mutual correspondences plus scores and adaptive-depth/pruning diagnostics.

## First checks

Install the public package or a local checkout with its runtime dependencies:

```bash
python -m pip install git+https://github.com/cvg/LightGlue.git
# or, in a local checkout:
python -m pip install -e .
```

Minimal import check:

```python
from lightglue import LightGlue, SuperPoint, DISK, SIFT, ALIKED, DoGHardNet, match_pair
from lightglue.utils import load_image, rbd
```

Download-free API smoke check from this skill:

```bash
python scripts/lightglue_smoke.py --device cpu
```

This smoke check validates imports and synthetic tensor shapes with `features=None`; it does not validate pretrained matching quality.

## Route by task

| If the user asks to... | Read |
|---|---|
| Match two image files, save a match plot, use `match_pair`, or interpret coordinate correspondences. | [sub-skills/image-pair-matching/SKILL.md](sub-skills/image-pair-matching/SKILL.md) |
| Choose/configure SuperPoint, DISK, ALIKED, SIFT, or DoGHardNet, or validate precomputed feature dictionaries. | [sub-skills/extractors-and-features/SKILL.md](sub-skills/extractors-and-features/SKILL.md) |
| Call `LightGlue` directly, set thresholds, use `features=None`, disable adaptivity, compile, or interpret output keys. | [sub-skills/matcher-configuration/SKILL.md](sub-skills/matcher-configuration/SKILL.md) |
| Benchmark latency/throughput, use FlashAttention or `torch.compile`, tune pruning thresholds, or plot matches/keypoints/pruning. | [sub-skills/performance-and-visualization/SKILL.md](sub-skills/performance-and-visualization/SKILL.md) |

## Shared references and scripts

- [references/package-overview.md](references/package-overview.md): package purpose, dependencies, public entry points, feature families, first-use weights, and backend stance.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting install/import, network/cache, backend, and data-shape failures.
- [references/repo-provenance.md](references/repo-provenance.md): source commit, package version, evidence paths, and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured scenario metadata for repo-skill routing.
- [scripts/lightglue_smoke.py](scripts/lightglue_smoke.py): deterministic import and synthetic matcher smoke check with no pretrained downloads.

## Operating defaults

- Use `SIFT` for offline feature-schema checks because the default OpenCV SIFT extractor does not download neural weights.
- Use feature-specific matcher presets (`features="superpoint"`, `"disk"`, `"aliked"`, `"sift"`, or `"doghardnet"`) for real pretrained matching; they may download matcher weights on first use.
- Use `features=None` only for precomputed/custom descriptors or API smoke checks. Random/untrained weights are not a matching-quality proof.
- CPU is adequate for import checks, schema validation, and tiny smoke tests. CUDA/MPS/FlashAttention are optional acceleration paths, not required package semantics.
- Do not send users to original repo files for runtime instructions; use the bundled references and scripts in this skill tree.

## Non-goals

This skill does not cover training LightGlue from scratch, full structure-from-motion/localization pipelines, third-party ONNX/TensorRT export projects, or generic computer-vision tasks unrelated to local feature matching.
