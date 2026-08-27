# Paired Inference Workflows

Use these recipes from a prepared source checkout with the repository dependencies installed and CUDA available for actual model execution. The bundled helper scripts are safe planning utilities: they validate/preview inputs and print commands, but they do not download checkpoints, launch servers, or run model inference unless explicitly described.

## 1. Canny edge-to-image

Source quickstart task: take an RGB image, extract Canny edges, and generate an image from a prompt.

### Plan and validate the command

```bash
python sub-skills/paired-inference/scripts/build_paired_inference_command.py \
  --model_name edge_to_image \
  --input_image assets/examples/bird.png \
  --prompt "a blue bird" \
  --output_dir outputs \
  --low_threshold 100 \
  --high_threshold 200
```

Expected helper output is a command shaped like:

```bash
cd . && python src/inference_paired.py --input_image assets/examples/bird.png --prompt 'a blue bird' --output_dir outputs --model_name edge_to_image --low_threshold 100 --high_threshold 200
```

If the input image dimensions are not divisible by 8 and the file can be inspected, the helper warns that the source script will resize down to the nearest divisible-by-8 dimensions.

### Preview Canny preprocessing without the model

```bash
python sub-skills/paired-inference/scripts/preview_canny.py \
  --input_image assets/examples/bird.png \
  --output_image outputs/bird_canny_preview.png \
  --low_threshold 100 \
  --high_threshold 200 \
  --invert-preview
```

Use `--invert-preview` when you want the display-style inverted Canny visualization. Without it, the helper writes the raw control-map polarity produced by OpenCV Canny and expanded to three channels.

### Run source inference only when downloads and CUDA are acceptable

```bash
python src/inference_paired.py \
  --model_name "edge_to_image" \
  --input_image "assets/examples/bird.png" \
  --prompt "a blue bird" \
  --output_dir "outputs"
```

Expected source outputs for `.png` input:

- `outputs/bird_canny.png`: inverted Canny visualization saved by the edge branch.
- `outputs/bird.png`: generated RGB output image.

The constructor may download `edge_to_image_loras.pkl` into `checkpoints/` and will also require the Stable Diffusion Turbo components to be available through the model-loading stack.

## 2. Stochastic sketch-to-image

Source quickstart task: take a sketch plus a prompt, use stochastic guidance `gamma`, and save a generated image.

### Plan the command with deterministic seed and guidance

```bash
python sub-skills/paired-inference/scripts/build_paired_inference_command.py \
  --model_name sketch_to_image_stochastic \
  --input_image assets/examples/sketch_input.png \
  --prompt "ethereal fantasy concept art of an asteroid. magnificent, celestial, ethereal, painterly, epic, majestic, magical, fantasy art, cover art, dreamy" \
  --output_dir outputs \
  --gamma 0.4 \
  --seed 42
```

Expected helper output is a command shaped like:

```bash
cd . && python src/inference_paired.py --input_image assets/examples/sketch_input.png --prompt 'ethereal fantasy concept art of an asteroid. magnificent, celestial, ethereal, painterly, epic, majestic, magical, fantasy art, cover art, dreamy' --output_dir outputs --model_name sketch_to_image_stochastic --gamma 0.4 --seed 42
```

### Run source inference only when downloads and CUDA are acceptable

```bash
python src/inference_paired.py \
  --model_name "sketch_to_image_stochastic" \
  --input_image "assets/examples/sketch_input.png" \
  --gamma 0.4 \
  --seed 42 \
  --prompt "ethereal fantasy concept art of an asteroid. magnificent, celestial, ethereal, painterly, epic, majestic, magical, fantasy art, cover art, dreamy" \
  --output_dir "outputs"
```

Expected source output:

- `outputs/sketch_input.png`: generated image saved under the input basename.

For difficult sketch cases, inspect the input size before running. A 513x513 sketch is resized by the source script to 512x512, so the stochastic noise map has spatial shape `(64, 64)` because it is created as `(H // 8, W // 8)`.

## 3. Custom Pix2Pix-Turbo checkpoint inference

