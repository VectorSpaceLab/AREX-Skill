# Testing troubleshooting

## Fast triage order

1. Run `scripts/check_checkpoints.py` for the intended `--model` stage.
2. Confirm the command includes the intended `--checkpoints`, `--input`, `--mask`, and `--output` paths.
3. Check whether `config.yml` has `EDGE: 1` or `EDGE: 2`.
4. For directory inputs, compare the sorted image, mask, and optional edge lists.
5. If startup fails before model loading, check legacy dependency compatibility.

## Symptom matrix

| Symptom | Likely cause | Concrete fix |
| --- | --- | --- |
| `config.yml` is missing | The checkpoint directory is empty, wrong, or points at a parent directory | Put the intended `config.yml` directly in the checkpoint directory, or select the leaf directory that contains it. Do not rely on startup auto-copy unless you intentionally want a fresh template config. |
| A new generic config appears in the checkpoint directory | Startup fallback copied `config.yml.example` from the launch working directory | Replace it with the run-specific config before testing. Review `EDGE`, `GPU`, `DEBUG`, and any test path defaults. |
| Output is noise or not meaningfully inpainted, but the command did not fail | A required generator checkpoint is absent; the model can remain randomly initialized | For `--model 1`, provide `EdgeModel_gen.pth`. For `--model 2`, provide `InpaintingModel_gen.pth`. For `--model 3` or `4`, provide both. Run `scripts/check_checkpoints.py` first. |
| Only `*_dis.pth` files are present | Discriminator files are training companions, not inference weights | Recover the matching `*_gen.pth` generator files for the selected stage. |
| `--model 3` or `--model 4` fails or produces poor output with only one generator file | Edge-then-inpaint inference needs both model families | Use a checkpoint directory containing both `EdgeModel_gen.pth` and `InpaintingModel_gen.pth`, or switch to the stage that matches the available generator. |
| `--edge` seems ignored | The config has `EDGE: 1`, so the dataset computes Canny edges | Set `EDGE: 2` in `config.yml` when external edge maps should be consumed. |
| External-edge run crashes or prints loading errors | The config has `EDGE: 2`, but `--edge`/`TEST_EDGE_FLIST` is missing or shorter than the image list | Provide an edge file, directory, or flist aligned one-to-one with the input images; or change the config to `EDGE: 1` to use Canny. |
| Directory input appears empty | The loader only reads top-level lower-case `*.jpg` and `*.png` files | Build explicit flists or rename/copy files into a flat directory with supported suffixes. Flist construction belongs to `data-preparation`. |
| Image/mask pairs are mismatched | Directories or flists sort differently | Compare ordered lists before running. Prefer matching basenames and explicit flists for nontrivial datasets. |
| Mask covers the wrong region | Mask polarity is inverted or mask values are not thresholded as expected | Use masks where pixels greater than zero mark the missing/fill region and zero marks the kept region. White means fill; black means keep. |
| Mask dimensions differ from the image | The test loader resizes masks to image size | Prepare same-size masks when quality matters; resized masks can shift boundaries or blur edges before thresholding. |
| Results overwrite each other | Input basenames collide in the same output directory | Use unique basenames, split the run into separate output directories, or create a flattened input set with unique names. |
| No output directory was expected, but files appear under checkpoints | `--output` was omitted and no config `RESULTS` override was set | Pass `--output <output-dir>` explicitly for every test command unless checkpoint-local `results/` is intended. |
| Debug output crashes for names like `case.v1.png` | Debug naming splits the filename on a single dot | Rename inputs to single-dot basenames or set `DEBUG: 0` before running. |
| CPU run is unexpectedly slow | CUDA is unavailable or not selected by the runtime | For quick checks, reduce the input set. For production inference, use a CUDA-capable environment and a `GPU` list matching available devices. |
| CUDA is expected but the run falls back to CPU | Torch does not report CUDA available after visible-device filtering | Check the runtime's CUDA-enabled Torch installation and the config `GPU` list. Use a small smoke command before a large directory run. |
| Import/startup fails around SciPy, NumPy, scikit-image, or OpenCV before model code runs | The project uses legacy image APIs and removed NumPy aliases | Use a legacy-compatible dependency set for this repository. Treat this as environment compatibility, not bad checkpoints. |

## Missing checkpoint advice by stage

| Intended command | Minimum files to add before running |
| --- | --- |
| `python test.py --model 1 ...` | `config.yml`, `EdgeModel_gen.pth` |
| `python test.py --model 2 ...` | `config.yml`, `InpaintingModel_gen.pth` |
| `python test.py --model 3 ...` | `config.yml`, `EdgeModel_gen.pth`, `InpaintingModel_gen.pth` |
| `python test.py --model 4 ...` | `config.yml`, `EdgeModel_gen.pth`, `InpaintingModel_gen.pth` |

Add `EdgeModel_dis.pth` and/or `InpaintingModel_dis.pth` when a complete training-resume bundle is required, but do not treat discriminator files as a substitute for generator files.

## Output path behavior

The result directory is selected in this order:

1. CLI `--output`, if supplied.
2. `RESULTS` from `config.yml`, if non-null.
3. `results/` inside the checkpoint directory.

The test loop creates the directory if needed. It does not create per-subfolder output structure; all result basenames are written into the selected output directory.

## Config copy behavior

The startup loader creates the checkpoint directory if it is missing. If `config.yml` is also missing, it tries to copy a template named `config.yml.example` from the current launch directory. This behavior is convenient during development but risky for repeatable inference because it can hide a wrong checkpoint path.

Preferred practice:

- Create or copy the intended `config.yml` into the checkpoint directory before launch.
- Run `scripts/check_checkpoints.py` before `test.py`.
- Pass explicit `--input`, `--mask`, `--edge` when needed, and `--output` so test paths do not depend on stale config values.

## External edge requirements

When `EDGE: 2` is active:

- Every input image needs an aligned external edge image.
- The edge path can be a single file, directory, or flist, but it must pair by index with the input images.
- `NMS: 1` multiplies external edges by Canny edges after resizing.

When `EDGE: 1` is active:

- Do not supply external edge maps unless you are only preparing a config override for later.
- Canny edges are computed from the grayscale input image, with the masked region excluded in test mode.

## Boundary with other sub-skills

- Use `data-preparation` to build flists, flatten directories, or validate config path keys.
- Use `training` to produce, resume, or explain checkpoint training.
- Use `evaluation` for PSNR, SSIM, MAE, FID, or metric-script troubleshooting after inference outputs exist.
