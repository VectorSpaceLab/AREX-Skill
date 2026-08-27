# Troubleshooting

## 1. Install or import fails

Check these basics first:

- Python target: 3.12 or newer.
- The package must be installed in editable or equivalent form so the repo package
  resolves correctly.
- The runtime dependencies from `requirements.txt` must be present, including
  `einops`, `numpy`, `pillow`, `diffusers`, `safetensors`, `tokenizers`,
  `transformers[accelerate,tiktoken]`, `huggingface_hub[cli]`, and `loguru`.
- The torch stack must match the environment you intend to use for generation.

Symptom patterns:

- `import hunyuan_image_3` fails: the package is not installed or the module search
  path is wrong.
- `HunyuanImage3ForCausalMM` lookup fails after a lazy import: a torch-side dependency
  or the backend branch is missing.
- `hunyuan-image` crashes with a `TypeError`: the console-script wiring in this snapshot
  is broken; use the direct Python entry path or the bundled smoke helper instead.

## 2. Optional backend or dependency failures during lazy import

The package uses lazy loading, so a symbol error usually means one of the symbol's own
dependencies is missing.

Common checks:

- `HunyuanImage3ForCausalMM` depends on torch, `einops`, `transformers`, `diffusers`,
  and the model-local modules.
- `HunyuanImage3ImageProcessor` depends on `torchvision` and SigLIP2 fast image-processor
  support.
- `flashinfer` is optional and should only affect optimized paths.
- If the import error mentions `Siglip2ImageProcessorFast`, verify the installed
  `transformers` build and image-processing extras.

## 3. `skip_load_module` or config incompatibility

`skip_load_module={"all"}` expands to:

- `vae`
- `vit`
- `timestep_emb`
- `patch_embed`
- `time_embed`
- `final_layer`
- `time_embed_2`
- `transformers`

That still leaves `image_processor` and `cached_rope` construction in place.
It is enough for constructor smoke, but not enough for full generation.

Other compatibility traps:

- `HunyuanImage3ImageProcessor` still expects a valid `vit_type` and `vit_processor`.
- `load_tokenizer(...)` must be called before any code path that reads `self.tokenizer`.
- A minimal config that omits the multimodal wiring fields may construct the config object
  but still fail when the image processor is created.

## 4. Responsibility confusion

Use the right object for the right job:

- `HunyuanImage3Config` sets dimensions, ids, and high-level wiring.
- `HunyuanImage3TokenizerFast` builds templates and special-token sequences.
- `HunyuanImage3ImageProcessor` handles image geometry and metadata.
- `HunyuanImage3ForCausalMM` orchestrates the model and generation flow.
- `HunyuanImage3Text2ImagePipeline` owns denoising and VAE decode.
- `FlowMatchDiscreteScheduler` owns step timing only.

If a task is really about prompt modes or image-conditioning policy, route to the
sibling `prompt-and-image-conditioning` sub-skill.

## 5. Optional accelerator paths

- `flashinfer` and FlashAttention are performance paths, not the baseline API contract.
- Do not treat their absence as a fatal core-API failure unless you are explicitly
  trying to exercise the optimized branch.

## 6. Safe recovery path

When in doubt, run the bundled smoke helper from this sub-skill and confirm the import
surface before digging into model generation.

```bash
python scripts/check_core_api_surface.py
```
