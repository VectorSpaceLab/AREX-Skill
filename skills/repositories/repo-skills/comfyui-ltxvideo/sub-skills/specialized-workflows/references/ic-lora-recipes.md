# IC-LoRA specialized recipes

This reference distills the IC-LoRA workflow families and node behavior needed to build specialized ComfyUI-LTXVideo graphs without reopening the source checkout or original workflow JSON files.

## IC-LoRA node roles

| Node | Role | Key outputs and constraints |
| --- | --- | --- |
| `LTXICLoRALoaderModelOnly` | Load an IC-LoRA into an existing LTX model without touching a CLIP/text encoder. | Returns the patched `MODEL` and a `latent_downscale_factor` float extracted from safetensors metadata key `reference_downscale_factor`; if metadata is missing or invalid, the node falls back to `1.0` and logs a warning. |
| `LTXAddVideoICLoRAGuide` | Encode a reference image/video guide and append guide tokens/latent conditioning. | Inputs are positive/negative conditioning, VAE, a video-only latent, reference image/video frames, frame index, strength, `latent_downscale_factor`, crop mode, and optional tiled VAE encode settings. Outputs updated positive, negative, and latent; all three must be routed downstream. |
| `LTXAddVideoICLoRAGuideAdvanced` | Same guide operation plus per-guide self-attention control. | Adds `attention_strength` and optional `attention_mask`; use when several references compete or when a guide should affect only a spatial region. |
| `LTXVSetAudioRefTokens` | Add speaker-reference audio tokens to conditioning for audio/video IC-LoRA workflows. | Described in [audio/HDR/motion](audio-hdr-motion.md); useful for Dub-It, V2V IC-LoRA, pixel upscaler, inpaint, and outpaint families with audio. |

## Generic IC-LoRA graph pattern

1. Build the normal base LTX graph first: model checkpoint, prompt conditioning, video latent, audio latent if needed, sampler, VAE decode, and output nodes. Use [core-generation](../../core-generation/SKILL.md) for sampler/latent/decode details and [prompt-conditioning](../../prompt-conditioning/SKILL.md) for text or Gemma setup.
2. Insert `LTXICLoRALoaderModelOnly` on the model path before the sampler. Select the LoRA family that matches the task and place the safetensors under ComfyUI's `models/loras` area.
3. Prepare the guide image/video at the intended guide resolution. Resize to model-friendly multiples before guide encoding; common families use dimensions that are multiples of the VAE spatial scale, and downscaled-reference LoRAs may need stricter divisibility.
4. Place `LTXAddVideoICLoRAGuide` or `LTXAddVideoICLoRAGuideAdvanced` on the video-only latent and positive/negative conditioning path before final AV latent concatenation. Connect the loader's `latent_downscale_factor` output into the guide when available.
5. Route the guide node's returned positive, negative, and latent into the downstream sampler/AV concat path. If the graph is two-stage, repeat guide placement at the appropriate stage resolution rather than reusing stage-1 latent outputs blindly.
6. Keep prompt/negative prompt and sampler parameters synchronized with the specialized objective: an IC-LoRA guide supplies visual/audio structure, but prompts still control target content and style.

## Guide placement details

- Guide nodes expect a **5D video latent** with shape semantics like batch, channels, frames, latent height, latent width. Do not feed a final concatenated audio/video latent into an IC-LoRA guide.
- For multi-frame guides, the basic guide normalizes frame placement through the LTX guide indexing logic. Non-initial multi-frame guides have a causal-fix prefix internally; if the guide would extend beyond the latent sequence, the node raises `Conditioning frames exceed the length of the latent sequence.`
- The basic guide tooltip documents that multi-frame `frame_idx` values are rounded to the nearest valid 1-modulo-8 placement and negative values count from the end. Plan tracks/reference clips so the chosen start frame plus guide length fits the generated latent.
- `strength` controls how much guide conditioning is appended through the LTX guide mechanism. It is not the same as LoRA model strength (`strength_model`) and not the same as advanced `attention_strength`.
- `crop="center"` crops while resizing to fit; `crop="disabled"` stretches. Use center crop when preserving aspect is more important than preserving the entire frame.
- `use_tiled_encode`, `tile_size`, and `tile_overlap` reduce VAE encode memory for large guides. They do not remove the need for model assets/CUDA during generation.

## `latent_downscale_factor` and divisibility

IC-LoRA LoRAs may operate on downscaled reference latents. `LTXICLoRALoaderModelOnly` exposes the model metadata value so guide nodes can match the trained reference grid.

