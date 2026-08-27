# Pipeline Data Layouts

`Augmentor.Pipeline` is directory-backed. It scans paths at initialization and stores `AugmentorImage` records containing the image path, output directory, file extension, class label, integer class id, and categorical label.

## Supported disk image extensions

The directory scanner recognizes these extensions: `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.img`, `.png`, `.tif`, and `.tiff`. On non-Windows systems, uppercase variants are also scanned.

## Layout rules

| Source layout | What Augmentor scans | Class labels | Output placement |
| --- | --- | --- | --- |
| `source/` contains images and no subdirectories | Images directly in `source/` | Basename of `source` | `source/output/` by default |
| `source/` contains immediate class subdirectories | Images directly inside each immediate subdirectory | Each immediate subdirectory basename | `source/output/<class>/` when multiple classes exist |
| `source/` contains both root images and class subdirectories | Root images are ignored; class subdirectories define the scan | Immediate subdirectory basenames | Class output directories as above |
| Nested subdirectories under a class folder | Nested images are not scanned by the normal disk pipeline | Only the immediate class folder | No recursive class scan |
| Configured output directory already exists under `source/` | That exact output directory is ignored during class discovery | Other immediate subdirectories only | Existing output is reused |

## Output directory semantics

Constructor defaults:

```python
p = Augmentor.Pipeline(source_directory="source", output_directory="output", save_format=None)
```

Behavior:

- The default output path is named `output` relative to the source directory.
- If the source has multiple class subdirectories, Augmentor writes into output subdirectories named after the class labels.
- The configured output directory is ignored during scanning so generated files do not become a new class on a later initialization.
- If you change `output_directory` to another name, only that configured name is ignored. A folder named `output` can be treated as a class if it is not the configured output folder.
- The pipeline prints the resolved output path when initialized; use that printed path and `p.status()` to confirm a large run.

## Class label details

With class subfolders, Augmentor sorts immediate subdirectories before assigning integer labels. Each image record receives:

- `class_label`: class subfolder basename.
- `class_label_int`: the sorted class index.
- `categorical_label`: a one-hot vector for multi-class scans.

With no class subfolders, every directly scanned image receives the source directory basename as its class label.

## Sampling behavior

- `sample(n)` randomly chooses `n` images from the current pipeline image list with replacement and writes augmented outputs.
- `sample(0)` means “use every current image once”.
- `process()` is a wrapper around `sample(0, multi_threaded=True)`.
- `sample()` raises if the pipeline has zero images or zero operations.

## Save format behavior

- If `save_format` is `None`, output filenames use each input image extension/format.
- `set_save_format("auto")` resets to that per-input behavior.
- `set_save_format("PNG")`, `"JPEG"`, `"BMP"`, or `"GIF"` forces a format at save time when Pillow can write that image mode to that format.
- Use PNG when source images may have an alpha channel; JPEG cannot store alpha without conversion.
