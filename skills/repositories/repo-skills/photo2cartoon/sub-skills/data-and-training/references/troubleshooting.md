# Troubleshooting

## Missing split folders

**Symptom:** training fails before the first step, or the validator reports a missing split.

**Likely cause:** the dataset root does not contain all four required folders: `trainA`, `trainB`, `testA`, `testB`.

**Fix:** create the missing split directories and place the correct domain images in each one, then rerun the bundled validator.

## Zero image files

**Symptom:** `ImageFolder` raises `RuntimeError("Found 0 files in subfolders of: ...")`.

**Likely cause:**

- the split folder is empty
- every file uses an unsupported suffix
- the files are nested outside the split root you pointed at
- preprocessing skipped every source image because face detection returned `None`

**Fix:** verify the split root, count the supported suffixes, and inspect a few preprocessed portraits before training.

## Unsupported extensions

**Symptom:** files exist, but the loader still sees no data.

**Likely cause:** the loader only accepts `.jpg`, `.jpeg`, `.png`, `.ppm`, `.bmp`, `.pgm`, and `.tif`.

**Fix:** convert the files to one of the supported extensions or update the loader and validator together in your fork. The batch preprocessor is also not recursive, so keep the source photo folder flat and avoid directory entries or unreadable files.

## RGB / BGR confusion

**Symptom:** colors look swapped or the preprocessing output looks wrong.

**Likely cause:** OpenCV reads and writes BGR arrays, while `ImageFolder` returns RGB images through Pillow.

**Fix:** keep the original preprocessing contract intact:

- `data_process.py` reads with OpenCV, converts BGR to RGB for preprocessing, then converts back before writing
- training reads the saved files through Pillow as RGB

## Missing MobileFaceNet weights

**Symptom:** training crashes during model build when the face feature extractor is created.

**Likely cause:** the trainer loads `models/model_mobilefacenet.pth` immediately inside the training model.

**Fix:** place the weight file where the trainer expects it before launch, or do not start training until the file is available.

## Batch size too large

**Symptom:** CUDA OOM, severe slowdown, or unstable training.

**Likely cause:** the training step is expensive: two generators, four discriminators, data augmentation, and Face ID extraction run every iteration.

**Fix:**

- use `--batch_size 1` first
- keep multi-GPU only when the single-GPU batch already fits
- reduce `--img_size` or `--ch` only if you understand checkpoint compatibility trade-offs

## Checkpoint load mismatch

**Symptom:** `load_state_dict` fails for `--pretrained_weights` or resume.

**Likely cause:** the checkpoint does not contain all six keys, or the current run uses different shape-sensitive settings such as `--light`, `--ch`, or `--img_size`.

**Fix:** use a checkpoint produced by the same configuration and keep the `%07d` naming pattern intact.

## Resume finds nothing

**Symptom:** `--resume true` starts from step 1 or `--phase test` prints load failure.

**Likely cause:** the run root changed because the CLI arguments changed, or `.../photo2cartoon/model/` has no saved `.pt` files.

**Fix:** reuse the exact same launch configuration that created the checkpoint, and confirm that the model folder contains numbered checkpoint files.

## FID / best-model expectations

**Symptom:** you need the best checkpoint, but `train.py` only gives you the latest saved file.

**Likely cause:** the trainer does not compute FID or automatically pick the best model.

**Fix:** run your own validation or FID selection outside this trainer. The repo docs describe manual selection after long training runs.

## Instability from Face ID loss

**Symptom:** results are unstable or over-constrained.

**Likely cause:** the Face ID term is too strong for the data you are using.

**Fix:** try `--faceid_weight 0` as a diagnostic run and compare the outputs.
