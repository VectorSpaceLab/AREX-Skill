# Pipeline Internals

## Purpose

Use this reference when you need to explain or modify the internal identity-conditioning path. It is the source of truth for the sub-skill, not the end-user command recipe.

## Verified API snapshot

Installed-package signature inspection confirmed:

```text
InfUFluxPipeline.__init__(self, base_model_path, infu_model_path, insightface_root_path='./', image_proj_num_tokens=8, infu_flux_version='v1.0', model_version='aes_stage2', quantize_8bit=False, cpu_offload=False)
InfUFluxPipeline.__call__(self, id_image: PIL.Image.Image, prompt: str, control_image: Optional[PIL.Image.Image] = None, width=864, height=1152, seed=42, guidance_scale=3.5, num_steps=30, infusenet_conditioning_scale=1.0, infusenet_guidance_start=0.0, infusenet_guidance_end=1.0, cpu_offload=False)
FluxInfuseNetPipeline.__call__(self, prompt: Union[str, List[str]] = None, prompt_2: Union[List[str], str, NoneType] = None, height: Optional[int] = None, width: Optional[int] = None, num_inference_steps: int = 28, timesteps: List[int] = None, guidance_scale: float = 3.5, controlnet_guidance_scale: float = 1.0, control_guidance_start: Union[float, List[float]] = 0.0, control_guidance_end: Union[float, List[float]] = 1.0, control_image: Union[PIL.Image.Image, numpy.ndarray, torch.Tensor, List[PIL.Image.Image], List[numpy.ndarray], List[torch.Tensor]] = None, control_mode: Union[int, List[int], NoneType] = None, controlnet_conditioning_scale: Union[float, List[float]] = 1.0, num_images_per_prompt: Optional[int] = 1, generator: Union[torch._C.Generator, List[torch._C.Generator], NoneType] = None, latents: Optional[torch.FloatTensor] = None, prompt_embeds: Optional[torch.FloatTensor] = None, pooled_prompt_embeds: Optional[torch.FloatTensor] = None, output_type: Optional[str] = 'pil', return_dict: bool = True, joint_attention_kwargs: Optional[Dict[str, Any]] = None, callback_on_step_end: Optional[Callable[[int, int, Dict], NoneType]] = None, callback_on_step_end_tensor_inputs: List[str] = ['latents'], max_sequence_length: int = 512, controlnet_prompt_embeds: Optional[torch.FloatTensor] = None, true_guidance_scale: float = 1.0, negative_prompt: Union[List[str], str, NoneType] = None, negative_prompt_2: Union[List[str], str, NoneType] = None, negative_prompt_embeds: Optional[torch.FloatTensor] = None, negative_pooled_prompt_embeds: Optional[torch.FloatTensor] = None, cpu_offload: bool = False)
Resampler.__init__(self, dim=1024, depth=8, dim_head=64, heads=16, num_queries=8, embedding_dim=768, output_dim=1024, ff_mult=4)
retrieve_timesteps(scheduler, num_inference_steps: Optional[int] = None, device: Union[str, torch.device, NoneType] = None, timesteps: Optional[List[int]] = None, sigmas: Optional[List[float]] = None, **kwargs)
calculate_shift(image_seq_len, base_seq_len: int = 256, max_seq_len: int = 4096, base_shift: float = 0.5, max_shift: float = 1.16)
```

## Core flow

1. `InfUFluxPipeline.__init__` loads the InfuseNet controlnet from `infu_model_path/InfuseNetModel` in `torch.bfloat16`, then loads the FLUX transformer and `text_encoder_2` from `base_model_path` in the same dtype.
2. If `quantize_8bit` is enabled, the source quantizes the InfuseNet module, the transformer, and `text_encoder_2` with `optimum.quanto` before the Diffusers pipeline is assembled, then freezes the quantized modules.
3. The identity projection path builds a `Resampler` with `dim=1280`, `depth=4`, `dim_head=64`, `heads=20`, `num_queries=image_proj_num_tokens`, `embedding_dim=512`, `output_dim=4096`, and `ff_mult=4`.
4. `image_proj_model.bin` is loaded with `torch.load(..., weights_only=True)` and the code expects a top-level `image_proj` entry whose tensor shapes match the current `Resampler` configuration.
5. The face path prepares three `FaceAnalysis` detectors (`640`, `320`, `160`) with `providers=['CUDAExecutionProvider', 'CPUExecutionProvider']` and an ArcFace recognition model on CUDA.
6. `InfUFluxPipeline.__call__` converts the identity image to BGR, tries face detection from largest to smallest detector, rejects empty detections, selects the largest face by bounding-box area, extracts a 512-d ArcFace vector, reshapes it to `[1, 1, 512]`, projects it, and sends the result as `controlnet_prompt_embeds`.
7. The control image is resized and padded to the target canvas before keypoints are drawn. If no control image is supplied, a black image is used instead.
8. The outer call forwards `infusenet_conditioning_scale` to `controlnet_conditioning_scale`, forwards `infusenet_guidance_start` and `infusenet_guidance_end` to `control_guidance_start` and `control_guidance_end`, and always keeps `controlnet_guidance_scale=1.0`.
9. `FluxInfuseNetPipeline.__call__` is the Diffusers controlnet wrapper. It adds `controlnet_prompt_embeds`, `true_guidance_scale`, and `cpu_offload` on top of the usual FluxControlNet inputs.

## Denoising and offload behavior

- `retrieve_timesteps` supports either custom `timesteps` or custom `sigmas`, never both, and it verifies that `scheduler.set_timesteps` accepts the requested keyword before calling it.
- `calculate_shift` linearly interpolates the scheduler shift as the latent sequence length moves between the base and max sequence lengths.
- When `cpu_offload=True`, the pipeline stages VAE, transformer, controlnet, and the text encoders between CPU and CUDA during different phases of inference. This is an offload strategy, not a CPU-only execution mode.
- The identity front-end still moves `arcface_model` and `image_proj_model` onto CUDA for the projection step and then returns them to CPU after use.
- The `controlnet_blocks_repeat` branch depends on whether the controlnet exposes `input_hint_block`; that branch is one of the first places to inspect if a Diffusers upgrade changes the controlnet contract.

## Drift and customization watchpoints

- If the installed signature of any helper in the snapshot differs from the code above, treat it as API drift and compare the source plus the bundled signature helper before editing runtime code.
- `controlnet_guidance_scale` is not the same as `controlnet_conditioning_scale`; the outer wrapper fixes the former at `1.0` and exposes the latter as the InfiniteYou-specific guidance knob.
- Any change to the face encoder output dimension must be mirrored in the `Resampler` input width and checkpoint layout.
- Any change to `image_proj_num_tokens` must be matched by a checkpoint whose `image_proj` weights were trained for the same query count.
- The source hard-codes CUDA moves and bf16 loads in several places. If you need CPU-only execution or fp16/fp32 support, that requires code changes rather than a flag change.

## Next checks when editing internals

1. Run the bundled signature helper and compare its output with this snapshot.
2. Confirm the local model tree contains the expected `InfuseNetModel`, `image_proj_model.bin`, and base FLUX subfolders before changing checkpoint or offload logic.
3. Re-check the troubleshooting guide before touching face detection, adapter loading, or scheduler code.
