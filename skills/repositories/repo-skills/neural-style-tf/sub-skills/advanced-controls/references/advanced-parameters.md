# Advanced Parameters

## When to read

Read this when a single-image `neural_style.py` command needs multiple styles, masks, color preservation, layer/loss tuning, initialization control, or optimizer changes. Build the base content/style/VGG/output command first, then add the flags here.

## Multiple style images and weights

`neural_style.py` accepts a space-separated style list and a matching weight list:

```bash
python neural_style.py \
  --content_img lion.jpg --content_img_dir ./image_input \
  --style_imgs starry-night.jpg the_scream.jpg \
  --style_imgs_dir ./styles \
  --style_imgs_weights 0.7 0.3 \
  --device /cpu:0
```

Source facts:

- `--style_imgs` is required and uses `nargs='+'`.
- `--style_imgs_weights` defaults to `[1.0]` and is normalized after parsing.
- `sum_style_losses(...)` zips style images and weights. If the lists differ in length, extra values can be ignored instead of producing a clear validation error.

Use `scripts/plan_advanced_args.py` to validate counts and see normalized weights before running:

```bash
python sub-skills/advanced-controls/scripts/plan_advanced_args.py \
  --style starry-night.jpg --style the_scream.jpg \
  --style-weight 7 --style-weight 3
```

## Style masks and segmentation

Masking is enabled with `--style_mask` and one or more `--style_mask_imgs` values:

```bash
python neural_style.py \
  --content_img face.jpg --content_img_dir ./image_input \
  --style_imgs starry-night.jpg kandinsky.jpg --style_imgs_dir ./styles \
  --style_mask --style_mask_imgs face_mask.png face_mask_inv.png
```

Important source behavior:

- `get_mask_image(...)` reads mask filenames from `--content_img_dir`, not from `--style_imgs_dir`.
- Masks are loaded as grayscale, resized to the style/content tensor width and height, normalized by the mask maximum, and broadcast across channels.
- `sum_masked_style_losses(...)` zips style images, weights, and masks. Keep the style count, weight count, and mask count aligned.
- A mask with all zero pixels can divide by zero during normalization. Check mask pixel values before a long run.

## Original-color transfer

Use this when the user wants style texture but content-image colors:

```bash
python neural_style.py \
  --content_img golden_gate.jpg --style_imgs starry-night.jpg \
  --original_colors --color_convert_type yuv
```

`--color_convert_type` choices are `yuv`, `ycrcb`, `luv`, and `lab`. The source converts the generated stylized image and original content image to the selected color space, keeps luminance from the stylized output, keeps chroma channels from the content image, converts back to BGR, and preprocesses again before writing.

Caveat: `--color_convert_time` is parsed with choices `after` and `before`, but the implementation always calls `convert_to_original_colors(...)` after optimization. Do not promise a pre-optimization color transfer mode unless a refreshed checkout implements it.

## Layer and loss controls

Default source values:

| Flag | Source default | Notes |
| --- | --- | --- |
| `--content_layers` | `conv4_2` | Content reconstruction layer list. |
| `--style_layers` | `relu1_1 relu2_1 relu3_1 relu4_1 relu5_1` | Style Gram-matrix layers. |
| `--content_layer_weights` | `1.0` | Normalized after parsing. Count should match content layers. |
| `--style_layer_weights` | `0.2 0.2 0.2 0.2 0.2` | Normalized after parsing. Count should match style layers. |
| `--content_loss_function` | `1` | Selects one of three constants in `content_layer_loss`. |
| `--pooling_type` | `avg` | Choices: `avg`, `max`. |
| `--content_weight` | `5.0` | Multiplies content loss. |
| `--style_weight` | `10000.0` | Multiplies style loss. |
| `--tv_weight` | `0.001` | Total variation/denoising weight. |

Practical guidance:

- Change one group at a time and keep the original command in metadata notes.
- Higher `--style_weight` or lower `--content_weight` generally pushes stronger stylization and weaker content preservation.
- Shallow style layers capture textures; deeper style layers capture larger motifs. Avoid deleting all shallow layers unless the user explicitly wants large-scale structure over texture.
- Keep weight-list lengths equal to their layer-list lengths. Use the planner script to catch mismatches.

## Initialization and stochasticity

| Flag | Source default | Notes |
| --- | --- | --- |
| `--init_img_type` | `content` | Choices: `content`, `random`, `style`. |
| `--noise_ratio` | `1.0` | Blend between random noise and content when `--init_img_type random`. |
| `--seed` | `0` | NumPy random seed for noise initialization. |

Use `random` plus an explicit seed when the user asks for multiple variations from the same content/style pair. Use `content` when reproducibility and content structure matter more than output diversity.

## Optimizer and memory controls

| Flag | Source default | Notes |
| --- | --- | --- |
| `--optimizer` | `lbfgs` | Better quality in repo docs, but memory-heavy and requires `tf.contrib.opt.ScipyOptimizerInterface`. |
| `--learning_rate` | `1.0` | Used only by Adam. |
| `--max_iterations` | `1000` | Long runs can be slow, especially on CPU. |
| `--print_iterations` | `50` | Only visible when `--verbose` is set. |
| `--max_size` | `512` | Resize cap for longest image side. Lower this first for memory failures. |

For a quick CPU sanity run when VGG weights are already available, prefer `--optimizer adam --max_iterations 1 --max_size 64 --device /cpu:0` and a disposable output directory. This verifies the command path without implying final artistic quality.
