---
name: segmentation-and-shapes
description: "Generate masks and synthetic shapes, clean and label them, and
  segment images with morphology, watershed, random walker, superpixels, graph
  helpers, and active contours."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Segmentation and Shapes

Use this sub-skill when the task is about drawing masks, synthesizing labeled scenes, cleaning binary regions, or partitioning an image into segments. It owns the stable `skimage.draw`, `skimage.morphology`, `skimage.segmentation`, and `skimage.graph` workflows that turn pixels into regions. This route stops before feature extraction or geometric registration.

## Route Here For

- Drawing lines, polygons, disks, ellipses, rectangles, Bezier curves, and perimeters.
- Painting or filling masks with `set_color` and `polygon2mask`.
- Generating synthetic scenes with `random_shapes`, including overlap control, intensity ranges, and grayscale via `channel_axis=None`.
- Cleaning masks with binary morphology, small-object/hole removal, flooding, reconstruction, and skeletonization.
- Creating markers and segments with `watershed`, `random_walker`, `slic`, `felzenszwalb`, `quickshift`, `expand_labels`, `join_segmentations`, `clear_border`, and `relabel_sequential`.
- Building or visualizing region adjacency graphs with `RAG`, `rag_mean_color`, `rag_boundary`, `show_rag`, `cut_threshold`, `cut_normalized`, and `merge_hierarchical`.
- Using active contours and snakes with `chan_vese`, `active_contour`, `morphological_chan_vese`, `morphological_geodesic_active_contour`, `inverse_gaussian_gradient`, `checkerboard_level_set`, and `disk_level_set`.
- Handling legacy or experimental segmentation helpers from `skimage.future`, including manual and trainable segmentation.

## Use Other Sub-skills For

- Image loading, dtype conversion, and sample data: `../data-io/SKILL.md`.
- Denoising, threshold selection, and intensity/color prep: `../enhancement/SKILL.md`.
- Feature extraction, region measurement, and metrics: `../analysis/SKILL.md`.
- Geometric warps, transforms, and registration: `../transform-registration/SKILL.md`.

## Start Here

- Read `references/workflows.md` for concrete recipes and API selection.
- Read `references/troubleshooting.md` for markers, connectivity, `channel_axis`, and legacy-API caveats.
- Prefer tiny synthetic arrays and CPU-only smoke checks when validating a segmentation path.

## Safe Defaults

- Treat 0 as background or unlabeled unless the API says otherwise; keep positive integers as seeds or region IDs.
- Use `channel_axis=None` for grayscale images and an explicit channel axis for multichannel SLIC or random walker workflows.
- Seed synthetic examples with `rng=0` or another fixed value when reproducibility matters.
- Prefer `expand_labels` over dilation when growth must not overlap.
- Run `relabel_sequential` after joins, cuts, or manual edits when downstream code expects dense labels.
- Treat `skimage.future` helpers as legacy and expect warnings or missing support in `skimage2`.

## Acceptance Checks

- Can a future agent build a mask, clean it, segment it, and inspect boundaries without reopening the source docs?
- Can a future agent choose between watershed, random walker, SLIC, graph cuts, and active contours?
- Are legacy or interactive helpers clearly separated from the stable segmentation route?
