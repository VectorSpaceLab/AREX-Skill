# Visualization Workflows

## Visualize a dataset

Use `Visualizer.visualize_dataset(...)` when you have a dataset object and want
an interactive inspection view.

```python
import open3d.ml.torch as ml3d

vis = ml3d.vis.Visualizer()
dataset = ml3d.datasets.SemanticKITTI(dataset_path="/path/to/dataset")
vis.visualize_dataset(dataset, "all", indices=range(10))
```

## Visualize custom point clouds

Use `Visualizer.visualize(...)` when you already have a list of dictionaries
with `name`, `points`, and optional label or prediction arrays.

Good uses include:

- labels vs. predictions
- custom scalar/vector attributes
- small debugging point clouds
- object-detection box overlays

If you need a small fixture first, run `scripts/create_visualization_fixture.py`
and feed the generated file into your own display code or summary writer.

## Visualize predictions

A common pattern is:

1. Run inference with `training-and-pipelines`.
2. Convert the result into a point-cloud dictionary.
3. Add labels, predictions, or custom attributes.
4. Visualize the combined data.

This is especially useful for segmentation workflows where you want to compare
ground truth and predicted labels on the same cloud.

## Bounding-box visualization

For object detection, build `BoundingBox3D` objects and pass them as the
`bounding_boxes` argument or convert them into line geometry first.

Useful box fields:

- `center`
- `front`, `up`, `left`
- `size`
- `label_class`
- `confidence`

## TensorBoard 3D summaries

The repo's TensorBoard examples write `vertex_*` arrays into the Open3D plugin
format.

Typical usage:

- `vertex_positions` for points
- `vertex_labels` for semantic labels
- `vertex_scores` for per-point scores
- `vertex_features` for feature vectors
- `vertex_intensities` for intensity-like channels
- `bboxes` for object-detection boxes

Keep the summary data tiny and explicit so it stays easy to inspect.

## OpenVINO wrapper

The optional OpenVINO wrapper is mainly for inference-time usage with supported
models. Use it only when you know the chosen model family is supported and the
necessary OpenVINO package is installed.

## Headless-safe fallback

When the GUI is unavailable, prefer:

- generating a fixture with the bundled helper
- writing TensorBoard summaries
- comparing dictionaries or saved arrays instead of opening a window
