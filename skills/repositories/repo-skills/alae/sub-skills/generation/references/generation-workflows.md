# ALAE generation workflows

This reference covers checkpoint-backed inference and visualization routes in an ALAE checkout. It separates the interactive GUI from noninteractive figure scripts and gives safe preflight patterns before any GPU script is launched.

## Common prerequisites

Run native ALAE commands from the ALAE repository root. For command-line launches, add the checkout root to `PYTHONPATH` because several subdirectory scripts import root modules such as `model`, `net`, `launcher`, and `checkpointer`.

```bash
cd <ALAE-checkout>
export PYTHONPATH="$PYTHONPATH:$(pwd)"
```

Most generation scripts accept `-c <config>` through the shared launcher. The primary README-supported generation configs are:

- `ffhq` -> `configs/ffhq.yaml`, `NAME: ffhq`, output checkpoint directory `training_artifacts/ffhq`, samples `dataset_samples/faces/realign1024x1024`, style-mix set `style_mixing/test_images/set_ffhq`.
- `celeba` -> `configs/celeba.yaml`, `NAME: celeba`, output checkpoint directory `training_artifacts/celeba`, samples `dataset_samples/faces/realign128x128`, style-mix set `style_mixing/test_images/set_celeba`.
- `celeba-hq256` -> `configs/celeba-hq256.yaml`, `NAME: celeba-hq256`, output checkpoint directory `training_artifacts/celeba-hq256`, samples `dataset_samples/faces/realign1024x1024`, style-mix set `style_mixing/test_images/set_ffhq`.
- `bedroom` -> `configs/bedroom.yaml`, `NAME: bedroom`, output checkpoint directory `training_artifacts/bedroom`, samples `dataset_samples/bedroom256x256`. The README advertises style mixing for `bedroom`, but this checkout does not include `style_mixing/test_images/set_bedroom`; provide a custom set or skip style mixing for that config.

The `mnist` and `mnist_fc` configs are training-oriented and are not primary routes for these qualitative figure scripts.

## Checkpoint and artifact setup

Every model-loading generation script uses `OUTPUT_DIR/last_checkpoint` from the selected config. That text file points to the actual `.pth` model file. The target can be produced by training or downloaded as a pretrained artifact.

The repository includes a networked manifest at `training_artifacts/download_all.py`. In this generated skill tree, prefer the root setup helper when it exists: [`../../../scripts/download_alae_artifacts.py`](../../../scripts/download_alae_artifacts.py). It is intended to expose a list/dry-run mode before any download. If that helper has not been generated yet, do not assume it exists; treat direct use of the repository manifest as explicit network setup work.

Safe asset preflight:

```bash
python scripts/check_generation_assets.py \
  --repo-root <ALAE-checkout> \
  --config ffhq
```

Use skip flags when checking a workflow that does not need every asset category, for example random generation without sample/style images:

```bash
python scripts/check_generation_assets.py \
  --repo-root <ALAE-checkout> \
  --config ffhq \
  --skip-samples \
  --skip-style-mix \
  --skip-directions
```

## Interactive demo: GUI latent attribute editing

Command patterns:

```bash
python interactive_demo.py
python interactive_demo.py -c ffhq
python interactive_demo.py -c celeba-hq256
```

Inputs:

- CUDA-capable PyTorch environment.
- A GUI/display context for `bimpy`.
- `OUTPUT_DIR/last_checkpoint` and the referenced `.pth` file for the selected config.
- Face samples under the path hard-coded in `interactive_demo.py`: `dataset_samples/faces/realign1024x1024`.
- Principal direction files `principal_directions/direction_0.npy`, `direction_1.npy`, `direction_2.npy`, `direction_3.npy`, `direction_4.npy`, `direction_10.npy`, `direction_11.npy`, `direction_17.npy`, and `direction_19.npy`.

Outputs:

- A live GUI window titled `Styles` with sliders for the committed directions.
- No stable image-output artifact by default.

Important distinctions:

- The default config is FFHQ.
- The committed direction files are documented as FFHQ-model directions. For non-FFHQ checkpoints, regenerate directions before trusting sliders.
- The demo can load an image from the hard-coded sample folder or generate a random latent inside the GUI; it is not a noninteractive batch renderer.

## Style mixing

Command pattern:

```bash
python style_mixing/stylemix.py -c <config>
```

Use one of `ffhq`, `celeba`, `celeba-hq256`, or a custom config whose `DATASET.STYLE_MIX_PATH` contains the required layout.

Inputs:

- Checkpoint through `OUTPUT_DIR/last_checkpoint`.
- `DATASET.STYLE_MIX_PATH/src/{0..4}.png` or `.jpg` for five source images.
- `DATASET.STYLE_MIX_PATH/dst/{0..5}.png` or `.jpg` for six destination images.
- Image sizes should be compatible with the config's generated resolution; the script downsamples by an integer factor when needed.

Outputs:

- `style_mixing/output/<cfg.NAME>/stylemix.png`.
- Per-image support files such as `source_<i>.png`, `dst_coarse_<i>.png`, and `rec_coarse_<row>_<col>.png` in the same output directory.

