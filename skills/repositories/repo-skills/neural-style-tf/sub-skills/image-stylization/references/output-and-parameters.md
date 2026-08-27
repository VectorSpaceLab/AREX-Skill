# Output and important single-image parameters

The repository is a legacy script-style TensorFlow 1.x program. The argument names below are the `neural_style.py` parser names. The builder in `../scripts/build_image_command.py` uses hyphenated names for its own options and prints the matching underscore-form `neural_style.py` flags.

## Required path model

`neural_style.py` separates each image into directory and filename:

| Purpose | `neural_style.py` flags | Parser default | Notes |
| --- | --- | --- | --- |
| Content image | `--content_img`, `--content_img_dir` | `--content_img` has no default; `--content_img_dir ./image_input` | Single-image runs need a readable content image. The script joins the directory and filename with `os.path.join`. |
| Style image(s) | `--style_imgs`, `--style_imgs_dir` | `--style_imgs` is required; `--style_imgs_dir ./styles` | This sub-skill covers the normal one-style case. Multiple style weighting/interpolation belongs to [advanced-controls](../../advanced-controls/SKILL.md). |
| VGG weights | `--model_weights` | `imagenet-vgg-verydeep-19.mat` | The `.mat` file is loaded by `scipy.io.loadmat` when the model is built. Put it in the working directory or pass an explicit path. |
| Output root/name | `--img_output_dir`, `--img_name` | `./image_output`, `result` | Output is nested under `<img_output_dir>/<img_name>/`, not written directly into `<img_output_dir>`. |

## Core single-image flags

| Flag | Parser default | Choices / type | Operational note |
| --- | --- | --- | --- |
| `--init_img_type` | `content` | `content`, `random`, `style` | Controls `get_init_image`. Use `random` with `--seed` for reproducible noise starts. |
| `--seed` | `0` | integer | Used by `get_noise_image` only when random initialization is selected. |
| `--max_size` | `512` | integer | `get_content_image` resizes the content image so the largest dimension is no more than this value; style images are resized to the resulting content dimensions. |
| `--device` | `/gpu:0` | `/gpu:0`, `/cpu:0` | The parser default assumes a CUDA-capable GPU. Use `/cpu:0` on CPU-only hosts. The command builder defaults to `/cpu:0` for safer non-interactive use. |
| `--optimizer` | `lbfgs` | `lbfgs`, `adam` | L-BFGS uses `tf.contrib.opt.ScipyOptimizerInterface` and usually uses more memory. Adam uses less memory but may need tuning. |
| `--max_iterations` | `1000` | integer | Passed to L-BFGS as `maxiter`; controls the Adam loop length. Reduce for smoke tests. |
| `--print_iterations` | `50` | integer | Only affects optimizer progress printing when `--verbose` is set. |
| `--verbose` | off | flag | Prints setup/progress messages and makes L-BFGS display progress. |

## Output bundle contents

`write_image_output` creates:

```text
<img_output_dir>/<img_name>/
  <img_name>.png
  content.png
  init.png
  style_0.png
  style_1.png
  ...
  meta_data.txt
```

The image files are written with OpenCV after postprocessing. `style_N.png` files are the style inputs resized to the processed content image dimensions, not byte-for-byte copies of the source style files.

`meta_data.txt` records:

- `image_name`
- content filename
- each style filename and its normalized weight
- style mask filenames when masks are used (masks are outside this sub-skill)
- initialization type
- content/style/TV weights
- content/style layer lists
- optimizer type
- max iterations
- max image size

If the output directory is empty, confirm that the process reached `write_image_output`; failures before that point include image path errors, missing VGG weights, TensorFlow runtime incompatibility, device placement failure, and memory exhaustion.

## Builder behavior

`../scripts/build_image_command.py` intentionally differs from `stylize_image.sh` in these ways:

- It is non-interactive and never prompts about dependencies or CUDA.
- It validates the script, content image, style image(s), and any explicit `--model-weights` path before printing a command.
- It expands `~` in input paths before deriving directories and basenames.
- It prints only by default; it runs only with `--run`.
- It uses `subprocess` without a shell when `--run` is supplied.
- It accepts repeatable `--style` values only when they can be represented by one `--style_imgs_dir`; if multiple styles are supplied, it emits equal raw `--style_imgs_weights` so every style participates. Custom style weighting/interpolation still belongs to [advanced-controls](../../advanced-controls/SKILL.md). If style images live in different directories, stage them into one directory or use a more advanced workflow.

## Evidence-backed limits

The generated skill evidence covers the README setup/usage/arguments/memory notes, the parser and single-image helper functions in `neural_style.py`, and the interactive `stylize_image.sh` wrapper. CLI help was verified in a TensorFlow 1.15 CPU-compatible inspection runtime. Full image rendering requires the external VGG-19 `.mat` file and is optional/not verified here.
