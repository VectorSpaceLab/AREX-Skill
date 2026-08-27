# Model Layout and Downloads

This guide describes the local files expected by the self-contained InfiniteYou inference and Gradio demo entry points. The bundled validator checks these paths without downloading anything.

## Two different knobs

| Knob | Default in the demo workflow | Meaning |
| --- | --- | --- |
| `model_dir` | `./models/InfiniteYou` | Root directory for InfiniteYou weights and support assets. |
| `base_model_path` | `./models/FLUX.1-dev` for generated entry points; `black-forest-labs/FLUX.1-dev` only when downloads/access are explicitly allowed | Source for the FLUX base model. This may be a local directory or a gated Hugging Face repo id. |

Keep these separate. `model_dir` stores the InfiniteYou release tree; `base_model_path` points to the FLUX base model used by the pipeline.

## Canonical local tree

```text
./models/InfiniteYou/
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
```

## Path roles

| Path | Required | Purpose |
| --- | --- | --- |
| `infu_flux_v1.0/aes_stage2/InfuseNetModel` | Yes | Default InfiniteYou model variant used by the demo. |
| `infu_flux_v1.0/aes_stage2/image_proj_model.bin` | Yes | Identity projection weights paired with the default model variant. |
| `infu_flux_v1.0/sim_stage1/InfuseNetModel` | Yes | Alternate variant that favors higher identity similarity. |
| `infu_flux_v1.0/sim_stage1/image_proj_model.bin` | Yes | Identity projection weights for the alternate variant. |
| `supports/insightface` | Yes | Face analysis support files used for landmark extraction and identity setup. |
| `supports/optional_loras/flux_realism_lora.safetensors` | Optional | Extra LoRA adapter for a realism-oriented style. |
| `supports/optional_loras/flux_anti_blur_lora.safetensors` | Optional | Extra LoRA adapter for blur reduction. |

The optional LoRAs are off by default. They become required only when a caller explicitly asks for them or when the validator is run with `--require-optional-loras`.

## Base model access

The generated entry points default to a local FLUX directory such as `./models/FLUX.1-dev`. The gated model id `black-forest-labs/FLUX.1-dev` is supported only when the user explicitly allows downloads/access.

- If you use the gated repo id, you may need to accept its license and authenticate with a Hugging Face token before a download can succeed.
- If you already have a local FLUX directory, point the runtime at that directory instead of the repo id.
- A local FLUX directory should contain the FLUX weights expected by the pipeline, including the transformer and text-encoder subfolders used at load time.

The bundled validator warns when the base model looks like the gated repo id. It does not attempt a download.

## Generated entry point behavior

The generated local inference and Gradio entry points use the bundled `runtime/pipelines/` code and default to local model paths. They do not require the original checkout.

1. `--dry-run` and `--check-only` modes never download models or instantiate the heavy pipeline.
2. Full generation or demo launch checks local model paths first.
3. If local paths are missing or a remote repo id is used, full execution refuses to proceed unless `--allow-downloads` is set.
4. With `--allow-downloads`, the upstream pipeline may use Hugging Face loading or fallback download behavior, so license/authentication must already be handled.

For offline or pre-seeded setups, populate the model tree first and validate it before launch.

## Validation checklist

Run the bundled validator when you want a quick layout check:

- confirm the InfiniteYou model root exists
- confirm both model variants are present
- confirm the InsightFace support tree exists
- optionally require the LoRA files
- note whether the base model is local or likely gated

The validator only checks the filesystem. It never downloads models, opens a browser, or starts Gradio. For demo-specific preflight, also run `scripts/launch_infinite_you_gradio.py --check-only` from this sub-skill.
