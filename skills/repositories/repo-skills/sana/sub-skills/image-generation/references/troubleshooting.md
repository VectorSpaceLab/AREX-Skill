# Sana Image Generation Troubleshooting

Use this reference when image generation, Sprint, ControlNet, quantization,
high-resolution inference, prompt-file batches, or Gradio launches fail.

## Quick Triage

1. Identify the surface: Diffusers, native batch script, native Python pipeline,
   Sprint, ControlNet, 4-bit/8-bit quantization, 2K/4K, or Gradio.
2. Verify model/config pairing and dtype before debugging output quality.
3. Verify CUDA and model/cache access before retrying expensive commands.
4. Reduce variables: one prompt, one image, batch size 1, 1024px or smaller,
   fixed seed, default steps, and no optional PAG/quantization until baseline
   works.
5. For ControlNet, validate the JSON and reference/control-map files before
   launching the model.

## CUDA Not Available

Symptoms:

- Native pipeline chooses CPU or Gradio prints a CPU warning.
- HED annotator or Sana model raises `.cuda()` or CUDA device errors.
- Generation appears to hang or is impractically slow on CPU.

Likely causes:

- PyTorch was installed without CUDA support.
- GPU is not visible to the process.
- Driver/CUDA runtime does not match the PyTorch build.
- The job is running in an environment without GPU allocation.

Actions:

```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
```

Do not claim CPU fallback for end-to-end Sana image, Sprint, ControlNet, 2K/4K,
or 4-bit generation. CPU import checks are useful, but generated media claims
need CUDA-backed verification.

## Missing Hugging Face Weights, Network, or Auth

Symptoms:

- `from_pretrained` cannot resolve a model id.
- Native `find_model` cannot download or locate an `hf://.../checkpoints/*.pth`
  checkpoint.
- Gemma text encoder, DC-AE VAE, ShieldGemma safety checker, ControlNet HED, or
  Nunchaku transformer load fails.
- Gradio app fails during startup before serving the page.

Likely causes:

- No network access or blocked downloads.
- Hugging Face token/auth missing for gated or rate-limited resources.
- Model id typo, wrong case, or using a `.pth` URI in Diffusers.
- Cache points at an incomplete or corrupted download.

Actions:

- Confirm exact model id or checkpoint label from
  [model-config-selection.md](model-config-selection.md).
- Use Diffusers IDs only with Diffusers `from_pretrained`; use `hf://...pth`
  labels only with native workflows.
- Pre-download model, VAE, text encoder, safety checker, ControlNet, and HED
  resources if network is unreliable.
- For Gradio, test the underlying non-server snippet first so safety-checker
  and model-load errors are visible outside the server.

## Wrong Model/Config Pair

Symptoms:

- `load_state_dict` reports many missing or unexpected keys.
- Shape mismatch around model blocks, PAG layers, or ControlNet modules.
- Sprint checkpoint fails in plain Sana pipeline or plain Sana checkpoint fails
  in Sprint.
- ControlNet checkpoint fails with a non-ControlNet config.

Likely causes:

- Mixing `SanaMS_*`, `SanaMSCM_*`, and `SanaMSControlNet_*` configs.
- Using 0.6B config with 1.6B checkpoint or the reverse.
- Using 2K/4K checkpoint with 1K config.
- Mixing Diffusers model id and native `.pth` workflow.

Actions:

- Recheck the config table in [model-config-selection.md](model-config-selection.md).
- For Sprint, use `configs/sana_sprint_config/...` and
  `scripts/inference_sana_sprint.py` or `SanaSprintPipeline`.
- For ControlNet, use `configs/sana_controlnet_config/...` and the ControlNet
  checkpoint label.
- Treat small `pos_embed` omissions as expected in native code, but investigate
  broad missing/unexpected key lists.

## Dtype Mismatch or Bad Outputs

Symptoms:

- Black images, NaNs, poor quality, or text encoder/VAE runtime errors.
- Diffusers downloads float32 weights unexpectedly and consumes too much disk.
- bf16 model fails on hardware that lacks bf16 support.

Likely causes:

- Missing `variant="fp16"` or `variant="bf16"` for Diffusers.
- Moving VAE/text encoder to unsafe dtype.
- Loading fp16 checkpoint with bf16 assumptions or vice versa.
- Hardware does not support requested dtype.

Actions:

- For fp16 Diffusers transformer weights: `variant="fp16"`,
  `torch_dtype=torch.float16`, then move `pipe.vae` and `pipe.text_encoder` to
  bf16 or fp32.
- For bf16 Diffusers weights: `variant="bf16"` when available and
  `torch_dtype=torch.bfloat16`.
- For native workflows, read `model.mixed_precision` and `vae.weight_dtype` from
  the chosen config; do not override blindly.
