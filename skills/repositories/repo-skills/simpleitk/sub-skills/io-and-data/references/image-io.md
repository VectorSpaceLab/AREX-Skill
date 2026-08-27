# Image IO

SimpleITK supports procedural image IO for short workflows and object-oriented reader/writer classes for backend selection, metadata probing, staged configuration, and diagnostic output.

## Procedural Reads and Writes

```python
import SimpleITK as sitk

image = sitk.ReadImage("input.mha")
sitk.WriteImage(image, "output.nrrd")
```

`ReadImage(fileName, outputPixelType=-1, imageIO='')` accepts a single filename/path-like object or an ordered sequence of filenames for slice-series reads. `WriteImage(image, fileName, useCompression=False, compressionLevel=-1, *, imageIO='', compressor='')` accepts a single output filename/path-like object or a sequence when writing an image series.

Use the procedural form when the file suffix/header can identify the backend, the task is a straightforward conversion, or the input sequence has already been sorted and validated.

```python
fixed = sitk.ReadImage("fixed.nii.gz", outputPixelType=sitk.sitkFloat32)
sitk.WriteImage(fixed, "fixed_float.mha", useCompression=True)
```

## Object-Oriented Reader and Writer

```python
import SimpleITK as sitk

reader = sitk.ImageFileReader()
reader.SetFileName("input.png")
reader.SetImageIO("PNGImageIO")
reader.SetOutputPixelType(sitk.sitkFloat32)
image = reader.Execute()

writer = sitk.ImageFileWriter()
writer.SetFileName("output.mha")
writer.UseCompressionOn()
writer.Execute(image)
```

Use `ImageFileReader` and `ImageFileWriter` when you need to:

- Force a backend with `SetImageIO("PNGImageIO")`, `SetImageIO("GDCMImageIO")`, `SetImageIO("NrrdImageIO")`, or another registered backend.
- Call `ReadImageInformation()` before loading pixels, then inspect `GetSize()`, `GetSpacing()`, `GetPixelID()`, and metadata keys.
- Enable DICOM private tag metadata before probing with `LoadPrivateTagsOn()`.
- Configure compression with `UseCompressionOn()`, `SetCompressionLevel()`, or a writer-specific compressor option before `Execute()`.

## ImageIO Discovery and Forcing

SimpleITK usually selects ImageIO from the filename suffix and/or file header. Force `imageIO` only when auto-selection is ambiguous, the suffix is absent or misleading, or the workflow must be constrained to a backend such as DICOM/GDCM.

```python
reader_ios = tuple(sitk.ImageFileReader().GetRegisteredImageIOs())
writer_ios = tuple(sitk.ImageFileWriter().GetRegisteredImageIOs())
print("readers", reader_ios)
print("writers", writer_ios)

image = sitk.ReadImage("scan.dcm", imageIO="GDCMImageIO")
sitk.WriteImage(image, "scan.nrrd", imageIO="NrrdImageIO")
```

Registered IO discovery is exposed through `ImageFileReader().GetRegisteredImageIOs()` and `ImageFileWriter().GetRegisteredImageIOs()`; use those object methods in Python examples for this skill.

Common backend names depend on the build and may include `MetaImageIO` for `.mha/.mhd`, `NrrdImageIO` for `.nrrd/.nhdr`, `NiftiImageIO` for `.nii/.nii.gz`, `GDCMImageIO` for DICOM, `PNGImageIO`, `TIFFImageIO`, and `JPEGImageIO`.

## File Suffix Choices

- Use `.mha` or `.mhd` (`MetaImageIO`) for simple, deterministic, metadata-preserving medical/scientific image round trips.
- Use `.nrrd` or `.nhdr` (`NrrdImageIO`) for metadata-preserving scalar or vector data.
- Use `.nii` or `.nii.gz` (`NiftiImageIO`) when downstream neuroimaging tools expect NIfTI.
- Use `.png` or `.tif/.tiff` for 2D display/interchange after verifying pixel type and dynamic range.
- Avoid `.jpg/.jpeg` for quantitative values or equality tests because JPEG compression is lossy.
- Use DICOM via `GDCMImageIO` only when the task truly requires DICOM files or metadata; ordinary volume interchange is usually safer with `.mha`, `.nrrd`, or `.nii.gz`.

## Pixel Type Casts During Reads

`ReadImage(..., outputPixelType=...)` and `reader.SetOutputPixelType(...)` cast pixels while reading.

```python
moving = sitk.ReadImage("moving.nii.gz", outputPixelType=sitk.sitkFloat32)

reader = sitk.ImageFileReader()
reader.SetFileName("labels.nrrd")
reader.SetOutputPixelType(sitk.sitkUInt16)
labels = reader.Execute()
```

This is useful for registration workflows that require floating-point inputs. It can also lose information: narrowing from floating point or 64-bit integer types to `sitkUInt8` can clip, round, or otherwise change values, and vector-to-scalar conversions assume common RGB/RGBA semantics that may be wrong for non-color vector images. Read without a cast first when the source type is unknown.

## Compression and Compressor Options

Procedural writes support `useCompression`, `compressionLevel`, keyword-only `imageIO`, and keyword-only `compressor`:

```python
sitk.WriteImage(image, "compressed.tif", useCompression=True, compressionLevel=1, compressor="DEFLATE")
sitk.WriteImage(image, "volume.nrrd", useCompression=True, imageIO="NrrdImageIO")
```

Compression behavior is ImageIO-specific. A compressor accepted for TIFF may be meaningless for another backend. If a writer rejects a compression option, first retry with a simple lossless format (`.mha` or `.nrrd`) before changing the image's pixel type.

## Round-Trip Validation Checklist

1. Choose a deterministic lossless suffix such as `.mha` or `.nrrd` in a temporary directory.
2. Write with explicit compression/backend options only when those options are part of the behavior under test.
3. Read back using auto-selection or the same forced `imageIO`.
4. Compare `GetSize()`, `GetPixelID()`, `GetSpacing()`, `GetOrigin()`, and `GetDirection()`.
5. Compare `sitk.Hash(original)` and `sitk.Hash(read_back)` only for lossless formats and unchanged pixel types.
6. Verify required metadata with `HasMetaDataKey()` and `GetMetaData()` only for formats expected to preserve those keys.

For a bundled deterministic check, use `../scripts/io_roundtrip_smoke.py`.

## Evidence

Distilled from SimpleITK IO documentation, the `SimpleIO` and `ImageIOSelection` examples, and Python image read/write tests. The bundled examples here are self-contained and do not require those source files at runtime.
