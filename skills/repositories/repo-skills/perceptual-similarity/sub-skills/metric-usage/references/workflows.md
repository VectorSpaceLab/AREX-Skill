# Metric Usage Workflows

## Purpose

Read this when you need the exact command shape for pairwise LPIPS comparison, directory comparison, spatial maps, or LPIPS-loss optimization.

## Pairwise comparison

Compare two images with the bundled defaults:

```bash
python skills/disco/perceptual-similarity/sub-skills/metric-usage/scripts/compare_images.py --mode pair
```

Compare your own files:

```bash
python skills/disco/perceptual-similarity/sub-skills/metric-usage/scripts/compare_images.py \
  --mode pair \
  --path0 /path/to/a.png \
  --path1 /path/to/b.png
```

Useful options:

- `--metric lpips|baseline|l2|ssim`
- `--net squeeze|alex|vgg`
- `--version 0.1|0.0`
- `--use_gpu`
- `--spatial`
- `--spatial_map_out path.png`

The spatial-map mode is best when you want localization instead of a single scalar.

## Directory-pair comparison

Compare matching filenames in two directories:

```bash
python skills/disco/perceptual-similarity/sub-skills/metric-usage/scripts/compare_images.py \
  --mode dir-pair \
  --dir0 /path/to/dir0 \
  --dir1 /path/to/dir1 \
  --out /tmp/dir_scores.txt
```

The helper compares only filenames that exist in both directories.

## All-pairs comparison

Compare adjacent files in a folder:

```bash
python skills/disco/perceptual-similarity/sub-skills/metric-usage/scripts/compare_images.py \
  --mode all-pairs \
  --dir /path/to/images \
  --out /tmp/all_pairs.txt
```

Add `--all-pairs` to compare every unique pair instead of only consecutive pairs.

## LPIPS optimization demo

Run the bounded perceptual-loss demo:

```bash
python skills/disco/perceptual-similarity/sub-skills/metric-usage/scripts/optimize_lpips.py
```

Common options:

- `--ref_path` and `--pred_path` to supply your own images.
- `--steps` to bound runtime.
- `--out_dir` to control where the saved frames and final image are written.
- `--net vgg` if you want the closer-to-traditional perceptual-loss variant used in the paper's demo.

## Bundled smoke assets

The default inputs live under `../../assets/examples/` relative to this sub-skill:

- `ex_ref.png`
- `ex_p0.png`
- `ex_p1.png`
- `ex_dir0/`
- `ex_dir1/`
- `ex_dir_pair/`

These defaults let the helpers run even after the source repository checkout is gone.

## Read next if something fails

- `references/troubleshooting.md` for normalization, backbone download, and headless rendering issues.
- `../../references/api-reference.md` for the verified LPIPS API and model flags.
