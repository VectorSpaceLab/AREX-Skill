# Input and handoff workflows

These workflows are deliberately independent of a particular checkout. They
assume the utility package and its runtime dependencies are installed in the
execution environment.

## 1. Validate before touching pixels

```bash
python scripts/validate_image_input.py /path/to/input.png
python scripts/validate_image_input.py /path/to/input.dcm --output-dir /path/to/work
```

The command checks existence, regular-file status, a conventional supported
suffix, and a non-PHI file signature. With `--output-dir`, it also checks that
the destination exists, is a directory, and is writable. A validation failure
is actionable: fix the path/suffix/permissions or route to a caller that
supports the actual format. The helper does not decode pixels, so a DICOM with
an unsupported transfer syntax can still fail later at `pixel_array`.

For CI or smoke checks, run:

```bash
python scripts/validate_image_input.py --self-test
```

The self-test creates only a temporary directory and tiny synthetic headers;
it does not require a medical image, network, or model service.

## 2. Ordinary image path

1. Validate `.png`, `.jpg`, or `.jpeg`.
2. Keep the validated path as `display_path`.
3. Call the visualizer when a UI result is useful:

   ```python
   output, metadata = ImageVisualizerTool()._run(
       image_path=display_path,
       title="Chest radiograph",
       description=None,
       figsize=(10, 10),
       cmap="gray",
   )
   ```

4. Require `"error" not in output` before forwarding `output["image_path"]`.
5. Hand the same path to an analysis tool only if its own input contract accepts
   the format. Route the actual analysis to
   [chest-xray-analysis](../../chest-xray-analysis/SKILL.md).

`title` and `description` are presentation fields. Keep them generic and free
of patient identifiers.

## 3. DICOM source with a display derivative

Use two variables from the beginning:

```python
original_path = "/controlled/input/study.dcm"
# display_path is assigned only after successful conversion.

converted, dicom_meta = DicomProcessorTool(temp_dir=work_dir)._run(
    dicom_path=original_path,
    window_center=None,
    window_width=None,
)
if "error" in converted:
    raise RuntimeError(dicom_meta.get("error_details", converted["error"]))
display_path = converted["image_path"]
```

Then:

- show `display_path` in the UI or visualizer;
- retain `original_path` for provenance, archival, or a DICOM-aware consumer;
- use `display_path` for an image-only model tool that reads PIL/skimage/JPG/PNG;
- carry only redacted/necessary `dicom_meta` forward.

Do not assign `display_path` back into `original_path`. The generated PNG is
not a replacement for the DICOM, and deleting the source after conversion is
outside this workflow.

## 4. How the interface uses the distinction

The upload interface copies a selected file into temporary storage and records
`original_file_path`. For a `.dcm` suffix it invokes the DICOM processor and
records the generated PNG as `display_file_path`; a regular image can use the
same file for both.

When a message is added, the interface prefers `original_file_path` for the
message content. During processing it also sends an `image_path` message and
uses the original path first. This preserves the source identity, but it means
a caller integrating a model that cannot decode DICOM must explicitly pass the
PNG derivative to that model rather than blindly inheriting the UI's original
path preference. Raw DICOM bytes must not be labeled as JPEG in a multimodal
request; use the display PNG and `image/png` when that transport is required.

The interface uses a visualizer result's `image_path` for the displayed image.
This is why a conversion can be display-only while the original remains
available to the agent layer. UI event/state details belong to
[web-interface](../../web-interface/SKILL.md).

## 5. Window/level selection

Use this decision order:

1. If the request supplies both center and width, use those values after
   checking that width is positive and finite.
2. Otherwise allow the converter to use the first DICOM window pair.
3. If no complete pair exists, inspect the output for a constant-range failure
   and confirm that min/max scaling is clinically acceptable.

A center without a width, or width without a center, is not a complete manual
window. Avoid silently combining a user value with an unrelated DICOM tag.
When window settings materially affect interpretation, record the selected
values in a protected run record without copying patient identifiers.

## 6. Temporary files and output directories

Prefer a dedicated, access-controlled temporary directory for generated PNGs.
Validate it before conversion. The utility generates unique names, but it does
not provide a retention policy. The caller should:

- retain both paths for the duration of any required UI/model handoff;
- remove only generated derivatives under an explicit cleanup policy;
- avoid cleaning a directory that may contain an uploaded original;
- report a permission failure with the destination and remediation, without
  dumping DICOM metadata.
