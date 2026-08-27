---
name: generation
description: "Use ALAE checkpoints for demo, image generation, reconstructions,
  style mixing, traversals, and principal-direction management."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# ALAE generation router

Use this sub-skill when the user wants to run ALAE or StyleALAE from an existing pretrained or trained checkpoint for:

- the `interactive_demo.py` GUI;
- random generation figures;
- reconstruction, multi-resolution reconstruction, interpolation, and FFHQ/CelebA-HQ specialty figures;
- style-mixing figures;
- latent attribute traversals; or
- principal-direction file checks and regeneration planning.

Do **not** use this sub-skill to train checkpoints, prepare raw datasets/TFRecords, or run quantitative metrics. Route those to `../training/`, `../data-preparation/`, and `../metrics/` respectively.

## Required read order

1. Read [generation workflows](references/generation-workflows.md) to choose the correct GUI or noninteractive figure script and to identify required assets.
2. Read [latent editing](references/latent-editing.md) for `direction_*.npy` labels, FFHQ-specific caveats, and the expensive regeneration sequence.
3. If anything is missing or a command fails before model launch, read [generation troubleshooting](references/troubleshooting.md).

## Safe preflight before GPU or GUI work

When running native ALAE subdirectory scripts from a checkout root, first set that checkout root on the import path:

```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)"
```

Before launching those native scripts, run the bundled checkers from this sub-skill directory (or replace `scripts/...` with the actual path to this generated skill) and point `--repo-root` at the ALAE checkout. They validate assets without loading models or touching CUDA:

```bash
python scripts/check_generation_assets.py \
  --repo-root <ALAE-checkout> \
  --config ffhq

python scripts/check_principal_directions.py \
  --repo-root <ALAE-checkout> \
  --inspect-shapes
```

The checkers only inspect files and config text. A failed preflight should be fixed before launching `interactive_demo.py`, `style_mixing/stylemix.py`, or `make_figures/*.py`.

## Routing hints

- GUI latent editing: use `interactive_demo.py`; it needs a display/GUI context, CUDA, a checkpoint, sample face images, and FFHQ-compatible direction files.
- Style mixing: use `style_mixing/stylemix.py`; validate `DATASET.STYLE_MIX_PATH/src` and `dst` image counts first.
- Random generation: use `make_figures/make_generation_figure.py`; it only needs the selected config and checkpoint.
- Reconstructions and interpolation: use the relevant `make_figures/make_recon_figure_*.py` script; validate `DATASET.SAMPLES_PATH` and any hard-coded sample filenames called out in the workflow reference.
- Attribute traversals: use `make_figures/make_traversarls.py` and verify direction files first.
- Model artifact downloads are setup work. When the root helper exists, prefer the generated dry-run/list helper at `../../scripts/download_alae_artifacts.py`; otherwise treat the repository download manifest as a network action requiring explicit approval.
