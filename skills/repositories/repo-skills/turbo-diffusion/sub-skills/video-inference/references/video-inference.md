# One-shot TurboDiffusion video inference

This reference covers non-interactive command construction for TurboDiffusion's public Wan inference scripts. The bundled helpers render commands only; the rendered command is what a user runs in a prepared TurboDiffusion environment with model assets already present.

## When to use this workflow

Use this workflow for:

- Wan2.1 T2V: text prompt -> video, one DiT checkpoint via `--dit_path`.
- Wan2.2 I2V: input image + text prompt -> video, high-noise and low-noise DiT checkpoints via `--high_noise_model_path` and `--low_noise_model_path`.
- Choosing quantized vs unquantized checkpoints and the matching `--quant_linear` flag.
- Choosing `--attention_type`, `--sla_topk`, resolution, frame count, seed, and output path.
- Reviewing output expectations without downloading weights or launching generation.

Route elsewhere when the task is interactive serving, checkpoint conversion/quantization/training, or low-level CUDA/SLA build/debugging.

## No-download preflight checklist

Before rendering or running a command, confirm the following without fetching anything automatically:

1. **Runtime is prepared.** TurboDiffusion, PyTorch/CUDA, and the custom ops required by the selected acceleration path are installed. Full generation requires CUDA and large model weights; parser/help checks do not prove full model readiness.
2. **Source-layout imports are handled.** If using the public source scripts, make helper packages importable with a source-layout `PYTHONPATH` such as `PYTHONPATH=turbodiffusion`, or use an equivalent layout where `imaginaire`, `rcm`, `modify_model`, `serve`, `SLA`, and `ops` resolve.
3. **Assets are already present.** Supply explicit VAE, text encoder, DiT, and I2V image/checkpoint paths. The bundled helpers intentionally do not download or infer remote assets.
4. **Quantization flag matches checkpoint type.** Quantized filenames usually include `quant`; those commands need `--quant_linear`. Unquantized checkpoints should normally omit it.
5. **Prompt is suitable.** The repository notes that current models were trained on long English prompts; short prompts or non-English prompts may reduce quality unless expanded.
6. **Output path has a video suffix.** Include an extension such as `.mp4`, `.gif`, or `.webm`; create the output directory before model execution if your runtime does not do so.

## Wan2.1 T2V command planning

Typical decisions:

- `--model`: `Wan2.1-1.3B` for the 1.3B model family or `Wan2.1-14B` for 14B checkpoints.
- `--dit_path`: the T2V DiT checkpoint path. Use a checkpoint that matches the model family.
- `--resolution`: `480p` or `720p`. The README model catalog lists best-quality resolutions, but all listed checkpoints are documented as supporting both.
- `--num_steps`: 1-4; default 4. Fewer steps are faster but may reduce quality.
- `--sigma_max`: default 80. Larger values, such as 1600, may increase quality at the cost of diversity.
- `--attention_type`: `sagesla` by default in examples, `sla`, or `original`.
- `--sla_topk`: default 0.1; README recommends 0.15 for better visual quality in some cases.

Render a command with the bundled helper:

```bash
python scripts/build_t2v_command.py \
  --model Wan2.1-1.3B \
  --dit-path checkpoints/TurboWan2.1-T2V-1.3B-480P-quant.pth \
  --vae-path checkpoints/Wan2.1_VAE.pth \
  --text-encoder-path checkpoints/models_t5_umt5-xxl-enc-bf16.pth \
  --prompt "A long English prompt describing the subject, scene, camera motion, lighting, and style." \
  --resolution 480p \
  --quant-linear \
  --attention-type sagesla \
  --sla-topk 0.1 \
  --save-path output/t2v_sample.mp4
```

The helper prints a shell command resembling:

```bash
PYTHONPATH=turbodiffusion python turbodiffusion/inference/wan2.1_t2v_infer.py --model Wan2.1-1.3B --dit_path ...
```

Edit the `--script`, `--python`, or `--pythonpath` helper options if your public source layout uses different names.

## Wan2.2 I2V command planning

Typical decisions:

- `--model`: only `Wan2.2-A14B` is exposed by the one-shot I2V parser.
- `--high_noise_model_path` and `--low_noise_model_path`: separate checkpoint roles. Do not swap them; the high-noise model is loaded first and switches to the low-noise model when `t_cur < --boundary`.
- `--image_path`: input image path. The script opens the image with PIL and converts to RGB.
- `--adaptive_resolution`: resizes according to the input image aspect ratio while preserving the target area implied by `--resolution` and `--aspect_ratio`.
- `--ode`: uses ODE sampling; the source help describes it as sharper but less robust than SDE.
- `--sigma_max`: default 200 for I2V.

Render a command with the bundled helper:

```bash
python scripts/build_i2v_command.py \
  --high-noise-model-path checkpoints/TurboWan2.2-I2V-A14B-high-720P-quant.pth \
  --low-noise-model-path checkpoints/TurboWan2.2-I2V-A14B-low-720P-quant.pth \
  --vae-path checkpoints/Wan2.1_VAE.pth \
  --text-encoder-path checkpoints/models_t5_umt5-xxl-enc-bf16.pth \
  --image-path assets/i2v_inputs/i2v_input_0.jpg \
  --prompt "A long English prompt that describes motion starting from the input image." \
  --resolution 720p \
  --adaptive-resolution \
  --quant-linear \
  --attention-type sagesla \
  --sla-topk 0.1 \
  --ode \
  --save-path output/i2v_sample.mp4
```

The helper checks for common I2V mistakes before printing the command: missing image path, high/low names that look swapped, only one checkpoint marked as quantized, or quantized checkpoints without `--quant_linear`.

## Output validation after execution

After a real generation run, validate only the resulting artifact and logs; do not treat command rendering as model validation.

- Confirm the output file exists, is non-empty, and has the requested suffix.
- Confirm the command logs loaded the expected DiT checkpoint(s), VAE, text encoder, prompt, attention type, and resolution.
- For I2V, confirm logs mention the input image path and either fixed resolution or adaptive resolution dimensions.
- The source scripts save at 16 fps. With the default 81 frames, this is roughly a five-second video.
- With `--num_samples > 1`, the source saver arranges samples into a grid-like output rather than separate files; use separate runs if distinct files are required.
