# Single-image workflows

These workflows adapt the repository's `stylize_image.sh` behavior without interactive prompts. The shell wrapper asks about dependencies and CUDA, then derives directories and basenames with `dirname`/`basename`. Use the bundled builder to do the same derivation non-interactively and to avoid shell quoting mistakes.

## 1. Print a safe command from content/style paths

From the repository checkout root:

```bash
python skills/disco/neural-style-tf/sub-skills/image-stylization/scripts/build_image_command.py \
  --script neural_style.py \
  --content ./image_input/lion.jpg \
  --style ./styles/kandinsky.jpg \
  --output-dir ./image_output \
  --img-name lion_kandinsky \
  --device /cpu:0 \
  --max-size 256 \
  --max-iterations 50 \
  --optimizer adam \
  --print-only
```

The builder validates that the script, content image, and style image exist. It prints a command shaped like:

```bash
python neural_style.py \
  --content_img lion.jpg \
  --content_img_dir image_input \
  --style_imgs kandinsky.jpg \
  --style_imgs_dir styles \
  --img_output_dir image_output \
  --img_name lion_kandinsky \
  --device /cpu:0 \
  --max_size 256 \
  --max_iterations 50 \
  --optimizer adam
```

Keep `--print-only` while checking paths. Add `--run` only when the TensorFlow 1.x runtime and VGG weights are ready.

## 2. Execute a bounded CPU smoke render

Use a small image size and Adam when the host is CPU-only or memory-constrained:

```bash
python skills/disco/neural-style-tf/sub-skills/image-stylization/scripts/build_image_command.py \
  --script neural_style.py \
  --content ./image_input/golden_gate.jpg \
  --style ./styles/starry-night.jpg \
  --model-weights ./imagenet-vgg-verydeep-19.mat \
  --output-dir ./image_output \
  --img-name smoke_golden_gate_starry \
  --device /cpu:0 \
  --optimizer adam \
  --max-size 128 \
  --max-iterations 5 \
  --run
```

This is for plumbing validation, not visual quality. Increase `--max-size` and `--max-iterations` only after the render path works.

## 3. Higher-quality single-image run

The repository default optimizer is L-BFGS and the README recommends GPU when available. A larger run looks like:

```bash
python neural_style.py \
  --content_img tubingen.jpg \
  --content_img_dir ./image_input \
  --style_imgs the_scream.jpg \
  --style_imgs_dir ./styles \
  --model_weights ./imagenet-vgg-verydeep-19.mat \
  --img_output_dir ./image_output \
  --img_name tubingen_scream_lbfgs \
  --device /gpu:0 \
  --optimizer lbfgs \
  --max_size 512 \
  --max_iterations 1000 \
  --verbose
```

If GPU placement fails, switch to `--device /cpu:0`. If memory fails, reduce `--max_size`, reduce `--max_iterations`, or switch to `--optimizer adam`.

## 4. Content/style outside the default directories

`neural_style.py` wants a directory flag plus a filename flag. For arbitrary paths, either derive them manually:

```bash
python neural_style.py \
  --content_img portrait.jpg \
  --content_img_dir ../inputs/photos \
  --style_imgs wave.jpg \
  --style_imgs_dir ../inputs/styles \
  --model_weights ./imagenet-vgg-verydeep-19.mat \
  --img_output_dir ./image_output \
  --img_name portrait_wave \
  --device /cpu:0
```

or let the builder derive the directory and basename:

```bash
python skills/disco/neural-style-tf/sub-skills/image-stylization/scripts/build_image_command.py \
  --content ../inputs/photos/portrait.jpg \
  --style ../inputs/styles/wave.jpg \
  --model-weights ./imagenet-vgg-verydeep-19.mat \
  --img-name portrait_wave \
  --device /cpu:0 \
  --print-only
```

Avoid quoted `~` paths in direct `neural_style.py` commands. The builder expands `~` before printing, but the original script does not.

## 5. Initialization and reproducibility controls

Single-image initialization is selected with `--init_img_type`:

- `content` is the parser default and starts from the content image.
- `style` starts from the first style image.
- `random` starts from noise; combine it with `--seed` for reproducible random initialization.

Example:

```bash
python neural_style.py \
  --content_img lion.jpg \
  --content_img_dir ./image_input \
  --style_imgs kandinsky.jpg \
  --style_imgs_dir ./styles \
  --model_weights ./imagenet-vgg-verydeep-19.mat \
  --img_output_dir ./image_output \
  --img_name lion_kandinsky_seed7 \
  --device /cpu:0 \
  --optimizer adam \
  --max_size 256 \
  --max_iterations 100 \
  --init_img_type random \
  --seed 7
```

The builder exposes these as `--init-img-type` and `--seed`.

## Output layout

For a single-image run, `write_image_output` creates a nested result directory:

```text
<img_output_dir>/<img_name>/
  <img_name>.png       # stylized output
  content.png          # preprocessed/resized content image written back out
  init.png             # initialization image
  style_0.png          # first style image resized to content dimensions
  style_1.png          # additional style images, if used
  meta_data.txt        # selected configuration values
```

`meta_data.txt` records the image name, content filename, style filenames and weights, initialization type, content/style/TV weights, content/style layers, optimizer, max iterations, and max image size. The metadata records filenames as passed to `neural_style.py`; keep command logs if you need the full original source paths.

## Boundaries and cross-links

- Multiple style weighting/interpolation is outside this sub-skill; see [advanced-controls](../../advanced-controls/SKILL.md).
- Masks, original color preservation, and layer weighting are outside this sub-skill; see [advanced-controls](../../advanced-controls/SKILL.md).
- Video frames and optical flow are outside this sub-skill; see [video-stylization](../../video-stylization/SKILL.md).
- Runtime setup and VGG acquisition belong to the root [runtime notes](../../../references/runtime-and-installation.md) and [root troubleshooting](../../../references/troubleshooting.md).
