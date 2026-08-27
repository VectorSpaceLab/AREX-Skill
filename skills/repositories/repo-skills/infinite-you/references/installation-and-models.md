# Installation and Models

## Purpose

Read this before running local InfiniteYou-FLUX inference or the self-contained demo. It summarizes dependency pins, bundled runtime behavior, CUDA expectations, model layout, model access, and memory constraints.

## Bundled implementation and dependencies

This skill bundles the implementation modules needed for generation under `runtime/pipelines/`. You do not need the original repository checkout for normal use of the generated skill entry points.

Use an isolated Python 3.10 or 3.11 environment; Python 3.11 was used for inspection. From the generated skill directory, install the bundled dependency pins:

```bash
python -m pip install -r runtime/requirements.txt
```

Key pinned packages in the snapshot:

| Package | Version |
| --- | --- |
| `torch` | `2.6.0` |
| `torchvision` | `0.21.0` |
| `diffusers` | `0.31.0` |
| `transformers` | `4.48.0` |
| `accelerate` | `1.6.0` |
| `gradio` | `5.23.1` |
| `insightface` | `0.7.3` |
| `facexlib` | `0.3.0` |
| `onnxruntime` | `1.19.2` |
| `optimum-quanto` | `0.2.7` |
| `peft` | `0.14.0` |
| `huggingface-hub` | `0.28.1` |

Run a no-generation environment check:

```bash
python scripts/check_infinite_you_environment.py --require-cuda
```

The checker imports `runtime/pipelines` automatically and reports which implementation source was selected. Use `--implementation-root` only for intentional refresh/debug comparisons against another compatible source tree.

## CUDA requirement

Full InfiniteYou-FLUX generation is CUDA-required in this snapshot. The code moves the base pipeline, ArcFace path, image projection model, and generated embeddings to CUDA. `cpu_offload` reduces peak VRAM by staging modules between CPU and CUDA, but it is not CPU-only execution.

## Model variants

| Variant | Use when | Notes |
| --- | --- | --- |
| `aes_stage2` | Default; stronger text-image alignment and aesthetics. | Stage-2 SFT model. |
| `sim_stage1` | Higher identity similarity is more important. | If prompt alignment weakens, try `infusenet_guidance_start=0.1` or lower conditioning scale. |

Only InfiniteYou-FLUX `v1.0` is present in this repository snapshot.

## Expected local model layout

The generated entry points default to local model directories to avoid surprise downloads:

```text
models/InfiniteYou/
  infu_flux_v1.0/
    aes_stage2/
      InfuseNetModel/
      image_proj_model.bin
    sim_stage1/
      InfuseNetModel/
      image_proj_model.bin
  supports/
    insightface/
    optional_loras/
      flux_realism_lora.safetensors
      flux_anti_blur_lora.safetensors

models/FLUX.1-dev/
  transformer/
  text_encoder_2/
  ... other FLUX base model files ...
```

Validate the InfiniteYou tree without downloading anything:

```bash
python sub-skills/demo-and-model-setup/scripts/check_model_layout.py \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev
```

## Download and gated model policy

The bundled code can still invoke upstream Hugging Face loading behavior when full generation starts. The generated wrappers prevent surprise downloads by default and require `--allow-downloads` when paths are non-local or incomplete.

Potential external model sources:

- `ByteDance/InfiniteYou` for InfiniteYou weights and support files.
- `black-forest-labs/FLUX.1-dev` for the FLUX base model.

The FLUX base model may require accepting the model agreement and authenticating with a Hugging Face token. Do not place tokens in scripts, prompts, committed files, or generated skill content.

## Memory requirements

The README reports approximate peak VRAM:

| Mode | Peak VRAM |
| --- | --- |
| full bf16 inference | 43 GB |
| `cpu_offload` only | 30 GB |
| `quantize_8bit` only | 24 GB |
| both `cpu_offload` and `quantize_8bit` | 16 GB |

For first local runs on limited GPUs, start with both memory flags and default image size. Increase size or remove memory flags only after a stable result.

## Responsible setup checklist

1. Confirm the intended use complies with the code, model, base-model, LoRA, and face-model licenses.
2. Create an isolated Python environment and install `runtime/requirements.txt`.
3. Validate the bundled runtime and CUDA with the root checker.
4. Validate local model layout or explicitly authorize gated downloads.
5. Run local-inference dry-run and `--check-only` before actual generation.
6. Use the self-contained Gradio launcher only after model layout/CUDA checks pass.
