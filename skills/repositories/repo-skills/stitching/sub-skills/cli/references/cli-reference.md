# CLI Reference

## When to read this

Read this when you need the exact `stitch` flags, accepted values, or the
command-line shape for panorama stitching.

## Public entry point

The installed console script is `stitch`.

```bash
stitch --help
stitch --version
```

The public parser lives in `stitching.cli.stitch.create_parser()`, but future
agents should use the installed `stitch` command unless they are writing
Python-side validation.

## Verified command shape

```text
stitch [options] images [images ...]
```

The command accepts one or more image paths or glob patterns. When a single
pattern is supplied, the package resolves wildcards before stitching.

## Important flags

| Flag | Purpose | Verified values / notes |
| --- | --- | --- |
| `--verbose` | Write step-by-step diagnostic images and text files | Creates a directory named by `--verbose_dir` |
| `--verbose_dir` | Directory for verbose outputs | Default is a timestamped `*_verbose_results` folder |
| `--affine` | Switch to affine defaults for scan-like images | Equivalent to `AffineStitcher.AFFINE_DEFAULTS` |
| `--medium_megapix` | Registration resolution | Default `0.6` MP |
| `--low_megapix` | Seam/exposure resolution | Default `0.1` MP |
| `--final_megapix` | Final composition resolution | Default `-1` (original resolution) |
| `--detector` | Feature detector | Choices: `orb`, `sift`, `brisk`, `akaze` |
| `--nfeatures` | Feature count for `orb` and `sift` | Default `500` |
| `--feature_masks` | Per-image feature masks | Count and shape must match the image list |
| `--matcher_type` | Pairwise matcher family | Choices: `homography`, `affine` |
| `--range_width` | Limit matching neighborhood | Default `-1` |
| `--try_use_gpu` | Try a CUDA path in OpenCV | Optional only; not a required backend |
| `--match_conf` | Feature-match confidence | Default depends on detector |
| `--confidence_threshold` | Keep only the biggest connected panorama component | Default `1` |
| `--matches_graph_dot_file` | Write a DOT matches graph | Useful when images are dropped |
| `--estimator` | Camera estimator | Choices: `homography`, `affine` |
| `--adjuster` | Bundle adjuster | Choices: `ray`, `reproj`, `affine`, `no` |
| `--refinement_mask` | Bundle-adjustment refinement mask | Five-character string like `xxxxx` |
| `--wave_correct_kind` | Wave correction mode | Choices: `horiz`, `vert`, `auto`, `no` |
| `--warper_type` | Warp surface | Many OpenCV choices, default `spherical` |
| `--crop` / `--no-crop` | Enable or disable largest-interior-rectangle cropping | `--crop` is the default |
| `--compensator` | Exposure compensation | Choices: `gain_blocks`, `gain`, `channel`, `channel_blocks`, `no` |
| `--nr_feeds` | Compensation feed count | Integer |
| `--block_size` | Compensation block size | Integer |
| `--finder` | Seam finder | Choices include `dp_color`, `dp_colorgrad`, `gc_color`, `gc_colorgrad`, `voronoi`, `no` |
| `--blender_type` | Blend mode | Choices: `multiband`, `feather`, `no` |
| `--blend_strength` | Blend strength | Integer percentage-like value |
| `--timelapse` | Save timelapse frames instead of a final panorama | Choices: `no`, `as_is`, `crop` |
| `--preview` | Open a GUI preview window | Avoid in headless sessions |
| `--output` | Output panorama path | Default `result.jpg` |
| `--output_params` | OpenCV `imwrite()` flags | Pass integer pairs |

## Common command patterns

### Basic stitch

```bash
stitch img1.jpg img2.jpg img3.jpg --output panorama.jpg
```

### Glob-based stitch

```bash
stitch images/IMG*.jpg --output panorama.jpg
```

### Verbose diagnostics

```bash
stitch img*.jpg --verbose --verbose_dir stitch-debug
```

### Affine mode for scan-like images

```bash
stitch scans/*.jpg --affine --detector sift --no-crop --output scan-panorama.jpg
```

### Feature masks

```bash
stitch barcode1.png barcode2.png --feature_masks mask1.png mask2.png --output masked.jpg
```

### Headless run

```bash
stitch img*.jpg --output panorama.jpg
```

Avoid `--preview` in headless sessions.

## CLI validation helper

Use the bundled helper to check image and mask arguments before a full stitch:

```bash
python scripts/validate_cli_args.py -- stitch img*.jpg --feature_masks mask1.png mask2.png
```

The helper does not run the panorama stitch. It only checks parser-known flags,
resolved image counts, and feature-mask alignment.
