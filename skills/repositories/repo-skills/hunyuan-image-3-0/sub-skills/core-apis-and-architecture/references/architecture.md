# Architecture

This repository is organized around a lazy package entry point and a small set
of cooperating objects:

```text
hunyuan_image_3 (lazy _LazyModule)
├─ configuration_hunyuan_image_3.py -> HunyuanImage3Config
├─ tokenization_hunyuan_image_3.py -> HunyuanImage3TokenizerFast, ImageInfo,
│   ImageTensor, JointImageInfo, CondImage, ResolutionGroup, TokenizerEncodeOutput
├─ image_processor.py -> HunyuanImage3ImageProcessor, resize_and_crop,
│   SliceVocabLogitsProcessor
├─ modeling_hunyuan_image_3.py -> HunyuanImage3ForCausalMM, HunyuanImage3Model,
│   HunyuanStaticCache, decoder helpers, generation glue
├─ hunyuan_image_3_pipeline.py -> HunyuanImage3Text2ImagePipeline,
│   FlowMatchDiscreteScheduler
├─ cache_utils.py -> cache_init, TaylorCacheContainer, CacheWithFreqsContainer
└─ system_prompt.py -> get_system_prompt
```

## Module responsibilities

| Module | Main responsibility | Key objects |
|---|---|---|
| `configuration_hunyuan_image_3.py` | Store architecture, token-id, VAE, ViT, and generation settings. | `HunyuanImage3Config` |
| `tokenization_hunyuan_image_3.py` | Build chat templates, special tokens, mixed text / image sections, and conversation helpers. | `HunyuanImage3TokenizerFast`, `Conversation`, `DecoratorSections`, `ResolutionGroup`, `ImageInfo`, `JointImageInfo`, `CondImage`, `TokenizerEncodeOutput` |
| `image_processor.py` | Resize and align input images, derive image metadata, and postprocess output images. | `HunyuanImage3ImageProcessor`, `resize_and_crop`, `SliceVocabLogitsProcessor` |
| `modeling_hunyuan_image_3.py` | Own the transformer backbone, multimodal input routing, generation glue, and the model-facing cache. | `HunyuanImage3ForCausalMM`, `HunyuanImage3Model`, `HunyuanStaticCache` |
| `hunyuan_image_3_pipeline.py` | Run the diffusion denoising loop and decode latents to images. | `HunyuanImage3Text2ImagePipeline`, `FlowMatchDiscreteScheduler` |
| `cache_utils.py` | Hold optional Taylor-cache state used for repeated-step acceleration. | `cache_init`, `TaylorCacheContainer`, `CacheWithFreqsContainer` |
| `utils/import_utils.py` | Provide the lazy import machinery used by `hunyuan_image_3.__init__`. | `_LazyModule`, `define_import_structure` |
| `system_prompt.py` | Select the built-in or custom system prompt string. | `get_system_prompt` |

## Lazy import behavior

`hunyuan_image_3/__init__.py` installs a `_LazyModule` using
`define_import_structure(__file__)`.

Practical consequences:

- `import hunyuan_image_3` should stay lightweight.
- Accessing a torch-backed symbol such as `HunyuanImage3ForCausalMM` triggers the
  backend branch only when the attribute is read.
- A `ModuleNotFoundError` during symbol access usually means a missing dependency or
  backend, not that the package name itself is invalid.
- `cache_utils` and the pipeline module are not top-level exports; import them
  directly from their modules.

## End-to-end generation flow

1. The caller supplies a prompt, optional reference image(s), a `message_list`, a seed,
   an image size, and a prompt mode.
2. `HunyuanImage3ForCausalMM.generate_image(...)` resolves `use_system_prompt` and
   `bot_task` through `get_system_prompt(...)`.
3. `prepare_model_inputs(...)` converts the user material into sections, token ids,
   image metadata, rope information, and cache objects.
4. `HunyuanImage3TokenizerFast.apply_chat_template(...)` and
   `encode_general(...)` build the mixed text / image token stream.
5. `HunyuanImage3ImageProcessor` resizes conditioning images, computes ratio tokens,
   and prepares full-attention slices for image spans.
6. `HunyuanStaticCache` stores the generation-time KV cache for the transformer path.
7. `generate(...)` dispatches by mode:
   - `gen_text` uses `GenerationMixin.generate(...)`.
   - `gen_image` delegates to `HunyuanImage3Text2ImagePipeline`.
8. The pipeline calls the model on every denoising step, applies optional Taylor-cache
   reuse, and decodes the final latents through the VAE.
9. `HunyuanImage3ImageProcessor.postprocess_outputs(...)` optionally aligns the output
   image size with the conditioned image ratio.

## Important object relationships

- `HunyuanImage3Config` is the single source of truth for dimensions, special-token ids,
  modal wiring, and generation flags.
- `HunyuanImage3TokenizerFast` knows special-token placement, conversation templates, and
  how to turn structured sections into token streams.
- `HunyuanImage3ImageProcessor` knows geometry, resizing, ratio selection, and conditional
  image conversion.
- `HunyuanImage3ForCausalMM` is the orchestrator that glues the tokenizer, image processor,
  transformer backbone, scheduler, and pipeline together.
- `HunyuanImage3Text2ImagePipeline` owns diffusion-time sampling and VAE decode only; it does
  not decide prompt policy.
- `FlowMatchDiscreteScheduler` is step logic only; it does not own prompt rewriting or image
  preprocessing.
- `cache_utils` only optimizes repeated steps; it does not change the public model contract.
- `skip_load_module` reduces what gets instantiated, but it does not make every later method
  safe. Any code path that touches a skipped module will still fail.
- `load_tokenizer(...)` must run before any path that reads `self.tokenizer` or uses
  tokenizer-backed generation helpers.

## Mixed text / image section logic

The tokenizer and image processor cooperate through section dictionaries. Common section types are:

- `text`
- `gen_image`
- `cond_vae_image`
- `cond_vit_image`
- `cond_joint_image`

`TokenizerEncodeOutput` then exposes the derived token tensor, text slices, image slices,
masks, and scatter indices that the model and pipeline consume.

## What this architecture intentionally does not cover

- CLI parser and shell recipe details
- Gradio launch wiring
- vLLM server/client deployment
- external prompt rewrite services beyond `get_system_prompt`
