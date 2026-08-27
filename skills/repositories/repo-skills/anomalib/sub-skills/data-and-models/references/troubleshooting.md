# Troubleshooting guide

This reference collects the failure modes that matter most for data/layout and model-selection questions.

## 1) Layout and path failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MVTecAD` cannot find the dataset or a category folder | `root` does not point at the dataset root, or `category` is wrong | Point `root` at the dataset directory that contains the category folders, and make sure the category exists. Call `prepare_data()` if you want anomalib to download the benchmark. |
| `Folder` raises an error about missing folders | `normal_dir` is required and the relative path is wrong | Recheck `root` plus each subdirectory argument. Relative paths are resolved against `root`. |
| `Folder` says extensions are invalid or no images were found | `extensions` do not start with a dot, or the directories are empty | Use dot-prefixed suffixes such as `(".png", ".jpg")` and confirm the folders contain images. |
| `Folder` or `Tabular` appears to have mismatched masks | image and mask stems do not match | Make the abnormal image stem and mask stem line up, such as `001.png` ↔ `001_mask.png` or `001.png` ↔ `001.png` depending on the dataset convention. |
| `Tabular` fails after loading a file with mixed `Path` / string paths | The paths themselves are fine, but another column is invalid | Mixed path types are acceptable in memory; the common failure is usually an invalid split label, a missing file, or `None` / `NaN` introduced during normalization. If the raw parser trips a dtype-conversion issue, use the bundled validator to isolate the offending column or value. |
| `Tabular` reports `None` or `NaN` values | An invalid `split` or label mapping produced missing values | Check that split labels are only `train`, `val`, or `test`, and that every row has a usable `label_index`, `label`, or `split` column combination. |
| `PredictDataset` has no items | The path is not a file or directory of images | Point it at either a single image file or a directory of images that `get_image_filenames()` can discover. |
| Video loading fails with a message about `av` | The video extra is missing | Install `anomalib[video]` or the `av` package. The video clip indexer depends on `av` when it is available. |
| `Avenue` mask lookup looks wrong | The `gt_dir` path is not aligned with `root`, or the converted masks are missing | Make sure `root` and `gt_dir` belong to the same Avenue checkout and that the ground-truth masks exist under `testing_label_mask/`. |
| Depth items look misaligned | RGB, depth, and mask paths were not paired consistently | Keep the RGB path, depth path, and optional mask path aligned by filename stem. |

## 2) Path-validation errors

`anomalib.data.utils.path.validate_path()` is strict by design.

Common messages and what they mean:

- `TypeError`: the input was not a string or `Path`
- `Path is too long`: the path exceeded the maximum length guard
- `Path contains non-printable characters`: sanitize the string before retrying
- `FileNotFoundError`: the file or directory does not exist when existence is required
- `PermissionError`: the process cannot read or execute the path
- `Path extension is not accepted`: the suffix is not in the allowed extension set

Practical tips:

- For folder-style datasets, always use dot-prefixed extensions like `(".png", ".bmp")`
- Use relative subdirectory names when you want `root` to anchor the layout
- If a path seems valid but still fails, check for hidden characters or trailing whitespace in the config

## 3) Dataclass validation errors

Typical causes:

- `ImageItem` or `VideoItem` was given a batched tensor instead of a single item
- `ImageBatch` / `VideoBatch` received tensors with inconsistent batch dimensions
- `DepthItem` was missing one of the paired RGB/depth tensors

Fix:

- Match the modality shape exactly
- Use the item type for one sample and the batch type for a collated batch
- Let the dataset / dataloader build the batch when possible

## 4) Feature extractor mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| PatchCore or PaDiM warns that a layer was not found | The backbone's feature-map names do not match the `layers` argument | Inspect the backbone's feature info and pick valid layer names. |
| A transformer backbone fails in feature extraction | The extractor is in the wrong mode or the layer names are not `blocks.<index>` | Use `TimmFeatureExtractor(..., output_fmt="NLC")` and transformer block names. |
| No features are extracted after filtering | Every requested layer name was invalid | Double-check the timm layer names and rerun a dry-run feature-map check. |
| Model output sizes do not match the image size you expected | Backbone / layer / input-size combination changed the spatial reduction | Use `dryrun_find_featuremap_dims()` before finalizing the config. |

Helpful checks:

- `resnet18` commonly works with `layer1`, `layer2`, `layer3`
- `wide_resnet50_2` commonly works with `layer2`, `layer3`
- `mobilenetv3_large_100` commonly uses `blocks.4.1` and `blocks.6.0`
- transformer backbones often need `blocks.2`, `blocks.9`, or similar indices

## 5) Registry and class-path errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `UnknownModelError` from `get_model()` | The model name does not match a registered class | Use `list_models()` to discover the current names, then retry with a class name or known alias. |
| `UnknownDatamoduleError` from `get_datamodule()` | The `data.class_path` does not correspond to a datamodule in `anomalib.data` | Use one of the public datamodule class names and keep the class path inside `anomalib.data`. |
| Import from a fully qualified model path is rejected | The path points outside the allowed anomalib modules | Keep the class path under `anomalib.models`, `anomalib.models.image`, `anomalib.models.video`, or `anomalib.models.components`. |
| `list_models(case="snake")` looks odd for acronym-heavy names | The snake-case conversion is mechanical | Prefer `pascal` output for discovery, or use the class name directly in `get_model()`. |

## 6) Optional dependency notes

The codebase guards several subfamilies with imports that may be absent in a minimal environment.

| Surface | Missing dependency | What happens | What to install |
| --- | --- | --- | --- |
| Video dataloading / clip indexing | `av` | Video clip indexing raises an import error | `anomalib[video]` or `av` |
| WinCLIP / CLIP-style VLM detection | `open_clip` | The model raises an import error at construction time | `anomalib[clip]` and usually `anomalib[vlm]` |
| AnomalyVFM | `huggingface_hub`, `safetensors` | The model refuses to initialize without them | `anomalib[huggingface]` |
| VLM-AD backends | `transformers`, `ollama`, `openai`, `dotenv` | Backend-specific code raises a clear dependency error | `anomalib[vlm]` plus the backend you actually want |
| Kaputt / parquet-backed data loading | `pyarrow` | Parquet readers are unavailable | `pyarrow` or `anomalib[datasets]` |
| Fuvas backbone download path | network access to `torch.hub` / torchvision assets | The first initialization may need network access | Pre-download the requested backbone or work from a connected environment |

## 7) Practical recovery pattern

When a user says "the layout looks right but it still fails":

1. Check the exact root and category/root-subdir pairing.
2. Check file extensions and hidden characters.
3. Check mask stems.
4. Check split labels.
5. Check the model's backbone / layer names.
6. Run the bundled inspection script to reproduce the parser behavior directly.