When `latent_downscale_factor > 1`, guide execution requires the target latent width and height to be divisible by that factor. If this fails, the node raises a message of the form:

```text
Latent spatial size WxH must be divisible by latent_downscale_factor F
```

Fix the graph by resizing the generated video dimensions so the VAE latent spatial dimensions are divisible by `F`. In practice this means choosing output width/height that are divisible by the VAE spatial downscale factors multiplied by `F`; if unsure, resize to a stricter multiple such as 64 before guide encoding and keep the loader's metadata output connected.

## Advanced attention strength and masks

Use `LTXAddVideoICLoRAGuideAdvanced` when the guide's self-attention influence needs local or per-reference control.

- `attention_strength` is a scalar in `[0, 1]`: `1.0` is full reference attention, `0.0` ignores this guide's self-attention influence.
- `attention_mask` accepts a spatial mask in pixel space. The implementation normalizes `(H, W)` or `(F, H, W)` masks to an internal `(1, 1, F, H, W)` form.
- The effective attention influence is `attention_strength` multiplied by the mask values.
- This mask controls guide attention metadata; it is separate from latent noise masks, inpaint masks, and `LTXVPreprocessMasks` outputs unless the graph deliberately wires the same user mask into several places.
- Advanced guide is especially useful for inpaint/outpaint and multi-reference graphs where the IC-LoRA should influence only a face/object/border region.

## Workflow family chooser

| Family | Distilled intent | IC-LoRA recipe |
| --- | --- | --- |
| Union control | One LoRA supports multiple control signals such as depth, edge/canny, and pose-like control maps. | Preprocess the user's image/video into the desired control map(s), resize to the guide resolution, load the union-control LoRA, and add it as an IC-LoRA guide before sampling. Use the same core sampler recipe as a normal I2V/V2V graph. |
| Motion track | Move regions according to sparse user-drawn tracks over a reference image. | Use `LTXVSparseTrackEditor` to generate track JSON, validate it, render it with `LTXVDrawTracks`, then feed the rendered track image/video into the motion-track IC-LoRA guide. |
| HDR | Generate LogC3-compressed HDR frames and decode them after VAE decode. | Load the HDR IC-LoRA, guide with the HDR reference/control image/video, sample normally, VAE decode, then run `LTXVHDRDecodePostprocess` for tonemapped SDR preview and linear HDR output. |
| Dub-It | Rephrase or translate speech in a source video while preserving speaker identity and matching lips/audio. | Load the Dub-It LoRA, use source video frames as guide/reference, encode source audio, attach `LTXVSetAudioRefTokens` to conditioning, and in two-stage graphs freeze the audio latent during stage 2. |
| Pixel spatial upscaler | Creatively re-render a low-resolution reference clip at 2x or 4x with synthesized detail. | Choose the x2 or x4 pixel spatial upscaler LoRA, feed a resized low-res reference as guide, generate the higher-resolution target, and tune LoRA/guide strength for fidelity versus creative detail. This is not a pixel-exact upscaler. |
| Ingredients | Use a reference ingredient/object image as a controllable source of visual content. | Load the ingredients LoRA, resize the ingredient reference, add it as a guide, and let the prompt specify how the ingredient should appear in the output scene. |
| Inpaint/outpaint | Fill masked areas or extend canvas borders using in-outpainting LoRA guidance. | Use mask and green-composite preparation from [masks/inpaint/outpaint/upscale](masks-inpaint-outpaint-upscale.md), then use advanced guide if the mask should localize attention. Use Laplacian blending for final seams. |
| V2V IC-LoRA detail/edit | Transform a source clip with an IC-LoRA such as instant-shave/colorization/deblur/decompression/water/detailer. | Use the source video as the reference guide, optionally preserve audio with `LTXVSetAudioRefTokens`, and route ordinary V2V sampling details to [core-generation](../../core-generation/SKILL.md). |
| Text-to-audio | Generate audio only from text. | This is not an IC-LoRA guide recipe; use `LTXVAudioOnlyModel` and `LTXVAudioOnlyEmptyVideoLatent` in [audio/HDR/motion](audio-hdr-motion.md). |

## Model asset notes

Specialized families use LoRA safetensors selected by task: union control, motion track, HDR, Dub-It, ingredients, in-outpainting, pixel spatial upscaler x2/x4, and other edit/detail LoRAs. Keep them in ComfyUI's `models/loras` model area and restart/rescan if the loader combo does not list them. Do not promise first-use downloads or native execution unless the user's ComfyUI setup already has the required checkpoint, text encoder, audio VAE, LoRA, and upscaler assets.
