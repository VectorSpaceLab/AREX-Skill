# CV and file helpers

Use this reference when working with helper functions that prepare images, masks, visualizations, JSON, file lists, or optional imports around SAHI annotation and prediction objects.

## Image readers and color conventions

| Helper | Input | Output | Important caveats |
| --- | --- | --- | --- |
| `read_image(image_path)` | Local image path | RGB `np.ndarray` in HWC order | Internally reads with OpenCV BGR and converts to RGB. Raises/asserts when the image cannot be read. |
| `read_large_image(image_path)` | Local image path | `(rgb_array, use_cv2)` | Falls back to `skimage.io` if OpenCV cannot read the file. The fallback requires optional `scikit-image` support. |
| `read_image_as_pil(image, exif_fix=True, return_arr=False)` | PIL image, path/URL string, or numpy array | PIL image by default; RGB/HWC array if `return_arr=True` | For numpy input, channel order is not changed; pass RGB arrays. CHW arrays are transposed to HWC by channel-count heuristic. URL strings trigger a network request; use local paths for offline-safe workflows. |
| `_to_hwc(arr)` | Numpy array | HWC array when input looks CHW | Internal helper; useful to know when debugging tiny CHW arrays. |
| `convert_image_to(read_path, extension='jpg', grayscale=False)` | Local image path | Writes converted image beside input | Uses OpenCV; writes a new file. Avoid in non-writing smoke checks. |

`PredictionResult(image=...)` calls `read_image_as_pil`, so pass a PIL image or RGB HWC numpy array when creating synthetic in-memory results. If an image came from raw `cv2.imread`, convert it first with `cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)`.

## Visualization helpers

| Helper | Use for | Key options | Writes when |
| --- | --- | --- | --- |
| `visualize_object_predictions(image, object_prediction_list, ...)` | Draw SAHI `ObjectPrediction` objects on an RGB image. | `rect_th`, `text_size`, `text_th`, `color`, `hide_labels`, `hide_conf`, `output_dir`, `file_name`, `export_format`. | `output_dir` is not `None`; creates the directory and writes `file_name.export_format`. |
| `visualize_prediction(image, boxes, classes, masks=None, ...)` | Draw raw bbox/class arrays without `ObjectPrediction` wrappers. | Same drawing controls except no `hide_conf`; classes are rendered as strings and also used for palette indexing. | `output_dir` is supplied; writes PNG. |
| `PredictionResult.export_visuals(export_dir, ...)` | Simple result-level PNG export. | `text_size`, `rect_th`, `hide_labels`, `hide_conf`, `file_name`. | Always writes `file_name.png` under `export_dir`. |
| `crop_object_predictions(image, object_prediction_list, ...)` | Crop each predicted box from an RGB image. | `output_dir`, `file_name`, `export_format`. | Always writes crops under `output_dir`. |
| `Colors()` | Deterministic palette by category index. | `colors(index, bgr=False)` returns RGB by default. | No writes. |
| `apply_color_mask(image, color)` | Colorize a 2D 0/1 mask. | `color=(R, G, B)`. | No writes. |

Masks and boxes are drawn onto a deep copy of the image. The output image returned in the result dict remains RGB; OpenCV file writing internally converts to BGR.

## Mask and bbox helpers

| Helper | Input | Output | Notes |
| --- | --- | --- | --- |
| `get_coco_segmentation_from_bool_mask(bool_mask)` | 2D bool or 0/1 mask | COCO polygon list `[[x1, y1, ...], ...]` | Uses OpenCV contours. Empty masks return `[]`; tiny one-pixel/line masks may not produce a valid polygon because at least three points are needed. |
| `get_bool_mask_from_coco_segmentation(coco_segmentation, width, height)` | Polygon list plus width/height | 2D array of shape `(height, width)` filled with 0/1 values | Cast with `.astype(bool)` if a strict boolean dtype is required. |
| `get_bbox_from_bool_mask(bool_mask)` | 2D mask | `[xmin, ymin, xmax, ymax]` or `None` | Returns `None` for empty masks or zero-width/zero-height extents. |
| `get_bbox_from_coco_segmentation(coco_segmentation)` | Polygon list | `[xmin, ymin, xmax, ymax]` or `None` | Uses min/max over polygon coordinates. |
| `yolo_bbox_to_voc_bbox(yolo_bbox, image_width, image_height)` | Normalized YOLO `[x_center, y_center, width, height]` | Core/VOC `[xmin, ymin, xmax, ymax]` | Output is absolute pixels. |
| `get_coco_segmentation_from_obb_points(obb_points)` | OBB points shaped `(4, 2)` | One closed COCO polygon | Used for oriented boxes represented as polygons. |
| `normalize_numpy_image(image)` | Numpy image | Image divided by its max value | Guard against all-zero arrays before use. |

