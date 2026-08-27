# CLI Workflows

## When to read this

Read this when you need a copyable command for a common stitching scenario.

## 1) Stitch a few explicit images

Use this when you already know the filenames:

```bash
stitch img1.jpg img2.jpg img3.jpg --output panorama.jpg
```

### Expect
- A single output panorama at the path given by `--output`.
- No verbose directory unless `--verbose` is set.

## 2) Stitch a glob

Use this when the images share a predictable filename pattern:

```bash
stitch input/IMG*.jpg --output panorama.jpg
```

### Expect
- The command resolves the glob before stitching.
- If the glob matches nothing, the stitch will fail early or produce a file
  list problem that should be fixed before retrying.

## 3) Build an affine panorama for scans or aligned documents

Affine mode is useful for document scans or specialized capture devices:

```bash
stitch scans/*.jpg --affine --detector sift --no-crop --output scan-panorama.jpg
```

### Why these flags matter
- `--affine` switches the estimator, matcher, adjuster, warper, wave correction,
  and compensator defaults to the affine bundle.
- `--detector sift` is often a stronger default than ORB for scan-like images.
- `--no-crop` avoids crop failures when the panorama border is irregular.

## 4) Capture verbose diagnostics

Use verbose mode when a stitch succeeds but the quality is suspicious, or when
it fails after matching:

```bash
stitch img*.jpg --verbose --verbose_dir stitch-debug
```

### Expect
A directory with stage-by-stage files, including:
- a text snapshot of the stitcher settings,
- feature visualizations,
- match visualizations,
- a matches graph,
- warped images,
- timelapse frames,
- crop and seam diagnostics,
- the final result.

## 5) Use feature masks

Use feature masks when you want the detector to ignore part of each image:

```bash
stitch barcode1.png barcode2.png --feature_masks mask1.png mask2.png --output masked.jpg
```

### Important
- Provide one mask per image.
- Each mask must match the corresponding image resolution.
- If masks are mismatched, use the diagnostics workflow before trying a larger
  panorama run.

## 6) Headless or Docker usage

In a server or container session, avoid GUI preview:

```bash
stitch img*.jpg --output panorama.jpg
```

Do not use `--preview` unless the environment has a working display server.
If GUI support is unavailable, install the headless package instead of the GUI
build.

## 7) Output parameter overrides

If you need a different output encoding, pass OpenCV `imwrite()` flags:

```bash
stitch img*.jpg --output panorama.png --output_params 16 1
```

Use this only when you know the expected OpenCV flag numbers.

## Suggested recovery order

1. Confirm the image list or glob expands to the files you expect.
2. If the stitch drops images, lower `--confidence_threshold` and inspect the
   matches graph.
3. If masks are involved, confirm the mask count and resolutions.
4. If crop fails, retry with `--no-crop`.
5. If preview fails, remove `--preview` or switch to the headless package.
