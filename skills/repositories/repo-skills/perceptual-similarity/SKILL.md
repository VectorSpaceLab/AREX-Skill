---
name: perceptual-similarity
description: "Routes LPIPS image-similarity, BAPPS evaluation, and BAPPS
  training workflows for the PerceptualSimilarity package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Perceptual Similarity

Use this skill for the `lpips` package when the task is about perceptual image similarity, BAPPS scoring, or training the learned metric.

## When to use this skill

Choose this skill when the request mentions any of the following:

- LPIPS distances between two images or two folders of images.
- Perceptual loss, optimization with LPIPS, or spatial LPIPS maps.
- BAPPS 2AFC or JND evaluation.
- Training, fine-tuning, or smoke-testing the LPIPS/BAPPS training path.

If the task is about generic classification, detection, or segmentation rather than perceptual similarity, route elsewhere.

## Install

Install the public package dependencies first:

```bash
python -m pip install lpips torch torchvision numpy scipy scikit-image opencv-python matplotlib tqdm
```

Optional add-ons:

- `dominate` is only needed for the stock repo `train.py` HTML visualizer path.
- `ipython` is only useful for interactive debugging.
- A CUDA-capable Torch/torchvision build is needed only if you want GPU execution.

## Minimal import check

Run the bundled environment check after installation:

```bash
python skills/disco/perceptual-similarity/scripts/check_lpips_env.py
```

Or do the smallest direct import check:

```bash
python -I -c "import lpips; from lpips.lpips import LPIPS; print('lpips ok')"
```

## Route map

- `sub-skills/metric-usage/` — compare image pairs, compare directories, inspect LPIPS maps, and use LPIPS as a loss.
- `sub-skills/bapps-evaluation/` — score 2AFC and JND BAPPS splits with LPIPS, baseline, L2, or SSIM-style metrics.
- `sub-skills/bapps-training/` — train or fine-tune LPIPS on BAPPS-style 2AFC data.

## Bundled assets and helpers

- `assets/examples/` contains copied sample images and tiny directory examples for smoke tests.
- `scripts/make_tiny_bapps_fixture.py` creates a tiny BAPPS-style fixture from the bundled examples.
- `scripts/check_lpips_env.py` verifies the install, package metadata, and optional backend state.

## Cross-cutting notes

- Read `references/repo-provenance.md` before deciding whether this skill matches the current checkout.
- Read `references/troubleshooting.md` for install/import, optional dependency, backend, and legacy SSIM issues.
- The bundled evaluation helpers use a modern SSIM fallback; the stock `lpips.dssim` path is broken on current `scikit-image` releases.
- The bundled training helper avoids the old HTML/visdom stack used by `train.py`.

## Typical entry points

- `python skills/disco/perceptual-similarity/sub-skills/metric-usage/scripts/compare_images.py --help`
- `python skills/disco/perceptual-similarity/sub-skills/metric-usage/scripts/optimize_lpips.py --help`
- `python skills/disco/perceptual-similarity/sub-skills/bapps-evaluation/scripts/score_bapps.py --help`
- `python skills/disco/perceptual-similarity/sub-skills/bapps-training/scripts/train_bapps.py --help`

## Refresh baseline

If the repository commit, working tree state, or package version no longer match `references/repo-provenance.md`, refresh the skill before relying on it.