Round-trip example:

```python
import numpy as np
from sahi.utils.cv import (
    get_bbox_from_bool_mask,
    get_bool_mask_from_coco_segmentation,
    get_coco_segmentation_from_bool_mask,
)

mask = np.zeros((20, 30), dtype=bool)
mask[5:12, 7:16] = True
segmentation = get_coco_segmentation_from_bool_mask(mask)
restored = get_bool_mask_from_coco_segmentation(segmentation, width=30, height=20).astype(bool)
bbox = get_bbox_from_bool_mask(restored)
assert bbox is not None
```

## Shapely geometry helpers used by object conversions

| Helper | Use |
| --- | --- |
| `get_shapely_box(x, y, width, height)` | Convert COCO `[x, y, width, height]` to a Shapely box. |
| `get_shapely_multipolygon(coco_segmentation)` | Convert COCO polygon lists to a valid Shapely `MultiPolygon`; attempts to repair invalid geometry. |
| `get_bbox_from_shapely(shapely_object)` | Return both COCO `[x, y, width, height]` and core/VOC `[xmin, ymin, xmax, ymax]`. |
| `ShapelyAnnotation.from_coco_segmentation()` / `.from_coco_bbox()` | Build an annotation geometry for conversion, slicing, simplification, buffering, and intersection. |
| `ShapelyAnnotation.to_coco_segmentation()`, `.to_xywh()`, `.to_xyxy()`, `.to_opencv_contours()` | Export polygon, COCO bbox, core/VOC bbox, or OpenCV contour forms. |

Object-level `to_coco_*()` conversions rely on these helpers for area, bbox, and segmentation serialization. Polygon coordinates may be cast to integers during `to_coco_segmentation()`.

## JSON, path, and file-list helpers

| Helper | Use | Safety notes |
| --- | --- | --- |
| `save_json(data, save_path, indent=None)` | Write JSON with parent directory creation. | Uses `NumpyEncoder` so numpy ints/floats/arrays serialize cleanly. Writes to the requested path. |
| `load_json(load_path, encoding='utf-8')` | Read JSON. | Returns the decoded Python object. |
| `save_pickle(data, save_path)` / `load_pickle(load_path)` | Pickle persistence. | Pickle is Python-specific; do not load untrusted pickle files. |
| `list_files(directory, contains=['.json'], verbose=1)` | List matching files in one directory. | Matching is case-insensitive substring matching against file names. |
| `list_files_recursively(directory, contains=['.json'], verbose=True)` | Recursively list matching files. | Returns `(relative_paths, absolute_paths)`; relative paths are derived from the supplied directory string. |
| `get_base_filename(path)` | Return `(name_with_extension, stem_without_extension)`. | Pure path parsing. |
| `get_file_extension(path)` | Return extension such as `.json`. | Pure path parsing. |
| `increment_path(path, exist_ok=True, sep='')` | Avoid overwriting an existing path by suffixing a number when `exist_ok=False`. | Check the returned string before writing. |
| `import_model_class(model_type, class_name)` | Dynamically import `sahi.models.<model_type>.<class_name>`. | Model backends may require optional packages; route backend setup to model/prediction sub-skills. |
| `download_from_url(from_url, to_path)` | Download a URL if `to_path` does not exist. | Performs network I/O. Do not use in offline smoke scripts or unless the user explicitly requested a download. |

## Import and environment probes

SAHI import helpers are useful for optional dependency guards:

| Helper | Use |
| --- | --- |
| `is_available(module_name)` | Fast importability check with `importlib.util.find_spec`. |
| `check_requirements(package_names)` | Raise `ImportError` if any package is missing. |
| `get_package_info(package_name, verbose=True)` | Return `(is_available, version_string)` and optionally log package info. |
| `check_package_minimum_version(package_name, minimum_version)` | Return whether an installed package meets a minimum version; missing packages are treated as compatible by this helper. |
| `ensure_package_minimum_version(package_name, minimum_version)` | Raise when the installed package is below the minimum version. |
| `get_opencv_conflict_message()` | Explain a mixed-version OpenCV install when multiple OpenCV distributions conflict. |

Use these probes before optional `fiftyone`, `imantics`, `skimage`, or backend-specific imports. Keep fallback paths available: COCO JSON dictionaries are the most dependency-light interchange format.
