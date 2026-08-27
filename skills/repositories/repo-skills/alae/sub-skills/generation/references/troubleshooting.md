# ALAE generation troubleshooting

Use this checklist when a generation, demo, reconstruction, style-mixing, interpolation, or traversal command fails. Start with the safe checkers; they do not load models or use CUDA.

```bash
python scripts/check_generation_assets.py --repo-root <ALAE-checkout> --config ffhq
python scripts/check_principal_directions.py --repo-root <ALAE-checkout> --inspect-shapes
```

## Missing checkpoint or `last_checkpoint`

Symptoms:

- `FileNotFoundError` near `last_checkpoint`.
- `checkpointer.load()` fails before any images are written.
- The checker reports a missing pointer target.

Fixes:

1. Confirm the selected config's `OUTPUT_DIR` value.
2. Confirm `<OUTPUT_DIR>/last_checkpoint` exists and contains one checkpoint path.
3. If the path is relative, interpret it from the ALAE repository root unless your local training workflow deliberately wrote another convention.
4. Confirm the referenced `.pth` file exists.
5. If using pretrained weights, use the generated root artifact helper when present: `../../scripts/download_alae_artifacts.py` from this sub-skill directory, or `../../../scripts/download_alae_artifacts.py` from this reference directory. If that helper is absent, direct use of the repository manifest is a network action and should be explicitly approved.

A stale `last_checkpoint` can point to a deleted or renamed model. Editing the text file to point to a specific `.pth` checkpoint is supported by the repository's README.

## Missing sample image paths

Symptoms:

- Reconstruction scripts fail at `os.listdir(path)`.
- Interpolation or traversal scripts fail on a specific numbered `.png`.
- The checker reports an empty or missing `DATASET.SAMPLES_PATH`.

Fixes:

1. Inspect `DATASET.SAMPLES_PATH` in the selected config.
2. For general reconstruction pages and multi-resolution reconstruction, provide at least one RGB/RGBA image in that directory.
3. For interpolation, the source script expects `00001.png`, `00022.png`, `00077.png`, and `00016.png` in `DATASET.SAMPLES_PATH`.
4. For traversals, the source script expects the hard-coded sample files used by each attribute route, such as `00049.png`, `00125.png`, `00057.png`, `00031.png`, `00088.png`, `00004.png`, `00012.png`, and `00017.png`.
5. If preparing new aligned face samples, route to `../data-preparation/`.

## Missing style-mix `src` or `dst` images

Symptoms:

- `style_mixing/stylemix.py` fails opening `src/<i>.png`, `src/<i>.jpg`, `dst/<i>.png`, or `dst/<i>.jpg`.
- The checker reports fewer than five source images or six destination images.

Fixes:

1. Inspect `DATASET.STYLE_MIX_PATH` in the selected config.
2. Provide `src/0` through `src/4` and `dst/0` through `dst/5` as `.png` or `.jpg` files.
3. For `bedroom`, this checkout's config points to `style_mixing/test_images/set_bedroom`, but the bundled sample set may be absent. Provide a custom set or use another config.
4. Confirm images are compatible with the config resolution; the script can downsample by an integer factor but will assert if the final size is wrong.

## GUI/display problems in `interactive_demo.py`

Symptoms:

- `bimpy` import or context initialization fails.
- No window appears, or the process exits on a headless machine.

Fixes:

1. Confirm `bimpy` is installed in the active environment.
2. Run on a machine/session with a display server, or use an approved virtual display setup.
3. Use noninteractive figure scripts instead when running in CI or a headless shell.
4. Remember that `interactive_demo.py` uses `dataset_samples/faces/realign1024x1024` and the default FFHQ directions regardless of some config sample fields.

## `PYTHONPATH` or import errors

Symptoms:

- `ModuleNotFoundError: No module named 'net'`, `model`, `launcher`, `checkpointer`, or `defaults`.
- A subdirectory script works from an IDE but fails from the shell.

Fix:

```bash
cd <ALAE-checkout>
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python style_mixing/stylemix.py -c ffhq
```

The repository is a script checkout, not an installed Python package. Run commands from the checkout root and keep the root on `PYTHONPATH` for subdirectory scripts.

## CUDA and PyTorch issues

Symptoms:

- `torch.cuda.is_available()` is false.
- `torch.cuda.set_device(0)` fails.
- Model weights load but CUDA kernel launch fails.

Fixes:

1. Use a CUDA-capable PyTorch build compatible with the host GPU. Modern A100-class machines need a CUDA 11-capable torch stack, not the README-era CUDA 10 assumptions.
2. Confirm the active environment can allocate a small CUDA tensor before launching ALAE scripts.
3. Actual generation scripts do not have a CPU fallback in this skill. If CUDA is unavailable, stop at asset validation or move to a compatible host.
4. Keep TensorFlow/dnnlib issues separate: they matter for metrics and principal-direction regeneration, not for ordinary PyTorch generation figures.

## Missing direction files

Symptoms:

- `interactive_demo.py` fails loading `principal_directions/direction_<idx>.npy`.
- `make_figures/make_traversarls.py` fails during an attribute route.
- The checker reports missing or wrong-shaped direction arrays.

Fixes:

1. Confirm the expected files exist: `direction_0.npy`, `direction_1.npy`, `direction_2.npy`, `direction_3.npy`, `direction_4.npy`, `direction_10.npy`, `direction_11.npy`, `direction_17.npy`, and `direction_19.npy`.
2. For FFHQ checkpoints, expect one-dimensional 512-element vectors.
3. For non-FFHQ or custom checkpoints, regenerate directions; do not trust the committed FFHQ vectors for semantic editing.
4. Use [latent editing](latent-editing.md) for the regeneration sequence and its heavy dependencies.

## Non-FFHQ direction caveat

A command such as `python interactive_demo.py -c celeba-hq256` can load if the checkpoint and sample paths are present, but the sliders still use the same `principal_directions/direction_*.npy` files. Unless those files were regenerated for the selected checkpoint, the sliders are only a mechanical vector perturbation, not a validated attribute editor.

## Output directory confusion

Generation scripts write outputs under their own workflow folders, not under `OUTPUT_DIR`:

- Checkpoints are read from `OUTPUT_DIR/last_checkpoint`.
- Style mixing writes to `style_mixing/output/<cfg.NAME>/`.
- Most figure scripts write to `make_figures/output/<cfg.NAME>/`.
- FFHQ real reconstructions write `make_figures/reconstructions_ffhq_real_1.png` and `_2.png`.

If a run completes but no files appear where expected, check the current working directory. Native scripts assume they are launched from the ALAE repository root.
