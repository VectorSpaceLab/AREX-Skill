# Troubleshooting

## GUI fails to open

**Symptoms**
- Visualizer startup errors
- A blank or missing window
- Errors that mention GUI support being unavailable

**Likely causes**
- The installed Open3D wheel was built without GUI support.
- The machine is headless or lacks the needed display stack.

**Recovery**
- Use `scripts/create_visualization_fixture.py` and compare saved arrays rather
  than opening the GUI.
- Prefer TensorBoard 3D summaries for headless debugging.

## Large point clouds are hard to render

**Symptoms**
- The viewer becomes slow or unresponsive.
- The data load takes too long.

**Likely causes**
- Too many points or too many boxes were passed at once.

**Recovery**
- Subsample the fixture.
- Visualize only a small slice of the dataset.
- Keep the number of bounding boxes manageable.

## Label LUT mismatch

**Symptoms**
- Labels display with unexpected colors or names.
- Prediction and ground-truth colors do not line up.

**Likely causes**
- The LUT was built with a different label mapping from the dataset or model.

**Recovery**
- Rebuild the LUT from the dataset's label map.
- Keep the same label IDs across the whole visualization workflow.

## Missing checkpoints or downloaded demo data

**Symptoms**
- Example scripts or custom workflows try to download model weights.
- A visualization recipe assumes demo data that is not present.

**Likely causes**
- The source examples rely on network access or cached demo assets.

**Recovery**
- Use the bundled tiny fixture helper instead of depending on the source demo.
- Keep checkpoint downloads out of the default smoke path.

## TensorBoard schema mistakes

**Symptoms**
- The summary file is written but the 3D plugin does not show the expected
  geometry.
- Some channels appear empty or mislabeled.

**Likely causes**
- The keys are not in the documented `vertex_*` form.
- The shapes do not match the point count.

**Recovery**
- Use the exact keys documented in the API reference.
- Keep the fixture tiny and compare the saved arrays before trying a full run.

## OpenVINO limitations

**Symptoms**
- The wrapper imports, but the selected model does not work.
- A model/backend pair is not listed as supported.

**Likely causes**
- The chosen model family is outside the supported OpenVINO subset.
- The installed OpenVINO version is incompatible.

**Recovery**
- Restrict OpenVINO usage to the supported model families.
- Treat OpenVINO as optional, not core, unless the task specifically needs it.
