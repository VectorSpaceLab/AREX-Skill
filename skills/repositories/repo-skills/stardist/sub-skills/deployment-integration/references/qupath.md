# QuPath annotation handoff

`scripts/qupath_export_annotations.groovy` is a project-level 2D helper. It
must be run in QuPath's script editor with **Run for project**; it is not a
Python program or a generic Groovy script.

## External prerequisites and operation

- Install a compatible QuPath release with its ImageJ extension enabled.
  The script imports `qupath.imagej.gui.IJExtension` and ImageJ legacy classes
  (`IJ`, `RoiManager`, and `ChannelSplitter`).
- Open a QuPath project, add the raw 2D images, and create non-overlapping
  object annotations. Rectangle ROIs are intentionally ignored.
- Review `channel_of_interest` (1-based; `null` means all channels) and
  `downsample` (1 is native resolution) at the top of the bundled script.
- Back up or copy the project. The script creates output directories and may
  replace same-named TIFFs through ImageJ's save behavior.

For each project image, the script requests the full image, converts the
annotation ROIs to sequential positive labels in a 16-bit mask, and writes:

```text
<project>/ground_truth/images/<image-name>.tif
<project>/ground_truth/masks/<image-name>.tif
```

Background is 0 and non-rectangle objects receive labels starting at 1. The
image and mask must be inspected for identical shape, channel selection,
downsample, and pairing before routing them to [2D workflows](../../2d-workflows/SKILL.md).
This route is 2D only; it does not create 3D labels.

## Recovery

| Symptom | Action |
|---|---|
| No project/image data | Open a project and use **Run for project**, not a generic interpreter. |
| Missing `IJExtension`, `RoiManager`, or `ChannelSplitter` | Install/enable the QuPath ImageJ extension and use a compatible QuPath API. Python packages cannot repair a Java bridge. |
| Missing objects | Ensure annotations are in the image hierarchy and selected; convert rectangles to polygon/area annotations because rectangles are skipped. |
| Shifted/small output | Check `downsample`, server calibration, and image-server path; do not rescale only one of image/mask. |
| Filename collision | Run in a controlled project copy, compare existing `ground_truth` files, and keep image/mask pairs synchronized. |

QuPath GUI execution, ImageJ bridge compatibility, and visual correctness are
external/manual checks. Static script inspection may pass while these remain
unverified.
