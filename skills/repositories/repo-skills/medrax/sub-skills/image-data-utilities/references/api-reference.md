# Utility API reference

This reference records the observable contracts of the image-data utilities.
Callers should use the public tool inputs and `_run`/`_arun` entry points rather
than depending on private implementation details. The current tools return a
two-item tuple even where a type annotation says `Dict`.

## `DicomProcessorTool`

### Construction

```python
DicomProcessorTool(temp_dir: Optional[str] = None)
```

- If `temp_dir` is omitted, the tool creates a temporary directory.
- If supplied, the directory is created if needed by the tool's constructor.
- The tool writes a unique PNG named like
  `processed_dicom_<8-hex-characters>.png` into that directory.
- No model weights or network access are required by this utility.

### Input schema

```python
{
    "dicom_path": str,
    "window_center": float | None,
    "window_width": float | None,
}
```

`dicom_path` is required. `window_center` and `window_width` are optional
contrast parameters. They are a pair: a caller should provide both or neither.
The implementation only applies the explicit windowing branch when both are
non-`None`.

### Processing order

1. Read the file with `pydicom.dcmread(dicom_path)`.
2. Read `dcm.pixel_array` and cast it to floating point.
3. If no explicit center was supplied, use `WindowCenter` when present. If it
   is a list/multi-value, the implementation selects the first value.
4. If no explicit width was supplied, use `WindowWidth` when present, likewise
   selecting the first value from a list.
5. If both `RescaleSlope` and `RescaleIntercept` are present, calculate
   `pixel * RescaleSlope + RescaleIntercept`.
6. If center and width are both available, clip to
   `center - width // 2` through `center + width // 2`, then scale to uint8
   `[0, 255]`.
7. Otherwise, min/max-normalize to uint8 `[0, 255]`.
8. Save the resulting array as a PNG.

The implementation does not inspect `PhotometricInterpretation`, invert
`MONOCHROME1`, validate a positive window width, or apply a modality-specific
VOI LUT. A caller must treat these as known limitations and verify image
appearance when they matter.

### Success result

```python
output, metadata = tool._run(
    dicom_path,
    window_center=None,
    window_width=None,
)
```

The success shape is:

```python
output == {"image_path": "<generated PNG path>"}
metadata == {
    "PatientID": value_or_None,
    "StudyDate": value_or_None,
    "Modality": value_or_None,
    "PixelSpacing": value_or_None,
    "WindowCenter": selected_or_explicit_center,
    "WindowWidth": selected_or_explicit_width,
    "ImageOrientation": value_or_None,
    "ImagePosition": value_or_None,
    "BitsStored": value_or_None,
    "original_path": dicom_path,
    "output_path": "<generated PNG path>",
    "analysis_status": "completed",
}
```

The values are taken directly from the DICOM object. Some may be pydicom
multi-values rather than plain JSON scalars. `PatientID`, `StudyDate`, and
spatial fields are sensitive; keep them in memory only when needed and redact
before logging or displaying them.

### Failure result

Any exception in reading pixels, applying transforms, or saving the PNG is
caught and returned as:

```python
output == {"error": "<exception text>"}
metadata == {
    "dicom_path": dicom_path,
    "analysis_status": "failed",
    "error_details": "<exception text>",
}
```

Check `output.get("error")` before dereferencing `image_path`. A failure tuple
is not raised by `_run`, so callers that only catch exceptions can accidentally
continue with a missing output.

## `ImageVisualizerTool`

### Input schema

```python
{
    "image_path": str,
    "title": str | None,
    "description": str | None,
    "figsize": (float, float),
    "cmap": str,
}
```

`image_path` is required. The input model documents JPG or PNG images.
`figsize` defaults to `(10, 10)` and `cmap` defaults to `"rgb"`.

### Success result

The current `_run` verifies that `Path(image_path).is_file()` and then returns:

```python
output == {"image_path": image_path}
metadata == {
    "image_path": image_path,
    "title": bool(title),
    "description": bool(description),
    "figsize": figsize,
    "cmap": cmap,
    "analysis_status": "completed",
}
```

The normal `_run` path has the actual `_display_image(...)` call commented out.
If a notebook or desktop display is explicitly required, call the rendering
method in an environment with matplotlib/skimage support, but keep that
presentation concern out of model-tool handoffs.

### Failure result

A missing path or another visualization error returns:

```python
output == {"error": "<exception text>"}
metadata == {
    "image_path": image_path,
    "visualization_status": "failed",
    "note": "An error occurred during image visualization",
}
```

The failure metadata uses `visualization_status`, while success uses
`analysis_status`; check the output error key first.

## Async calls

Both tools expose `_arun` and delegate to their synchronous `_run` behavior.
They do not introduce separate conversion or rendering semantics. Preserve the
same tuple/error handling in asynchronous orchestration.
