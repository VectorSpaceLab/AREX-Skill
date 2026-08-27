# Inference API Troubleshooting

Use this guide for failures around `sgm.inference.api.SamplingPipeline`, `SamplingParams`, SDXL model specs, helper image conversion, and base/refiner handoff.

## Pipeline Construction Fails Immediately

Symptoms:

- `FileNotFoundError`, `IsADirectoryError`, or YAML parse errors from config loading.
- Model load returns `None` or raises while reading a checkpoint.
- The pipeline tries to access CUDA on a CPU-only host.

Likely causes and recovery:

- `config_path` does not point to a directory containing `sd_xl_base.yaml` or `sd_xl_refiner.yaml`. Pass the directory that contains those exact filenames.
- `model_path` does not contain the checkpoint name expected by `model_specs`, such as `sd_xl_base_1.0.safetensors` for `SDXL_V1_BASE`.
- The constructor defaults to `device="cuda"` and `use_fp16=True`, while the public sampling methods call helpers that still default internal tensors/autocast to CUDA. In CPU-only planning, do not instantiate the pipeline; use `scripts/inspect_inference_api.py --json`. If CPU loading is intentionally attempted, set `device="cpu"`, consider `use_fp16=False`, and expect to patch or wrap helper calls before sampling.

## Checkpoint And Config Mismatch

Symptoms:

- `load_state_dict` reports missing keys or unexpected keys.
- Base model loads with a refiner checkpoint, or refiner loads with a base checkpoint.
- Sampling fails after apparently successful config parsing.

Recovery:

1. Inspect `model_specs` with `python scripts/inspect_inference_api.py --json`.
2. Match `ModelArchitecture.SDXL_V1_BASE` with `sd_xl_base.yaml` and `sd_xl_base_1.0.safetensors`.
3. Match `ModelArchitecture.SDXL_V1_REFINER` with `sd_xl_refiner.yaml` and `sd_xl_refiner_1.0.safetensors`.
4. Use the corresponding `0.9` checkpoint names for `SDXL_V0_9_*` architectures.
5. Check checkpoint license/access separately; missing gated files can look like ordinary missing-path errors.

## Invalid Sampler, Discretization, Or Guider

Symptoms:

- `ValueError: unknown sampler ...`.
- `ValueError: unknown discretization ...`.
- `NotImplementedError` from guider or thresholder configuration.

Recovery:

- Use exact enum values from the API reference. Valid samplers are `EulerEDMSampler`, `HeunEDMSampler`, `EulerAncestralSampler`, `DPMPP2SAncestralSampler`, `DPMPP2MSampler`, and `LinearMultistepSampler`.
- Valid discretizations are `LegacyDDPMDiscretization` and `EDMDiscretization`.
- Valid guiders are `VanillaCFG` and `IdentityGuider`.
- Only `Thresholder.NONE` is implemented. Do not invent dynamic thresholding values.
- Prefer enum members, for example `Sampler.DPMPP2M`, when writing new code; validate user-provided strings before constructing `SamplingParams`.

## Image-To-Image Strength Or Shape Problems

Symptoms:

- Assertion failure inside `Img2ImgDiscretizationWrapper`.
- Shape errors when `image_to_image` reads `image.shape[2]` and `image.shape[3]`.
- Unexpected cropped or resized output dimensions.

Recovery:

- Validate `0.0 <= img2img_strength <= 1.0` before calling `image_to_image`.
- Use `[batch, channels, height, width]` image tensors scaled to `[-1, 1]`, normally from `get_input_image_tensor`.
- Remember `get_input_image_tensor` rounds image width and height down to multiples of 64.
- For direct tensor inputs, ensure height and width are compatible with the model factor of 8 and SDXL's practical multiple-of-64 expectation.

## Base Plus Refiner Handoff Fails

Symptoms:

- Refiner receives decoded RGB samples and raises shape or channel errors.
- Refiner output dimensions are wrong.
- Refiner conditioning behaves like the wrong SDXL version.

Recovery:

- Call the base method with `return_latents=True` and pass the second returned value, `samples_z`, to `refiner(..., image=samples_z)`.
- Use matching pairs: `SDXL_V1_BASE` with `SDXL_V1_REFINER`, or `SDXL_V0_9_BASE` with `SDXL_V0_9_REFINER`.
- Do not pass decoded `samples` to `refiner`; refiner uses `skip_encode=True` and expects latent input.

## Missing Optional Dependencies

Symptoms:

- Import errors mentioning `imwatermark`, `open_clip`, `xformers`, image libraries, or transformer/encoder modules.
- Sampling code imports but model construction fails when config targets are instantiated.

Recovery:

- `sgm.inference.helpers` imports `imwatermark` for watermark embedding in save helpers.
- SDXL configs reference OpenCLIP embedder modules and xformers attention names; ensure the runtime environment includes compatible optional dependencies before GPU sampling.
- For inspection-only tasks, use the bundled inspection script; it is designed to report import errors cleanly and avoids checkpoint loads.
- Do not route UI demo or watermark detection workflows here; use the demos/watermarking sibling for those tasks.

## CPU-Only Or CUDA Unavailable

Symptoms:

- `Torch not compiled with CUDA enabled`.
- CUDA device initialization errors.
- Half-precision errors after forcing CPU.

Recovery:

- Treat CPU-only environments as API-inspection environments. Use `scripts/inspect_inference_api.py --assert-expected`.
- For actual sampling, move to a CUDA-capable environment with compatible PyTorch, model checkpoints, and optional dependencies.
- If debugging on CPU is unavoidable, instantiate with `device="cpu"` and `use_fp16=False`, but remember the public sampling methods still call CUDA-default helper paths unless patched or wrapped. Do not expect this to be a supported performance path.

## Planning Without Loading Checkpoints

When a user asks for a plan, code skeleton, or diagnosis and checkpoints are unavailable:

1. Use the inspection script to capture exact signatures and spec names.
2. Build code around `model_specs[model_id].config` and `.ckpt` instead of hard-coding unknown files.
3. Add preflight file checks before `SamplingPipeline(...)`.
4. State clearly that API inspection was CPU-only and that model execution needs checkpoint/device validation.
