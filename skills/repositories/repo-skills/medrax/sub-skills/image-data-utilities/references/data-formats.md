# Data formats, pixels, and privacy

## Accepted roles and formats

| Input role | Typical suffix | Native utility contract | Result |
| --- | --- | --- | --- |
| Display/model image | `.png` | `ImageVisualizerTool` documents JPG/PNG | Same path is returned |
| Display/model image | `.jpg`, `.jpeg` | JPEG is the JPG family; verify the receiving tool | Same path is returned |
| Medical source | `.dcm`, or a DICOM file with another suffix | `DicomProcessorTool` calls pydicom; suffix alone is not a DICOM proof | Temporary PNG plus metadata |

`ImageVisualizerTool` explicitly says it supports JPG or PNG, even though the
underlying skimage reader may recognize more formats. Do not expand the public
contract based only on an accidental reader capability. A DICOM file is not an
image input for this visualizer until converted to a viewable derivative.

The bundled validator uses the conventional image suffixes `.png`, `.jpg`,
`.jpeg` and DICOM suffixes `.dcm`, `.dicom`. It performs only lightweight header
checks; successful validation does not prove that a decoder can read every
pixel.

## DICOM pixel handling

`DicomProcessorTool` reads `pixel_array`, converts it to floating point, and
then optionally applies the two rescale tags:

```text
scaled = raw_pixel * RescaleSlope + RescaleIntercept
```

If explicit `window_center` and `window_width` are not both supplied, the tool
uses the first `WindowCenter` and `WindowWidth` values from the dataset when
available. With a complete window pair it clips and linearly maps the window to
8-bit grayscale. Without a complete pair it maps the observed minimum and
maximum to 0 and 255.

The PNG is a display derivative. It is not a lossless archival replacement for
the source DICOM, and the conversion does not preserve all DICOM tags in the
PNG. Keep the original path separately whenever provenance, reprocessing, or a
DICOM-aware consumer is required.

### Important edge cases

- `window_width <= 0` makes the window transform invalid or meaningless. Reject
  or correct it before invocation; do not rely on the implementation to repair
  it.
- A zero dynamic range (`img.max() == img.min()`) makes the fallback min/max
  expression divide by zero. Treat a constant-pixel image as a preparation
  failure or choose a deliberate constant rendering policy outside the tool.
- Multi-valued DICOM window tags are reduced to their first value by this tool;
  a caller needing a different VOI selection must make that choice explicit.
- DICOM transfer syntaxes may need optional pydicom pixel handlers. A readable
  file header does not guarantee that `pixel_array` is decodable.
- Photometric interpretation, orientation, and inversion are reported in part
  through metadata but are not fully normalized by the converter.

## PNG/JPG pixel handling

The visualizer reads the file with `skimage.io.imread` only when its rendering
method is used. Its colormap behavior is:

- `cmap="rgb"`: pass the loaded array to matplotlib with no explicit colormap;
- another `cmap`: pass that name to matplotlib;
- when the array has more than two dimensions and `cmap != "rgb"`, retain only
  the first channel before display.

For chest radiographs, use `gray` for a single-channel display unless the
actual input is intentionally RGB. Do not apply a colormap before a model tool
unless that model's input contract requests a rendered visualization; model
preprocessing belongs to the analysis skill.

## Privacy and metadata

The converter exposes these selected DICOM values when present:

- `PatientID`, `StudyDate`;
- `Modality`, `PixelSpacing`, `BitsStored`;
- `ImageOrientation`, `ImagePosition`;
- selected `WindowCenter` and `WindowWidth`.

This is a reporting convenience, not anonymization. The PNG may also be
sensitive because it contains the radiograph. Apply the caller's approved
retention and access policy to both files. In particular:

1. Do not put patient identifiers or dates in `title`, `description`, chat
   messages, filenames, test reports, or logs.
2. Do not assume a PNG has no identifying information merely because DICOM tags
   were not copied into it.
3. Redact metadata before serializing a result outside the controlled runtime.
4. Preserve the original-to-derivative association in a protected record when
   provenance is needed, but expose only opaque references to downstream UI or
   evaluation outputs.

The validator script intentionally reads only path metadata and a few file
signature bytes. It does not parse DICOM tags or pixel data, so it does not
perform PHI inspection or anonymization.
