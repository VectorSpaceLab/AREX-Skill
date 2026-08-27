# Data and training troubleshooting

## No input files found

### Symptom
`RuntimeError: No input file found in ...`

### Likely cause
The image directory is empty, points to the wrong location, or contains only hidden files/subdirectories.

### Recovery
- Put image files directly under the configured images directory.
- Do not nest class folders or split folders inside `data/imgs` for this loader.
- Run `scripts/validate_dataset_layout.py --images data/imgs --masks data/masks`.

## No mask or multiple masks for an ID

### Symptom
`Either no mask or multiple masks found for the ID ...`

### Likely cause
The mask naming convention does not match the dataset class, or duplicate files share the same basename.

### Recovery
- For Carvana-style masks, use `--carvana` in the bundled validator and ensure masks are named `<id>_mask.<ext>`.
- For generic data, omit `--carvana` and ensure masks are named `<id>.<ext>`.
- Remove duplicate mask files such as both `.png` and `.gif` for the same ID unless you intentionally modify the loader.

## Image and mask sizes differ

### Symptom
`Image and mask <id> should be the same size, but are ...`

### Likely cause
Mask images were generated at a different resolution from the inputs or were resized independently.

### Recovery
Regenerate or resize masks to exactly match input image dimensions before training. The loader scales both image and mask after this equality check, so pre-scale dimensions must match.

## Scale too small

### Symptom
`Scale is too small, resized images would have no pixel` or validator reports zero resized dimensions.

### Likely cause
`--scale` is so small that `int(scale * width)` or `int(scale * height)` becomes zero.

### Recovery
Increase `--scale`, use larger input images, or validate with the bundled helper before training.

## Channel mismatch

### Symptom
`Network has been defined with 3 input channels, but loaded images have 1 channels...`

### Likely cause
The training CLI constructs `UNet(n_channels=3, ...)`, but the dataset contains grayscale images.

### Recovery
- Convert images to RGB before using the stock CLI.
- Or adapt the model construction programmatically to use `n_channels=1`.
- Route architecture-specific changes through the `model-api` sub-skill.

## Label range or class-count mismatch

### Symptom
- Evaluation asserts true mask indices should be in `[0, n_classes[`.
- Loss errors because target classes exceed model outputs.

### Likely cause
`--classes` is lower than the number of discovered `mask_values`, or the mask palette has unexpected values.

### Recovery
Inspect the validator's `mask_values_sample` and set `--classes` to match the number of semantic labels. Clean masks that contain stray antialiasing values or colors.

## W&B import or logging issues

### Symptom
- `ModuleNotFoundError` for W&B dependencies.
- W&B asks for login, stalls, or fails in an offline environment.

### Likely cause
Training initializes W&B by default. Older `wandb==0.13.5` can also require `pkg_resources` compatibility from setuptools.

### Recovery
- Install dependencies from the repo requirements and retain setuptools compatibility when needed.
- Configure W&B offline/disabled behavior externally before training if network is unavailable.
- Do not start a real training run merely to inspect CLI flags.

## CUDA out of memory

### Symptom
`torch.cuda.OutOfMemoryError` during training.

### Likely cause
Batch size, image scale, or resolution is too high for the device.

### Recovery
- Lower `--batch-size`.
- Lower `--scale`.
- Add `--amp` on a compatible CUDA GPU.
- Let the CLI retry with `model.use_checkpointing()` if the initial attempt fails, understanding that it slows training.

## Kaggle download blocked

### Symptom
The data helper asks for credentials, cannot find `~/.kaggle/kaggle.json`, fails to install `kaggle`, cannot download archives, or cannot unzip them.

### Likely cause
The helper is credentialed and network-dependent.

### Recovery
Ask the user for explicit approval and required credentials before data acquisition. Prefer validating already-provided data with the bundled validator. Do not treat Kaggle download failure as a model or training-code failure.
