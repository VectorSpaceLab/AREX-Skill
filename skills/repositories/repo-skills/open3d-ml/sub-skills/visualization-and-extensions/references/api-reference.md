# Visualization API Reference

## Purpose

Read this when you need the exact object names, method signatures, and data
shapes for Open3D-ML visualization and summary-writing workflows.

## Verified signatures

From live inspection in the private environment:

- `Visualizer.visualize(self, data, lut=None, bounding_boxes=None, width=1280, height=768)`
- `Visualizer.visualize_dataset(self, dataset, split, indices=None, width=1280, height=768)`
- `LabelLUT.add_label(self, name, value, color=None)`
- `BoundingBox3D(center, front, up, left, size, label_class, confidence, meta=None, show_class=False, show_confidence=False, show_meta=None, identifier=None, arrow_length=1.0)`

## Point-cloud visualization dictionaries

A custom visualization entry should include:

- `name`: unique point-cloud name.
- `points`: array-like point positions.
- Optional per-point arrays such as:
  - `labels`
  - `pred`
  - `random_colors`
  - `int_attr`
  - any other scalar or vector attribute the visualizer can display.

The visualizer accepts NumPy arrays and may also accept framework tensors via
conversion in the internal data model.

## Dataset visualization

`visualize_dataset(dataset, split, indices=None, width=1280, height=768)`
expects a dataset object that can supply a `label_to_names` mapping and a split
object.

Use it when you want to inspect real dataset items instead of a hand-built
point-cloud dictionary.

## Label LUT

`LabelLUT.add_label(name, value, color=None)` associates a display name and
integer value with a color.

Use the LUT when:

- you want the same label coloring across multiple point clouds
- you compare predictions against ground truth
- you visualize custom labels or semantic segmentation outputs

## Bounding boxes

`BoundingBox3D` uses an oriented-box frame:

- `center`: box center
- `front`, `up`, `left`: orthogonal orientation vectors
- `size`: width/height/depth-like extents
- `label_class`, `confidence`: semantic and score fields

The object can be rendered directly by the visualizer or converted into line
geometry for custom display paths.

## TensorBoard 3D summary keys

The repo's TensorBoard examples use `vertex_*` keys for per-vertex data.
Common keys include:

- `vertex_positions`
- `vertex_labels`
- `vertex_scores`
- `vertex_features`
- `vertex_intensities`
- `bboxes` for bounding-box summaries

Notes:

- Point/feature arrays should be shaped consistently with the number of points.
- Summary helpers may also accept `label_to_names` for class-name display.
- If you are writing 3D summaries, keep the schema small and explicit.

## OpenVINO wrapper

The optional OpenVINO wrapper can wrap selected model families, but it is not a
core requirement for visualizing point clouds or writing summaries. It is a
separate extension path with its own version/support constraints.
