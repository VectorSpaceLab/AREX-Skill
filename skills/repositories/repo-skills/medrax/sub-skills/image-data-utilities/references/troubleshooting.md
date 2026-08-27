# Troubleshooting image preparation

Start with the validator and preserve the original input. Do not retry a
failed conversion against a guessed path or overwrite the source file.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `input does not exist` | Typo, expired upload, or wrong working directory | Confirm the caller supplied the intended path and that the upload has not been cleaned up; rerun the validator. |
| Unsupported suffix | File is not `.png`, `.jpg`, `.jpeg`, `.dcm`, or `.dicom` under the helper contract | Confirm the receiving tool's format contract. Convert explicitly or use an approved suffix override; do not rename bytes without conversion. |
| Image signature mismatch | File is truncated, mislabeled, or malformed | Re-acquire the file or decode it with an approved image library; a suffix change alone is not repair. |
| DICOM has no `DICM` marker | Some DICOM files omit the Part 10 preamble, or the file is not DICOM | Let a pydicom-aware check decide whether it is readable; do not expose tags while probing. |
| `pixel_array` fails | Missing pixel decoder, unsupported transfer syntax, corrupt pixel data, or non-image DICOM | Install/enable the approved pixel handler or obtain a decodable export. Do not treat header validation as pixel validation. |
| `WindowWidth`/`window_width` is zero or negative | Invalid or clinically inappropriate window | Stop, choose a positive width from trusted source context, or use the DICOM's valid window pair. Never divide by a non-positive width. |
| A center or width is missing | Only half of a manual window was supplied, or only one DICOM tag exists | Supply both explicit values or omit both and let the tool use a complete source pair/fallback. |
| Black/white or low-contrast PNG | Wrong window, rescale not expected, inversion/orientation issue, or constant range | Inspect selected center/width, slope/intercept, photometric interpretation, and pixel range. Do not infer a diagnosis from a display artifact. |
| Runtime warning/error on constant image | `img.max() == img.min()` in min/max fallback | Treat as a zero-dynamic-range input. Preserve it for review and apply a documented constant rendering policy outside the converter. |
| `output["image_path"]` missing | `_run` returned an error tuple, but caller ignored `output["error"]` | Branch on the error key first and surface `error_details`. |
| Visualizer says file not found | Display path was not retained, temporary derivative was cleaned, or a relative path changed base directory | Keep the generated path alive through rendering; use a stable absolute/managed path in the caller, without embedding it in public metadata. |
| Visualizer appears to do nothing | Current `_run` checks and returns metadata but leaves `_display_image` commented out | Use the returned path in the UI, or invoke the rendering method in a supported interactive environment. Do not mistake a status tuple for a plotted figure. |
| Grayscale looks colorized | `cmap` was left at `rgb` or a non-gray map was selected | Use `cmap="gray"` for a grayscale CXR display. Keep model preprocessing separate. |
| RGB image becomes one channel | A non-`rgb` colormap was passed and the renderer selected `img[..., 0]` | Use `cmap="rgb"` for intentional RGB display or choose a single channel deliberately. |
| Cannot save generated PNG | Temporary/output directory is missing or not writable | Run the validator with `--output-dir`, create a permitted directory, or change the caller's configured temp directory. Do not use a destructive broad cleanup. |
| UI shows PNG but analysis receives DICOM | The interface intentionally prefers `original_file_path` for message/tool context | Keep the original for provenance, but pass `display_file_path` to a tool that only accepts PIL/skimage/JPG/PNG. Route tool-specific behavior to chest-xray-analysis. |
| DICOM bytes sent as JPEG | A transport encoded raw DICOM while using an `image/jpeg` data URL | Convert first and encode the PNG with `image/png`; retain the DICOM separately. |
| PHI appears in logs or captions | Raw converter metadata was serialized or tags were placed in display text | Redact `PatientID`, dates, positions, and other sensitive fields before logging/display. Conversion is not anonymization. |

## Actionable malformed/nonexistent path check

```bash
python scripts/validate_image_input.py /path/to/missing.dcm
python scripts/validate_image_input.py /path/to/suspect.png --output-dir /path/to/work --json
```

The first command should exit non-zero with an existence error. The second
returns machine-readable checks without parsing DICOM tags or reading image
pixels. If it passes but the utility fails, the problem is decoder/pixel data,
not path existence; follow the corresponding row above.

## Safe escalation

If a failure persists, capture only the suffix, file size, validator result,
selected window values, and non-sensitive exception class/message. Do not attach
DICOM files, raw metadata, base64 payloads, or generated images to an issue
unless the approved privacy process explicitly permits it.
