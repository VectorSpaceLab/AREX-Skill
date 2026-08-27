# IO Troubleshooting

## Unable to Determine ImageIO

Symptoms include errors that SimpleITK cannot determine an ImageIO reader/writer, cannot write a filename with no usable suffix, or rejects a forced backend.

Actions:

- Check that the path exists, is readable, and points to a file for single-image reads.
- Use a known suffix such as `.mha`, `.nrrd`, `.nii.gz`, `.png`, `.tif`, `.tiff`, `.jpg`, or `.dcm`.
- Inspect registered reader backends with `sitk.ImageFileReader().GetRegisteredImageIOs()` and writer backends with `sitk.ImageFileWriter().GetRegisteredImageIOs()`.
- Force the backend only when appropriate: `sitk.ReadImage(path, imageIO="GDCMImageIO")`, `sitk.WriteImage(image, path, imageIO="NrrdImageIO")`, or `reader.SetImageIO("PNGImageIO")`.
- For DICOM directories, use `ImageSeriesReader.GetGDCMSeriesIDs()` and `GetGDCMSeriesFileNames()` instead of `ReadImage(directory)`.

## Missing Backend

If an expected backend such as `GDCMImageIO`, `NiftiImageIO`, or `PNGImageIO` is absent:

- Confirm you are inspecting the correct object: `sitk.ImageFileReader().GetRegisteredImageIOs()` for reads and `sitk.ImageFileWriter().GetRegisteredImageIOs()` for writes.
- Choose a format supported by the installed SimpleITK build, usually `.mha`/`MetaImageIO` for broad smoke-test compatibility.
- Do not assume optional wrappers such as `ElastixImageFilter` or `TransformixImageFilter` are available; they are not required for core image or transform IO.
- If the task specifically needs a missing backend, report the missing backend and ask for an install/build that includes it rather than silently changing the data format.

## Empty DICOM Series

If `sitk.ImageSeriesReader.GetGDCMSeriesIDs(directory)` returns no IDs:

- Confirm the directory contains DICOM slice files, not only nested folders, archives, thumbnails, JSON sidecars, or converted PNG/JPEG exports.
- Try discovery on the subdirectory that directly contains the slice files.
- Confirm `GDCMImageIO` appears in `sitk.ImageFileReader().GetRegisteredImageIOs()`.
- Probe one suspected file with `ImageFileReader`, `SetImageIO("GDCMImageIO")`, and `ReadImageInformation()`.
- Check permissions, zero-byte files, anonymization damage, and whether the files require external decompression.

If multiple IDs are returned, print every ID with its file count and choose the intended acquisition deliberately.

## Directory Passed to `ReadImage`

A directory is not a single image file. Passing a DICOM directory to `ReadImage` commonly fails or reads the wrong thing. Use this pattern instead:

```python
series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(input_dir)
file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(input_dir, series_ids[0])
reader = sitk.ImageSeriesReader()
reader.SetFileNames(file_names)
image = reader.Execute()
```

## Lossy Casts and Display Formats

Reading with `outputPixelType` or `SetOutputPixelType()` performs a cast. Narrowing conversions can clip, wrap, round, or lose precision. Vector-to-scalar conversions may assume RGB/RGBA semantics and may be wrong for non-color vector data.

Actions:

- Read once without a cast and inspect `sitk.GetPixelIDValueAsString(image.GetPixelID())`.
- Use `sitk.sitkFloat32` or `sitk.sitkFloat64` casts for registration only when the downstream algorithm requires float images.
- For PNG/JPEG display output, explicitly rescale intensity and cast to `sitk.sitkUInt8` so value loss is intentional.
- Do not compare `sitk.Hash` values across JPEG writes, display rescaling, or deliberate pixel type casts.

## Compression and Format Failures

- JPEG is lossy; successful write/read does not imply pixel equality.
- Some formats cannot represent 3D volumes, vector pixels, signed or 64-bit integer pixels, or full spatial metadata.
- Compression levels and compressor names are backend-specific; unsupported settings can fail at write time.
- If a writer fails for quantitative data, switch to `.mha` or `.nrrd` before changing pixel type or dropping metadata.

## Transform IO Pitfalls

- A transform file suffix selects transform IO; unsupported suffixes fail even when the transform object is valid.
- Text formats such as `.tfm` are convenient for small transforms but poor choices for large displacement fields.
- Binary formats such as `.hdf` or `.mat` are better for displacement-heavy or composite transforms when supported.
- Compare transform parameters and test point mappings after reading; do not assume a loaded transform is semantically equivalent because the read succeeded.
- Registration-generated transform stacks, displacement interpretation, and resampling side effects belong in `../registration-transforms/SKILL.md`.

## Minimal Debug Probe

```python
import SimpleITK as sitk

print("read ImageIOs", sitk.ImageFileReader().GetRegisteredImageIOs())
print("write ImageIOs", sitk.ImageFileWriter().GetRegisteredImageIOs())

reader = sitk.ImageFileReader()
reader.SetFileName("input-file")
reader.ReadImageInformation()
print(reader.GetSize(), sitk.GetPixelIDValueAsString(reader.GetPixelID()))
print(reader.GetMetaDataKeys())
```

Use this probe for one readable image file. For DICOM directories, probe one slice and run series discovery on the containing directory separately.

## Evidence

Distilled from SimpleITK IO documentation, ImageIO selection examples, DICOM tag and series examples, and Python IO tests. The diagnostic snippets here are self-contained.
