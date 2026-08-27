# Supported Model Families and Layouts

ComfyUI detects many model families from checkpoint or standalone diffusion model state dictionaries, then chooses matching model, latent, text encoder, and VAE handling. This reference helps agents route files into the right folder categories and explain compatibility without downloading anything.

## Broad Capability Surface

The repository evidence shows support for image, image-editing, video, audio, 3D, detection, depth, and segmentation-oriented model families. Public feature notes include Stable Diffusion variants, SDXL, SD3/3.5, Stable Cascade, PixArt, AuraFlow, Hunyuan, Flux, Lumina, HiDream, Qwen Image, Wan, LTX-Video, Mochi, Stable Audio, ACE Step, Hunyuan3D, and others. The source `supported_models` registry includes many more specialized classes.

Treat this list as model-family support, not as a promise that weights are installed or that the user's torch/backend can run every family.

## Major Families in Current Source

| Family area | Examples from source registry | Common path implications |
| --- | --- | --- |
| Stable Diffusion checkpoints | `SD15`, `SD20`, `SDXL`, `SDXLRefiner`, SDXL derivatives, inpaint/instruct-pix2pix variants | All-in-one files usually go in `checkpoints`; separate configs may use `configs`. |
| Stable Cascade / Zero123 / SV3D | `Stable_Cascade_C`, `Stable_Cascade_B`, `Stable_Zero123`, `SV3D_u`, `SV3D_p` | Often require specific stage/model pieces and sometimes CLIP vision files. |
| SD3 and Flux-style DiT | `SD3`, `Flux`, `FluxInpaint`, `FluxSchnell`, `Flux2`, `Chroma`, `ChromaRadiance`, `Lens` | Split workflows commonly use `diffusion_models`, `text_encoders`, and `vae` rather than only `checkpoints`. |
| PixArt / Aura / Hunyuan image | `PixArtAlpha`, `PixArtSigma`, `AuraFlow`, `HunyuanDiT`, `HunyuanImage21` | Text encoders are often standalone T5/LLaMA/Qwen-style files in `text_encoders`. |
| Qwen / HiDream / Z Image / Omnigen / Ideogram | `QwenImage`, `HiDream`, `HiDreamO1`, `ZImage`, `Omnigen2`, `Ideogram4`, `Boogu`, `ErnieImage`, `LongCatImage` | Expect newer split-model layouts and backend-sensitive dtype/memory choices. |
| Video | `HunyuanVideo`, `HunyuanVideo15`, `WAN21_*`, `WAN22_*`, `LTXV`, `LTXAV`, `GenmoMochi`, `Cosmos*`, `CogVideoX_*`, `SVD_img2vid` | Large VRAM and multiple supporting files are common; route graph shape questions to `../../workflow-execution/SKILL.md`. |
| Audio | `StableAudio`, `StableAudio3`, `ACEStep`, `ACEStep15` | Audio encoders and audio model files may use `audio_encoders` and family-specific loaders. |
| 3D / vision helpers | `Hunyuan3Dv2`, `TripoSplat`, `RT_DETR_v4`, `DepthAnything3`, `SAM3` | Use helper categories such as `detection`, `geometry_estimation`, or family-specific folders when loader nodes expect them. |

## All-in-One vs Split Layouts

All-in-one checkpoint workflow:

- Put checkpoint files in `models/checkpoints` or an extra `checkpoints` path.
- Loader nodes select the checkpoint filename from that category.
- The checkpoint may include model, CLIP/text encoder, and VAE pieces; ComfyUI guesses config from the state dict.

Split-model workflow:

- Put standalone diffusion model files in `diffusion_models`.
- Put text encoders in `text_encoders`.
- Put VAEs in `vae`.
- Put CLIP vision models in `clip_vision` when required.
- Put LoRAs in `loras`; they patch compatible base model/text encoder keys at load time.

Diffusers folder workflow:

- Put folder-based Diffusers layouts in `diffusers`.
- The category accepts folders rather than checkpoint extensions.

## Detection and Loading Notes

ComfyUI's loading path detects model type from keys and metadata in the model state dictionary. A failure such as `ERROR UNSUPPORTED DIFFUSION MODEL` usually means one of these is true:

- The file is in the wrong category for the loader node.
- The file is not the model component the node expects, such as using a text encoder file as a diffusion model.
- The model family or exact checkpoint format is not recognized by this ComfyUI version.
- A quantized checkpoint uses metadata/layouts not supported by this build.
- The model requires optional code or dependencies not installed in the environment.

## Quantization Compatibility

ComfyUI supports quantized tensor concepts through `QuantizedTensor`, layout handlers, and mixed-precision operation selection. Compatible quantized checkpoints are standard checkpoint containers with quantized weights, scaling parameters, and `_quantization_metadata` that describes layer formats.

Practical guidance:

- Do not convert or download models automatically. Explain expected format and ask the user to provide compatible files.
- FP8 flags such as `--fp8_e4m3fn-unet`, `--fp8_e5m2-unet`, `--fp8_e8m0fnu-unet`, and text-encoder fp8 flags depend on torch dtype support and backend capability.
- If a quantized model fails on one backend, retrying with fp16/fp32 flags or a non-quantized checkpoint is often a better diagnostic than changing paths.
- Mixed-precision checkpoints may keep sensitive layers in higher precision and quantize compute-heavy layers; not every layer must be quantized.
- Unsupported quantized operations can fall back to dequantization paths when implemented, but this may reduce speed or increase memory.

## Model Folder Advice by Request

- “My checkpoint is missing”: verify the file exists in `checkpoints`, has a supported extension, and the graph references the same filename.
- “My LoRA does not show”: verify `loras`, not `checkpoints`; refresh/restart and confirm file extension.
- “Flux/SD3/Qwen/Wan needs multiple files”: use split categories (`diffusion_models`, `text_encoders`, `vae`, sometimes `clip_vision`) and check the workflow's loader nodes.
- “ControlNet/T2I adapter missing”: use `controlnet`; the default category already includes both `models/controlnet` and `models/t2i_adapter`.
- “Upscaler missing”: use `upscale_models`.
- “Embeddings/textual inversion missing”: use `embeddings`.
- “Custom node model folder missing”: custom nodes may register their own categories; validate known categories but allow intentional custom categories when the node documents them.
