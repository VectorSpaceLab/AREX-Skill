# Unpaired inference workflows

These workflows separate safe command construction from actual model execution. The bundled helper validates arguments and prints a source-checkout command; it does not import torch, instantiate the model, download checkpoints, or run inference.

## General workflow

1. Work in a prepared img2img-turbo source checkout with the repository dependencies installed and CUDA available.
2. Choose one mode:
   - Pretrained: `--model_name` is one of `day_to_night`, `night_to_day`, `clear_to_rainy`, or `rainy_to_clear`; omit prompt and direction.
   - Custom: `--model_path` points to a CycleGAN-Turbo checkpoint; include both `--prompt` and `--direction`.
3. Run the command helper from the source checkout root, or pass the checkout root explicitly through `--source_root` if you invoke the helper from elsewhere:

   ```bash
   python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
     --source_root . \
     --model_name day_to_night \
     --input_image assets/examples/day2night_input.png \
     --output_dir outputs
   ```

4. Inspect the printed command, then run it from the source checkout when CUDA/checkpoints/downloads are acceptable.
5. Confirm the expected output file exists at `OUTPUT_DIR/<input basename>`. The source script creates `OUTPUT_DIR` when needed and saves using the input basename.

## Pretrained day to night

Use for day driving images that should become night driving images. The model supplies caption `driving in the night` and direction `a2b` internally.

Build the command:

```bash
python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
  --source_root . \
  --model_name day_to_night \
  --input_image assets/examples/day2night_input.png \
  --output_dir outputs \
  --image_prep resize_512x512
```

Command to run from the source checkout:

```bash
python src/inference_unpaired.py \
  --model_name day_to_night \
  --input_image assets/examples/day2night_input.png \
  --output_dir outputs \
  --image_prep resize_512x512
```

Expected saved file: `outputs/day2night_input.png`.

Do not add `--prompt` or `--direction`; those are assertion-prone and unnecessary for this pretrained model.

## Pretrained night to day

Use for night driving images that should become day driving images. The model supplies caption `driving in the day` and direction `b2a` internally.

```bash
python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
  --source_root . \
  --model_name night_to_day \
  --input_image assets/examples/night2day_input.png \
  --output_dir outputs
```

Then run the printed source-checkout command. Expected saved file: `outputs/night2day_input.png`.

## Pretrained clear to rainy

Use for clear driving images that should become rainy driving images. The model supplies caption `driving in heavy rain` and direction `a2b` internally.

```bash
python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
  --source_root . \
  --model_name clear_to_rainy \
  --input_image assets/examples/clear2rainy_input.png \
  --output_dir outputs
```

Then run the printed source-checkout command. Expected saved file: `outputs/clear2rainy_input.png`.

## Pretrained rainy to clear

Use for rainy driving images that should become clear driving images. The model supplies caption `driving in the day` and direction `b2a` internally.

```bash
python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
  --source_root . \
  --model_name rainy_to_clear \
  --input_image assets/examples/rainy2clear_input.png \
  --output_dir outputs
```

Then run the printed source-checkout command. Expected saved file: `outputs/rainy2clear_input.png`.

## Optional fp16 inference

Add `--use_fp16` only after a normal command validates and the selected GPU supports half precision well:

```bash
python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
  --source_root . \
  --model_name day_to_night \
  --input_image assets/examples/day2night_input.png \
  --output_dir outputs \
  --use_fp16
```

The source script halves the model and input tensor. This can reduce memory use and improve speed on suitable CUDA GPUs, but it does not remove the CUDA requirement.

## Custom checkpoint: A to B

Use this when `--model_path` points to a custom CycleGAN-Turbo checkpoint and the input image belongs to training domain A. Supply a target-domain B prompt and `--direction a2b`.

```bash
python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
  --source_root . \
  --model_path checkpoints/custom_cyclegan_turbo.pkl \
  --input_image path/to/domain_a_image.png \
  --prompt "<target-domain-B prompt>" \
  --direction a2b \
  --output_dir outputs_custom_a2b \
  --image_prep resize_512x512
```

Printed command shape:

```bash
python src/inference_unpaired.py \
  --model_path checkpoints/custom_cyclegan_turbo.pkl \
  --input_image path/to/domain_a_image.png \
  --prompt "<target-domain-B prompt>" \
  --direction a2b \
  --output_dir outputs_custom_a2b \
  --image_prep resize_512x512
```

For a horse-to-zebra checkpoint trained with horses as domain A and zebras as domain B, the documented example input name `assets/examples/my_horse2zebra_input.jpg` is an appropriate source-domain fixture name. Use the actual target-domain prompt from the checkpoint's training setup rather than guessing if training records are available.

## Custom checkpoint: B to A

Use this when the input image belongs to training domain B and you want the reverse mapping into domain A. Supply a target-domain A prompt and `--direction b2a`.

```bash
python sub-skills/unpaired-inference/scripts/build_unpaired_inference_command.py \
  --source_root . \
  --model_path checkpoints/custom_cyclegan_turbo.pkl \
  --input_image path/to/domain_b_image.png \
  --prompt "<target-domain-A prompt>" \
  --direction b2a \
  --output_dir outputs_custom_b2a
```

If the checkpoint was trained with fixed prompt files, copy the exact target-domain fixed prompt into `--prompt` for the requested direction.

## Batch-like use without changing source code

The source inference CLI processes one image per process and saves by basename. For a small directory of images, loop over files and use an output directory whose contents may be overwritten intentionally:

```bash
mkdir -p outputs_day_to_night
for img in inputs_day/*.png; do
  python src/inference_unpaired.py \
    --model_name day_to_night \
    --input_image "$img" \
    --output_dir outputs_day_to_night
done
```

Before running a large loop, test one file and confirm that no two input paths share the same basename. If basenames collide, the later output will overwrite the earlier one.

## Validation checklist after a run

- The process completed without CUDA, xformers, checkpoint-download, prompt/direction, or image-size errors.
- `OUTPUT_DIR` exists.
- `OUTPUT_DIR/<input basename>` exists and has the original input image dimensions, because the source script resizes the output back to the original width and height before saving.
- For pretrained mode, the command contains `--model_name` and does not contain `--prompt`, `--direction`, or `--model_path`.
- For custom mode, the command contains `--model_path`, `--prompt`, and `--direction`, and does not contain `--model_name`.
