# Single-image troubleshooting

Use this page after runtime setup has been handled by the root [runtime notes](../../../references/runtime-and-installation.md) and [root troubleshooting](../../../references/troubleshooting.md). This sub-skill focuses on failures that appear while constructing or running a single-image `neural_style.py` command.

## Shell wrapper prompts or hangs

Symptom: `bash stylize_image.sh ...` asks whether dependencies are installed and whether CUDA is available.

Cause: `stylize_image.sh` is an interactive helper. It only derives `content_img_dir`, `content_img`, `style_imgs_dir`, `style_imgs`, and `--device`, then calls `python neural_style.py`.

Fix: use `../scripts/build_image_command.py` to build the same kind of command non-interactively, then add `--run` only after inspecting the printed command.

## Missing content/style image

Symptom examples:

- Builder exits before printing a command and reports a missing `--content` or `--style` path.
- Direct `neural_style.py` run raises an `OSError`/`ENOENT` from `check_image`.

Cause: `get_content_image` and `get_style_images` use `cv2.imread`. When OpenCV cannot read the path, it returns `None`, and `check_image` raises a missing-file error for the joined path.

Fix:

1. Confirm the effective pair of flags, not just the original path:
   - `--content_img_dir` + `--content_img`
   - `--style_imgs_dir` + each value in `--style_imgs`
2. Prefer the builder for arbitrary paths; it derives the directory and basename like `stylize_image.sh`.
3. If the image file exists but still fails, check the extension and OpenCV readability. The README lists `.png`, `.jpg`, `.ppm`, and `.pgm` as supported image formats.

## Missing VGG `.mat` weights

Symptom: image paths validate, then the run fails while loading `imagenet-vgg-verydeep-19.mat` or another `.mat` path.

Cause: `build_model` calls `scipy.io.loadmat(args.model_weights)`. The parser default is `imagenet-vgg-verydeep-19.mat`, interpreted relative to the process working directory.

Fix:

- Put `imagenet-vgg-verydeep-19.mat` in the working directory used for the run, or pass an explicit `--model_weights` path.
- With the builder, pass `--model-weights ./imagenet-vgg-verydeep-19.mat`; explicit model paths are validated before execution.
- Missing image errors occur before model construction; if the traceback mentions `cv2.imread`/`check_image`, fix image paths first. If it mentions `scipy.io.loadmat` or the `.mat` filename, fix VGG weights.

## TensorFlow 2.x lacks `tf.contrib` or `tf.Session`

Symptom examples:

- `AttributeError: module 'tensorflow' has no attribute 'Session'`
- `AttributeError: module 'tensorflow' has no attribute 'contrib'`
- failure constructing the L-BFGS optimizer through `tf.contrib.opt.ScipyOptimizerInterface`

Cause: this repository targets TensorFlow 1.x APIs. The source uses `tf.Session()` and `tf.contrib.opt.ScipyOptimizerInterface` directly.

Fix: run in a TensorFlow 1.x-compatible runtime. TensorFlow 1.15 CPU was sufficient for CLI help and import-level inspection. If you must use TensorFlow 2.x, this generated skill does not provide a port; expect code changes beyond this sub-skill.

## Protobuf descriptor errors

Symptom examples:

- `TypeError: Descriptors cannot be created directly`
- errors mentioning generated protobuf code being out of date

Cause: older TensorFlow 1.x packages are commonly incompatible with protobuf 4.x.

Fix: use a protobuf version compatible with the TensorFlow 1.x runtime, commonly a 3.x release such as `protobuf<4`. Re-check TensorFlow import before running a render.

## CPU/GPU device failures

Symptom examples:

- CUDA library or device placement errors on a CPU-only host.
- TensorFlow reports that `/gpu:0` is unavailable.

Cause: `neural_style.py` parser default is `--device /gpu:0`, and the README assumes GPU is recommended. CPU-only hosts need an explicit CPU device.

Fix:

- Add `--device /cpu:0` to direct commands.
- The builder defaults to `/cpu:0`; override with `--device /gpu:0` only on a prepared CUDA/GPU runtime.
- GPU setup issues belong to the root runtime/troubleshooting docs; return here after TensorFlow can see the intended device.

## Memory exhaustion or very slow L-BFGS

Symptom examples:

- process is killed, stalls, or fails with allocation errors.
- L-BFGS consumes too much memory at large `--max_size` values.

Cause: the README notes that the default GPU backend plus L-BFGS can consume substantial memory. `get_content_image` scales the content image by `--max_size`, and style images are resized to match.

Fix:

- Reduce `--max_size` first; this lowers the tensor dimensions for both content and style images.
- Reduce `--max_iterations` for smoke tests.
- Switch from `--optimizer lbfgs` to `--optimizer adam` when memory is the constraint. Adam may require tuning `--learning_rate`, `--content_weight`, and `--style_weight` for final-quality output; those advanced tuning controls are covered by [advanced-controls](../../advanced-controls/SKILL.md).

## Paths containing `~`

Symptom: a direct command using a quoted `~` path fails with a missing-file error even though the file exists under the home directory.

Cause: the README warns not to use `~` in image paths. `neural_style.py` does not expand `~`; it joins strings and passes them to OpenCV.

Fix:

- Use a relative path from the checkout root, or use a fully expanded absolute path.
- The builder expands `~` for `--content`, `--style`, `--script`, `--output-dir`, and `--model-weights` before printing the command.

## Output directory exists but result is missing

Symptom: `<img_output_dir>` exists but no `<img_name>.png` appears.

Cause possibilities:

- Single-image output is nested one level deeper: `<img_output_dir>/<img_name>/<img_name>.png`.
- The run failed before `write_image_output`, so only the top-level output directory may have been created by `parse_args`.
- The process lacks write permission under the output directory.
- OpenCV `cv2.imwrite` failed silently; the source does not check its return value.

Fix:

1. Inspect `<img_output_dir>/<img_name>/`.
2. Check stderr/stdout for earlier TensorFlow, image path, VGG, device, or memory errors.
3. Try a writable relative output directory such as `./image_output`.
4. Use a short ASCII `--img_name` without path separators; pass the directory separately with `--img_output_dir` or builder `--output-dir`.

## Multiple styles from different directories

Symptom: the builder rejects repeatable `--style` paths that do not share one directory.

Cause: `neural_style.py` has one `--style_imgs_dir` for all names in `--style_imgs`. The simple builder preserves that model.

Fix: copy or symlink the selected style images into one staging directory and pass them from there, or use [advanced-controls](../../advanced-controls/SKILL.md) for richer multi-style workflows and weights.
