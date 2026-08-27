---
name: io-and-data
description: "Read and write SimpleITK images and transforms, choose ImageIO
  backends, discover DICOM series, inspect metadata, and validate safe IO round
  trips."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SimpleITK IO and Data

Use this sub-skill when a task mentions `ReadImage`, `WriteImage`, `ImageFileReader`, `ImageFileWriter`, `ImageSeriesReader`, DICOM series, metadata tags, ImageIO backends, transform IO, or file formats such as MHA, NRRD, NIfTI, PNG, TIFF, JPEG, and DICOM.

## Route by Task

- For procedural and object-oriented image reads/writes, `outputPixelType`, suffix choices, compression, explicit `imageIO`, and registered backend discovery, read [image-io](references/image-io.md).
- For DICOM directory discovery, series IDs, sorted filenames, metadata dictionaries, tag inspection, and multi-series pitfalls, read [dicom-series](references/dicom-series.md).
- For `ReadTransform`/`WriteTransform` workflows, transform format choices, and displacement-field storage caveats, read [transform-io](references/transform-io.md).
- For missing ImageIO backends, empty DICOM discovery, directory-vs-file mistakes, lossy casts, compression surprises, and transform IO failures, read [troubleshooting](references/troubleshooting.md).
- To validate an installed SimpleITK environment with generated data only, run [io_roundtrip_smoke.py](scripts/io_roundtrip_smoke.py).

## Core APIs

- Import the Python package as `import SimpleITK as sitk`; the package distribution is `simpleitk`.
- `sitk.ReadImage(fileName, outputPixelType=-1, imageIO='')` reads a single image file or an ordered filename sequence; use `outputPixelType` only for deliberate casts such as registration float inputs.
- `sitk.WriteImage(image, fileName, useCompression=False, compressionLevel=-1, *, imageIO='', compressor='')` writes one image file or a filename sequence when writing a series.
- `sitk.ImageFileReader()` and `sitk.ImageFileWriter()` provide `SetFileName`, `SetImageIO`, metadata probing, output pixel type selection, compression settings, and registered ImageIO discovery.
- Discover ImageIO backends with `sitk.ImageFileReader().GetRegisteredImageIOs()` or `sitk.ImageFileWriter().GetRegisteredImageIOs()`; do not use a module-level helper for this.
- `sitk.ImageSeriesReader.GetGDCMSeriesIDs(directory)` and `sitk.ImageSeriesReader.GetGDCMSeriesFileNames(directory, seriesID)` discover and sort DICOM slices before `ImageSeriesReader.Execute()` reads them.
- `sitk.ReadTransform(filename)` and `sitk.WriteTransform(transform, filename)` round-trip transforms through supported transform IO formats.

## Boundaries

- For image construction, pixel containers, spacing/origin/direction fundamentals, indexing, and NumPy views, route to `../image-core/SKILL.md`.
- For filters, segmentation, intensity transforms, and algorithms that consume loaded images, route to `../filtering-segmentation/SKILL.md`.
- For registration-generated transforms, transform composition, resampling, displacement-field interpretation, and optimizer-specific output, route to `../registration-transforms/SKILL.md`.
- Optional `ElastixImageFilter` and `TransformixImageFilter` are build-dependent; do not assume they exist in a SimpleITK install.

## Guardrails

- Prefer `.mha` or `.nrrd` for deterministic smoke tests and metadata-preserving examples; avoid JPEG for pixel equality because it is lossy.
- Use DICOM series discovery for directories; do not pass a directory to `ReadImage` and expect a volume.
- Treat DICOM metadata as potentially identifying; inspect or copy only tags required by the task.
- Keep runtime workflows self-contained; examples here use generated data or user-supplied paths and do not depend on the original repository checkout.
