---
name: image-pair-matching
description: "Match two images end-to-end with LightGlue and a selected
  local-feature extractor."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# image-pair-matching

Use this sub-skill when you need to match two user-supplied images end-to-end with LightGlue, choose one public extractor head, and save the resulting visualization.

It distills the README minimal script and the demo notebook into a CLI-friendly flow:
- `load_image(...)` to read and normalize RGB tensors,
- device placement for the images, extractor, and matcher,
- `LightGlue(features=...)` matching,
- `rbd(...)` when you handle the dictionaries manually,
- coordinate indexing from `matches[..., 0]` and `matches[..., 1]`,
- and `viz2d` saving for the final PNG.

Use `match_pair(...)` when you want the compact helper equivalent; keep the explicit flow here when you need to inspect the intermediate feature/result dicts.

## Owned runtime assets
- [scripts/match_image_pair.py](scripts/match_image_pair.py)
- [references/workflows.md](references/workflows.md)
- [references/data-and-results.md](references/data-and-results.md)
- [references/troubleshooting.md](references/troubleshooting.md)

## Routed elsewhere
- Extractor choice and feature schema: [../extractors-and-features/SKILL.md](../extractors-and-features/SKILL.md)
- LightGlue thresholds and matcher config: [../matcher-configuration/SKILL.md](../matcher-configuration/SKILL.md)
- Broader plotting and benchmark helpers: [../performance-and-visualization/SKILL.md](../performance-and-visualization/SKILL.md)

## Typical flow
1. Load both images with `load_image`.
2. Move the image tensors, extractor, and matcher to the same device.
3. Build one supported pairing: `superpoint`, `disk`, `aliked`, `sift`, or `doghardnet`.
4. Extract features, run LightGlue, and strip the batch axis with `rbd` when you are handling the dicts yourself.
5. Index the keypoints with the match indices to recover coordinate arrays.
6. Save the visualization with the bundled CLI or the `viz2d` helpers.

## First-run note
SuperPoint, DISK, ALIKED, DoGHardNet, and the feature-specific LightGlue heads may download pretrained weights on first use. SIFT avoids neural extractor downloads, but the SIFT LightGlue head still loads its own weights the first time it runs.

For concrete recipes, start with [references/workflows.md](references/workflows.md) and the CLI in [scripts/match_image_pair.py](scripts/match_image_pair.py).