Use this path after the `training` sub-skill has produced a paired Pix2Pix-Turbo checkpoint compatible with `Pix2Pix_Turbo.save_model`.

### Plan the command

```bash
python sub-skills/paired-inference/scripts/build_paired_inference_command.py \
  --model_path checkpoints/my_pix2pix_checkpoint.pkl \
  --input_image path/to/input.png \
  --prompt "prompt used for this paired translation task" \
  --output_dir outputs
```

Expected helper output is shaped like:

```bash
cd . && python src/inference_paired.py --input_image path/to/input.png --prompt 'prompt used for this paired translation task' --output_dir outputs --model_path checkpoints/my_pix2pix_checkpoint.pkl
```

### Run source inference only when the checkpoint is present and CUDA is acceptable

```bash
python src/inference_paired.py \
  --model_path "checkpoints/my_pix2pix_checkpoint.pkl" \
  --input_image "path/to/input.png" \
  --prompt "prompt used for this paired translation task" \
  --output_dir "outputs"
```

Custom checkpoint branch notes:

- Do not also pass `--model_name`.
- Canny thresholds are not used in the custom branch.
- `--gamma` and `--seed` are not used in the custom branch.
- The checkpoint must contain the Pix2Pix-Turbo LoRA/skip schema described in [CLI and API reference](cli-and-api.md).

## 4. Local paired Gradio demos

The source repository provides two paired Gradio entry points. Both instantiate `Pix2Pix_Turbo` at module import, so launching them can trigger CUDA setup and model/checkpoint downloads before the UI is usable.

### Print Canny demo command and prerequisites

```bash
python sub-skills/paired-inference/scripts/build_gradio_command.py canny
```

The command printed by the helper is:

```bash
cd . && gradio gradio_canny2image.py
```

Source Canny demo facts:

- Loads `Pix2Pix_Turbo("edge_to_image")` at import.
- UI accepts uploaded PIL image, prompt, low Canny threshold, high Canny threshold, and Run button.
- Threshold sliders have minimum `1`, maximum `255`, defaults `100` and `200`, and step `10`.
- Process path resizes the input down to multiples of 8, computes Canny, runs the model, and returns both inverted Canny visualization and generated output.
- Source launch uses `debug=True, share=False`.

### Print sketch demo command and prerequisites

```bash
python sub-skills/paired-inference/scripts/build_gradio_command.py sketch
```

The command printed by the helper is:

```bash
cd . && gradio gradio_sketch2image.py
```

Source sketch demo facts:

- Loads `Pix2Pix_Turbo("sketch_to_image_stochastic")` at import.
- Canvas is configured for a 512x512 grayscale color-sketch input with inverted colors and default brush radius 4.
- Default style is `Fantasy art`; style templates wrap the user prompt.
- Sketch guidance slider ranges from `0` to `1`, default `0.4`, step `0.01`.
- Seed textbox defaults to `42`; Random uses a value up to the maximum signed 32-bit integer.
- The run path converts the sketch to RGB, applies the style template, creates a seeded latent noise map with shape `(1, 4, H // 8, W // 8)`, and calls the non-deterministic Pix2Pix-Turbo forward path.
- Source launch uses `debug=True, share=True`; treat this as a network exposure risk and change the source launch configuration before running on untrusted machines.

## Validation checklist before full inference

- Confirm exactly one selector: `--model_name edge_to_image`, `--model_name sketch_to_image_stochastic`, or `--model_path PATH`.
- Confirm a non-empty prompt and an existing image path relative to the source checkout.
- For edge-to-image, keep Canny thresholds within 0 to 255 and low threshold below high threshold.
- For sketch-to-image, keep `gamma` in the 0 to 1 range and use a fixed seed for reproducible stochastic variation.
- Expect the source script to resize images down to multiples of 8; pre-resize yourself if exact spatial dimensions matter.
- Do not expect CPU inference from the source code: paired model construction and tensors are moved to CUDA.
- Approve network/model downloads before first run, because pretrained selectors may download paired LoRA files and the model stack may fetch Stable Diffusion Turbo components.
