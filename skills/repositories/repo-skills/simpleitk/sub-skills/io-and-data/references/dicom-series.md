# DICOM Series

DICOM volumes are usually stored as a directory of slice files rather than a single image file. Use GDCM series discovery, select the intended series, and pass the scan-direction-sorted filenames to `ImageSeriesReader`.

## Directory to Volume Workflow

```python
import SimpleITK as sitk

input_dir = "dicom-directory"
series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(input_dir)
if not series_ids:
    raise RuntimeError(f"No DICOM series found in {input_dir!r}")

for series_id in series_ids:
    names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(input_dir, series_id)
    print(series_id, len(names))

selected_id = series_ids[0]
file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(input_dir, selected_id)
reader = sitk.ImageSeriesReader()
reader.SetFileNames(file_names)
image = reader.Execute()
sitk.WriteImage(image, "series.mha")
```

The filenames returned by `GetGDCMSeriesFileNames` are sorted for volume assembly. Do not replace them with an arbitrary filesystem listing; filename order often differs from acquisition order.

## Choosing a Series ID

A DICOM directory can contain multiple studies, acquisitions, localizers, derived images, or repeated reconstructions. Always inspect all `series_ids` and file counts before selecting one.

```python
summary = []
for series_id in sitk.ImageSeriesReader.GetGDCMSeriesIDs(input_dir) or []:
    names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(input_dir, series_id)
    summary.append({"series_id": series_id, "file_count": len(names)})
print(summary)
```

Select deliberately based on the task's expected modality, file count, slice geometry, or metadata. If no task-specific series is identified, report the available IDs instead of silently using the first one.

## Metadata and Tags

For a single DICOM file or metadata-only inspection, use `ImageFileReader`:

```python
reader = sitk.ImageFileReader()
reader.SetFileName("slice.dcm")
reader.SetImageIO("GDCMImageIO")
reader.LoadPrivateTagsOn()
reader.ReadImageInformation()

print(reader.GetSize(), sitk.GetPixelIDValueAsString(reader.GetPixelID()))
for key in reader.GetMetaDataKeys():
    print(key, reader.GetMetaData(key))
```

DICOM tag keys in SimpleITK metadata are commonly lowercase hexadecimal group/element strings separated by `|`, such as `0020|000e` for Series Instance UID and `0020|0013` for Instance Number. Some older examples or external DICOM tools use comma notation such as `0020,000d`; normalize spelling and lowercase when comparing keys.

For a series read, enable metadata dictionary updates before `Execute()` when per-slice tags are needed:

```python
reader = sitk.ImageSeriesReader()
reader.SetFileNames(file_names)
reader.MetaDataDictionaryArrayUpdateOn()
reader.LoadPrivateTagsOn()
image = reader.Execute()

first_slice_keys = reader.GetMetaDataKeys(0)
if "0020|000e" in first_slice_keys:
    print(reader.GetMetaData(0, "0020|000e"))
```

Per-slice tags do not automatically become reliable volume-level metadata. Inspect individual files or `ImageSeriesReader` metadata arrays when downstream logic depends on slice-specific tags.

## Multi-Series and Directory Pitfalls

- `ReadImage("dicom-directory")` is not the DICOM volume workflow; use `ImageSeriesReader` discovery and sorted filenames.
- `GetGDCMSeriesIDs(directory)` can return an empty tuple/list if the directory contains nested folders, non-DICOM exports, compressed archives, thumbnails, unreadable files, or no `GDCMImageIO` support.
- Recursive layouts may require walking subdirectories and running discovery where slices actually live.
- Multiple series IDs may represent localizer images, derived images, or different acquisitions; first ID is not necessarily the target.
- Missing or duplicate slices, inconsistent geometry, or mixed studies can produce warnings or a misleading volume; validate size, spacing, direction, and slice count.
- DICOM metadata can contain protected health information; avoid printing, copying, or storing patient tags unless the task explicitly requires it and the user has permission.

## Writing DICOM or Converted Output

After `reader.Execute()`, write an assembled volume to a regular image format for analysis or interchange:

```python
sitk.WriteImage(image, "converted.nrrd")
```

Prefer `.mha`, `.nrrd`, or `.nii.gz` for converted 3D volumes. Use `.png`, `.jpg`, or other 2D display formats only after extracting or rescaling a slice deliberately.

Writing a modified DICOM series is possible but delicate: many study, series, frame-of-reference, geometry, date/time, and derived-image tags must be set or updated correctly. For routine agent work, prefer writing a converted lossless volume unless the task specifically requires DICOM output and supplies the required metadata policy.

## No Synthetic Full-DICOM Dependency

This skill does not require or bundle a synthetic DICOM dataset. DICOM examples here are reference workflows for user-supplied directories. For deterministic install checks, use generated MHA and transform data via `../scripts/io_roundtrip_smoke.py` instead of fabricating a full DICOM study.

## Evidence

Distilled from SimpleITK DICOM reader, converter, tag-printing, series-read/modify/write examples, and Python `GetGDCMSeriesIDs` tests. The bundled guidance is self-contained and does not require those source examples at runtime.
