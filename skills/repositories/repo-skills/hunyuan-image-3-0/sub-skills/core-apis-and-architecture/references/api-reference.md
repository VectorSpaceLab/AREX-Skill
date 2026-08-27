# API reference

This page summarizes the importable objects and signatures that matter for the
core API / architecture sub-skill. For CLI recipes, use the sibling
`local-inference-cli` sub-skill. For system-prompt semantics, use the sibling
`prompt-and-image-conditioning` sub-skill.

## Import map

`import hunyuan_image_3` is lazy. The verified export structure exposes:

- No-backend exports: `HunyuanImage3Config`, `HunyuanImage3ImageProcessor`,
  `HunyuanImage3TokenizerFast`, `ImageInfo`, `ImageTensor`, `JointImageInfo`,
  `CondImage`, `ResolutionGroup`, `Siglip2VisionTransformer`, `LightProjector`,
  `get_system_prompt`
- Torch-backed exports: `HunyuanImage3ForCausalMM`, `HunyuanImage3Model`,
  `HunyuanImage3PreTrainedModel`, `TimestepEmbedder`, `UNetDown`, `UNetUp`,
  `CachedRoPE`, `apply_rotary_pos_emb`, `build_batch_2d_rope`

Direct imports for this sub-skill that are not top-level exports:

- `hunyuan_image_3.hunyuan_image_3_pipeline.HunyuanImage3Text2ImagePipeline`
- `hunyuan_image_3.hunyuan_image_3_pipeline.FlowMatchDiscreteScheduler`
- `hunyuan_image_3.cache_utils.cache_init`
- `hunyuan_image_3.cache_utils.TaylorCacheContainer`
- `hunyuan_image_3.cache_utils.CacheWithFreqsContainer`

## Core objects