- If bf16 is unsupported, select an fp16 model/config family rather than forcing
  partial dtype changes.

## Out of Memory

Symptoms:

- CUDA OOM during transformer forward, VAE decode, ControlNet VAE encode, or
  HED preprocessing.
- 2K/4K jobs fail near decode.
- Gradio app starts but crashes on first request.

Actions in order:

1. Use batch size 1 and `num_images_per_prompt=1`.
2. Reduce height/width to 1024 or 512 and verify the model first.
3. Reduce steps only after confirming the model/config is correct.
4. For 4K Diffusers, enable VAE tiling:

```python
pipe.vae.enable_tiling(
    tile_sample_min_height=1024,
    tile_sample_min_width=1024,
    tile_sample_stride_height=896,
    tile_sample_stride_width=896,
)
```

5. Use a smaller model (0.6B), a smaller resolution model, 8-bit component
   quantization, or 4-bit Nunchaku/SVDQuant if installed.
6. Restart the Python process after OOM if CUDA memory fragmentation persists.

## xformers or flash-attn Fallback

Symptoms:

- Import errors for xformers or flash-attn.
- Warnings about disabled memory-efficient attention.
- Sprint behavior differs from standard image inference.

Notes and actions:

- Sprint code explicitly sets `DISABLE_XFORMERS=1`; do not treat xformers being
  disabled as a Sprint bug.
- Sana image configs can use linear attention and optional memory-efficient
  kernels. If optional kernels fail, first verify a smaller baseline without the
  optional acceleration.
- Rebuild/install optional kernels only when the target GPU, CUDA, PyTorch, and
  compiler stack are known compatible.

## ControlNet Ref-Image, Control Map, and Annotator Problems

Symptoms:

- JSON parsing succeeds but generation fails before sampling.
- `cv2.imread` returns `None`, image shape access fails, or PIL cannot open an
  image.
- HED detector tries to download `ControlNetHED.pth` and fails.
- `.cuda()` errors occur inside HED detector.
- Output ignores the intended sketch/edge map.

Actions:

```bash
python scripts/validate_controlnet_request.py --json-file controlnet_request.json --strict
```

- Ensure top-level JSON is a list of objects.
- Each item must have a non-empty `prompt` and exactly one of
  `ref_image_path` or `ref_controlmap_path`.
- Paths should resolve relative to the project directory or the JSON file.
- Use `ref_controlmap_path` when you already have a control map and want to
  bypass HED annotation.
- For `ref_image_path`, make sure `ControlNetHED.pth` is available or network
  can download it, and that CUDA is available because the HED detector moves to
  CUDA.
- Keep ControlNet batch size 1.
- If the control signal is too thin/thick, adjust `--thickness`; use
  `--blend_alpha` for debugging alignment.

## Prompt File Format Errors

Symptoms:

- `FileNotFoundError` for prompt file.
- JSON mode fails with type or key errors.
- Output files have surprising names or prompts are skipped.

Actions:

- Ordinary `scripts/inference.py` text mode expects one prompt per line.
- Ordinary JSON mode expects a mapping such as
  `{"case_0001": {"prompt": "..."}}`.
- ControlNet JSON mode expects a list of objects, not a mapping.
- Use `--sample_nums`, `--start_index`, and `--end_index` to bound large prompt
  files.
- Existing output files are skipped; delete or change the output directory when
  a clean rerun is needed.

## Gradio Port and Share Problems

Symptoms:

- Server starts on a different port than expected or fails with port in use.
- Public share link does not appear.
- Page loads but generation fails on request.

Actions:

- Set `DEMO_PORT=<port>` before the `python app/app_*.py` command.
- Omit `--share` when a public tunnel is not wanted or network policy blocks it.
- Set `ROOT_PATH` when running behind a reverse proxy.
- Check CUDA and model-cache startup logs; apps load models before serving.
- Confirm ShieldGemma safety checker access if the default app loads it.
- For 4-bit app startup, confirm Nunchaku import and CUDA support first.

## Quantization-Specific Failures

8-bit:

- Verify compatible bitsandbytes, Diffusers, Transformers, CUDA, and GPU.
- Use `device_map="balanced"` only when the environment supports accelerate
  placement.
- If quality regresses, compare the same prompt/seed against non-quantized bf16
  or fp16.

4-bit:

- Verify `nunchaku.models.transformer_sana.NunchakuSanaTransformer2DModel`
  imports before promising the run.
- Use the SVDQuant model `mit-han-lab/svdq-int4-sana-1600m` with a bf16 Sana
  base pipeline.
- The 4-bit app and pipeline assert CUDA-style operation; do not attempt CPU.
- PAG with 4-bit uses a Nunchaku-specific path; do not assume plain
  `SanaPAGPipeline` accepts the same transformer replacement in every engine
  version.
