# Data formats

## Inputs

### Folder or file-list input
`fastdup.run` and `fastdup.create` accept:
- a local folder of images or videos
- a file containing one path per line
- `s3://...` or `minio://...` paths
- tar/zip/webdataset-style archives
- a list of filenames

### Annotation dataframe input
Common columns used by the repo workflows:
- `filename` — image or frame path
- `label` — class or semantic label
- `split` — optional train/test split
- `crop_filename` — optional crop path for bbox workflows
- `col_x`, `row_y`, `width`, `height` — axis-aligned bounding boxes
- `x1`, `y1`, `x2`, `y2`, `x3`, `y3`, `x4`, `y4` — rotated bounding boxes
- `img_h`, `img_w` — image size metadata
- `img_id` — optional row linkage

The safest convention is to keep `filename` absolute when in doubt.

## Output files

- `features.dat` — binary float32 matrix of image features
- `features.dat.csv` — filename list matching the binary rows
- `features.bad.csv` — corrupted or unreadable inputs
- `similarity.csv` — `from,to,distance`
- `outliers.csv` — outlier candidates
- `stats.csv` / `atrain_stats.csv` — image statistics depending on workflow
- `component_info.csv` — component sizes
- `connected_components.csv` — component assignment per image
- `nnf.index` — nearest-neighbor index for search/resume flows
- `config.json` — run metadata used by galleries and resume logic
- `galleries/*.html` — visual reports

## Binary feature round-trip

- Save features with `fastdup.save_binary_feature(save_path, filenames, np_array)`.
- `np_array` must be a `float32` array of shape `(rows, d)`.
- Load features with `fastdup.load_binary_feature(path, d=d)`.
- The default feature width used by the core engine is `576`.
- A width mismatch raises a reshape error.

## Annotation and export helpers

- COCO-style labels are read from text files with class ids.
- CVAT and LabelImg helpers write export-friendly annotations from image lists plus labels.
- TensorBoard projector helpers write embeddings, labels, and sprite images.

## Practical rule

When building a dataframe for fastdup, match the file paths to how the run will resolve them and keep the column names stable across all rows.