| Object | Signature / role | Notes |
|---|---|---|
| `HunyuanImage3Config` | `HunyuanImage3Config(...)` | Stores architecture, token-id, VAE, ViT, and generation fields. `model_type="Hunyuan"`; `keys_to_ignore_at_inference=["past_key_values"]`. `attention_head_dim` defaults to `hidden_size // num_attention_heads` when omitted. |
| `HunyuanImage3ForCausalMM` | `HunyuanImage3ForCausalMM(config, skip_load_module:set[str]={}, use_dist_vae=False, wgt_path="")` | Main orchestrator. Owns the tokenizer, image processor, optional VAE / ViT / transformer modules, cached RoPE, and generation helpers. |
| `HunyuanImage3ForCausalMM.from_config` | `from_config(config, skip_load_module:set[str]={})` | Convenience constructor that forwards to `__init__`. |
| `HunyuanImage3ForCausalMM.load_tokenizer` | `load_tokenizer(tokenizer)` | Loads `HunyuanImage3TokenizerFast.from_pretrained(tokenizer, model_version=config.model_version)`. |
| `HunyuanImage3ForCausalMM.generate_image` | `generate_image(prompt=None, image=None, message_list=None, seed=None, image_size="auto", use_system_prompt=None, system_prompt=None, bot_task=None, infer_align_image_size=False, use_taylor_cache=False, taylor_cache_interval=None, taylor_cache_order=None, taylor_cache_enable_first_enhance=None, taylor_cache_first_enhance_steps=None, taylor_cache_enable_tailing_enhance=None, taylor_cache_tailing_enhance_steps=None, taylor_cache_low_freqs_order=None, taylor_cache_high_freqs_order=None, **kwargs)` | Resolves prompt mode, builds model inputs, runs text or image generation, and returns the CoT text plus generated outputs. |
| `HunyuanImage3Model` | `HunyuanImage3Model(config)` | Transformer backbone used by `HunyuanImage3ForCausalMM` when the `transformers` module is not skipped. |
| `HunyuanImage3TokenizerFast` | `HunyuanImage3TokenizerFast(*args, **kwargs)` | Fast tokenizer with conversation templates, special tokens, and mixed text / image section encoding. |
| `HunyuanImage3TokenizerFast.apply_chat_template` | `apply_chat_template(batch_prompt=None, batch_message_list=None, mode="gen_text", batch_gen_image_info=None, batch_cond_images=None, batch_system_prompt=None, batch_cot_text=None, max_length=None, bot_task="auto", image_base_size=None, sequence_template="pretrain", cfg_factor=1, add_assistant_prefix=None, drop_think=False)` | Returns a dict with `output` and `sections`. |
| `HunyuanImage3TokenizerFast.encode_general` | `encode_general(sections=None, max_token_length=None, add_eos='auto', use_text_mask=True, add_pad='auto', add_bos=True, drop_last='auto')` | Converts structured sections into `TokenizerEncodeOutput`. |
| `HunyuanImage3TokenizerFast.encode_sequence` | `encode_sequence(template, token_source, total_length=None, add_timestep_token=False, add_timestep_r_token=False, add_guidance_token=False, add_eos=True, add_pad=True, add_bos=True, drop_last='auto', add_image_shape_token=False)` | Assembles text and image token blocks into a single sequence. |
| `HunyuanImage3ImageProcessor` | `HunyuanImage3ImageProcessor(config)` | Converts images into VAE / ViT / conditioned-image metadata, ratio tokens, and postprocessed outputs. |
| `HunyuanImage3ImageProcessor.build_gen_image_info` | `build_gen_image_info(image_size, add_guidance_token=False, add_timestep_r_token=False)` | Creates `ImageInfo` for image generation. |
| `HunyuanImage3ImageProcessor.build_cond_images` | `build_cond_images(image_list=None, message_list=None, infer_align_image_size=False)` | Converts user-supplied images or message-list image sections into conditioned-image objects. |
| `HunyuanImage3ImageProcessor.postprocess_outputs` | `postprocess_outputs(outputs, batch_cond_images, infer_align_image_size=False)` | Optionally aligns output image size to the input conditioning ratio. |
| `HunyuanImage3Text2ImagePipeline` | `HunyuanImage3Text2ImagePipeline(model, scheduler, vae, progress_bar_config=None)` | Diffusion pipeline that owns the denoising loop and VAE decode. |
| `HunyuanImage3Text2ImagePipeline.__call__` | `__call__(batch_size, image_size, num_inference_steps=50, timesteps=None, sigmas=None, guidance_scale=7.5, meanflow=False, generator=None, latents=None, output_type="pil", return_dict=True, guidance_rescale=0.0, callback_on_step_end=None, callback_on_step_end_tensor_inputs=["latents"], model_kwargs=None, **kwargs)` | Runs the diffusion loop and returns `HunyuanImage3Text2ImagePipelineOutput(samples=...)`. |
| `FlowMatchDiscreteScheduler` | `FlowMatchDiscreteScheduler(num_train_timesteps=1000, shift=1.0, reverse=True, solver="euler", use_flux_shift=False, flux_base_shift=0.5, flux_max_shift=1.15, n_tokens=None)` | Scheduler used by the pipeline and model. Supported solvers: `euler`, `heun-2`, `midpoint-2`, `kutta-4`. |
| `cache_init` | `cache_init(cache_interval, max_order, num_steps=None, enable_first_enhance=False, first_enhance_steps=3, enable_tailing_enhance=False, tailing_enhance_steps=1, low_freqs_order=0, high_freqs_order=2)` | Builds Taylor-cache metadata for optional repeated-step reuse. |
| `TaylorCacheContainer` | `TaylorCacheContainer(max_order)` | Stores Taylor derivatives and temporary derivatives. |
| `CacheWithFreqsContainer` | `CacheWithFreqsContainer(max_order)` | Stores low/high-frequency derivative state for frequency-aware Taylor caching. |
| `get_system_prompt` | `get_system_prompt(sys_type, bot_task, system_prompt=None)` | Returns a built-in, dynamic, custom, or `None` system prompt. Prompt-policy details live in the sibling prompt-conditioning sub-skill. |

## Bridge types

- `ImageInfo` carries image size, token-length, and alignment metadata.
- `JointImageInfo` pairs VAE and ViT image info for `vae_vit` conditioning.
- `CondImage` wraps a conditioned image and the tokenizer section type to emit.
- `TokenizerEncodeOutput` contains tokens, masks, slices, and scatter indices.
- `HunyuanStaticCache` is the generation-time cache object built inside model input preparation.

## Signature notes

- `generate_image` uses `use_system_prompt` + `bot_task` to choose a prompt, then builds
  a mixed text / image input graph before dispatching to `generate`.
- `apply_chat_template` and `encode_general` are the safest entry points for understanding
  how text, image, and assistant sections are turned into token blocks.
- `FlowMatchDiscreteScheduler.step(...)` returns a `FlowMatchDiscreteSchedulerOutput`
  with `prev_sample`.
- `HunyuanImage3ForCausalMM.pipeline` is lazy; it is created only after the VAE,
  scheduler, and model are available.

## Safe local smoke

Run the bundled script to confirm the import surface and signature map:

```bash
python scripts/check_core_api_surface.py
```