Preflight:

```bash
python scripts/check_generation_assets.py \
  --repo-root <ALAE-checkout> \
  --config ffhq \
  --skip-samples \
  --skip-directions
```

## Random generation figure

Command pattern:

```bash
python make_figures/make_generation_figure.py -c <config>
```

Inputs:

- Checkpoint through `OUTPUT_DIR/last_checkpoint`.
- CUDA-capable PyTorch environment.

Outputs:

- `make_figures/output/<cfg.NAME>/generations.jpg`.

Notes:

- The script uses a fixed random seed inside the source code.
- It does not require sample or style-mix image folders.

## Reconstruction pages

Command pattern:

```bash
python make_figures/make_recon_figure_paged.py -c <config>
```

Inputs:

- Checkpoint through `OUTPUT_DIR/last_checkpoint`.
- Image files under `DATASET.SAMPLES_PATH`.
- CUDA-capable PyTorch environment.

Outputs:

- `make_figures/output/<cfg.NAME>/reconstructions_<page>.png`.

The script sorts and shuffles sample files, then writes pages of source/reconstruction pairs. Validate `DATASET.SAMPLES_PATH` before launching.

## Multi-resolution reconstruction figure

Command pattern:

```bash
python make_figures/make_recon_figure_multires.py -c <config>
```

Inputs:

- Checkpoint through `OUTPUT_DIR/last_checkpoint`.
- Image files under `DATASET.SAMPLES_PATH`.
- `scikit-image` for `skimage.transform.resize`.
- CUDA-capable PyTorch environment.

Outputs:

- `make_figures/output/<cfg.NAME>/reconstructions_multiresolution.png`.

This route overlaps with reconstruction pages but renders a multi-scale paper-style layout.

## Interpolation figure

Command pattern:

```bash
python make_figures/make_recon_figure_interpolation.py -c <config>
```

Inputs:

- Checkpoint through `OUTPUT_DIR/last_checkpoint`.
- `DATASET.SAMPLES_PATH` containing the filenames hard-coded by the script: `00001.png`, `00022.png`, `00077.png`, and `00016.png`.
- CUDA-capable PyTorch environment.

Outputs:

- `make_figures/output/<cfg.NAME>/interpolations.png`.
- `make_figures/output/<cfg.NAME>/interpolations.jpg`.

Use this only when the selected sample set contains the expected files or after adapting the source script in the checkout.

## FFHQ real reconstruction figure

Command pattern:

```bash
python make_figures/make_recon_figure_ffhq_real.py
```

Inputs:

- FFHQ checkpoint through `configs/ffhq.yaml` and `training_artifacts/ffhq/last_checkpoint`.
- Test TFRecords configured by `DATASET.PATH_TEST` and `DATASET.PART_COUNT_TEST`.
- CUDA-capable PyTorch environment and DareBlopy data loading.

Outputs:

- `make_figures/reconstructions_ffhq_real_1.png`.
- `make_figures/reconstructions_ffhq_real_2.png`.

This is dataset-heavy compared with sample-folder reconstruction. If TFRecords are missing, route to `../data-preparation/` instead of trying to fabricate inputs here.

## CelebA-HQ pioneer reconstruction figure

Command pattern:

```bash
python make_figures/make_recon_figure_celeba_pioneer.py
```

Inputs:

- CelebA-HQ 256 checkpoint through the script's default `configs/celeba-hq256.yaml`.
- Samples under the hard-coded path `dataset_samples/faces/pioneer256x256`.
- CUDA-capable PyTorch environment.

Outputs:

- `make_figures/output/pioneer/<input-stem>_alae.png`.

This is a specialized paper-figure route, not the general reconstruction entry point.

## Attribute traversals

Command pattern:

```bash
python make_figures/make_traversarls.py -c <config>
```

Inputs:

- Checkpoint through `OUTPUT_DIR/last_checkpoint`.
- `DATASET.SAMPLES_PATH` containing the filenames hard-coded by the script for each traversal.
- Principal direction files for the selected attributes.
- CUDA-capable PyTorch environment.

Outputs:

- `make_figures/output/<cfg.NAME>/traversal_gender.jpg`.
- `make_figures/output/<cfg.NAME>/traversal_smile.jpg`.
- `make_figures/output/<cfg.NAME>/traversal_wavy-hair.jpg`.
- `make_figures/output/<cfg.NAME>/traversal_young.jpg`.
- `make_figures/output/<cfg.NAME>/traversal_big_lips.jpg`.
- `make_figures/output/<cfg.NAME>/traversal_big_nose.jpg`.
- `make_figures/output/<cfg.NAME>/traversal_chubby.jpg`.
- `make_figures/output/<cfg.NAME>/traversal_glasses.jpg`.

The filename `make_traversarls.py` is misspelled in the repository and should be typed exactly as above.

## Legacy routes to avoid as primary workflows

`make_figures/old/*` contains legacy reconstruction variants referenced by the README. Keep them as historical evidence only. Prefer the current scripts listed above unless the user specifically asks to reproduce an old paper layout and accepts source adaptation work.
