# Export helpers

## CVAT export

Some fastdup releases provide a `fastdup.cvat` helper, but not every installed wheel ships it. Prefer the bundled `scripts/export_cvat_smoke.py` as a self-contained pattern when the module is unavailable.

Typical outputs:
- `annotations.json`
- `task.json`
- `data/index.json`
- `data/manifest.jsonl`
- copied image files under `data/`
- `fastdup_label.zip`

Requirements:
- source images must be readable by OpenCV
- the output directory must be writable
- labels must align one-to-one with the input file list

## LabelImg export

Some fastdup releases provide a `fastdup.label_img` helper, but not every installed wheel ships it. Prefer the bundled `scripts/export_labelimg_smoke.py` as a self-contained pattern when the module is unavailable.

Typical outputs:
- one XML file per image
- `classes.txt`

Requirements:
- source images must be readable by OpenCV
- the output directory must be writable
- labels must align one-to-one with the input file list

## TensorBoard projector

Use the TensorBoard projector workflow from the model-enrichment path when you want to visualize embeddings.

Typical outputs:
- `meta.tsv`
- `sprite.png` when images are included
- TensorFlow checkpoint files for the embedding tensor
- TensorBoard projector config files

Requirements:
- `tensorflow` and the TensorBoard projector plugin must be installed
- the embedding matrix width must match the configured feature width
- the image list and feature matrix must stay aligned
