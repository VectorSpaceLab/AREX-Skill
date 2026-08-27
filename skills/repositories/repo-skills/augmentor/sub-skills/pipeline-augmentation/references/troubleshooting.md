# Pipeline Troubleshooting

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `IOError: The source directory you specified does not exist.` | `source_directory` path is wrong or unavailable. | Resolve the path before constructing `Pipeline`; use an absolute path or a path relative to the current process. |
| Initialization says `0 image(s) found` | Empty directory, unsupported extension, images are nested too deeply, or root images are ignored because class subfolders exist. | Check the layout rules in [data-layouts.md](data-layouts.md); move images into direct source/class folders or flatten nested directories. |
| `IndexError: There are no images in the pipeline...` during `sample()` | The scan found no images. | Fix the source layout, then reconstruct the pipeline so it rescans. |
| `IndexError: There are no operations associated with this pipeline.` | `sample()` or `process()` was called before adding operations. | Add at least one operation, commonly `resize(probability=1, ...)` for a smoke run. |
| Outputs appear under the source directory instead of the process working directory. | `output_directory` is resolved relative to `source_directory` by normal Augmentor usage. | Treat output as part of the source tree unless intentionally using a different relative path. Confirm the printed output directory after initialization. |
| A class folder is missing from outputs. | `sample(n)` samples with replacement; small `n` may not pick every class. | For class coverage checks, sample more images, call `sample(0)`, or run per-class pipelines. |
| Root-level images are ignored. | Immediate subdirectories make Augmentor use class-subfolder mode. | Put all images in class folders, or remove class subdirectories and use a flat source directory. |
| The existing `output` folder is not treated as a class. | The configured output directory is intentionally ignored during class scanning. | This is expected. If using a custom output name, remember only that custom name is ignored. |
| JPEG save fails for PNG/RGBA images or alpha channels. | JPEG cannot store alpha and Pillow rejects incompatible image modes. | Use `p.set_save_format("PNG")`, or convert images to RGB before forcing JPEG. See the root [save-format troubleshooting](../../../references/troubleshooting.md#save-format-and-pillow-errors) for cross-skill details. |
| An invalid save format fails only when sampling. | `set_save_format()` stores the value; final validation is delegated to Pillow when images are saved. | Use known formats such as `PNG`, `JPEG`, `BMP`, or `GIF`, and run a tiny smoke sample first. |
| Repeated seeded runs differ under multithreading. | Operations use global Python/NumPy random state and multithreaded execution can make exact call order harder to audit. | For deterministic checks, call `p.set_seed(seed)` immediately before sampling and use `p.sample(..., multi_threaded=False)`. Compare counts/dimensions, not UUID filenames. |
| `process()` is not single-threaded. | `process()` calls `sample(0, multi_threaded=True)`. | Use `p.sample(0, multi_threaded=False)` when processing every image once must be single-threaded. |
| `status()` prints but returns nothing useful. | `status()` is a console inspection helper. | Use it for human-readable checks; inspect `len(p.augmentor_images)`, `p.class_labels`, and `len(p.operations)` in code assertions. |

## Safe preflight checklist

Before a large disk run:

1. Construct the pipeline and read the initialization output path.
2. Call `p.status()` and confirm image count, class labels, dimensions, formats, and operation count.
3. Force `PNG` if any source image may have an alpha channel.
4. Run a tiny `p.sample(2, multi_threaded=False)` first.
5. Count output files under the expected output directory and open one with Pillow.
6. Only then scale `sample(n)` or `process()` to the full dataset.

## Difficult but common cases

### Output subfolder ignored during class scan

If this layout exists:

```text
source/
├── cat/
├── dog/
└── output/
```

and the pipeline is `Augmentor.Pipeline("source", output_directory="output")`, `cat` and `dog` are classes while `output` is ignored. This prevents old generated images from becoming a new class when the same source tree is scanned again.

### Deterministic tiny output

```python
import Augmentor

p = Augmentor.Pipeline("source")
p.rotate90(probability=1)
p.resize(probability=1, width=24, height=24)
p.set_save_format("PNG")
p.set_seed(123)
p.sample(2, multi_threaded=False)
```

Expected assertions for a deterministic smoke check: two readable output files exist, their dimensions are `24 x 24`, and the configured output directory was ignored as a class. Do not assert exact output filenames because Augmentor uses UUIDs.
