# Specialized workflow troubleshooting

Use this matrix for IC-LoRA, audio-only, Dub-It, HDR, sparse-track, mask, inpaint/outpaint, ingredients, and pixel spatial upscaler problems. Cross-cutting install/model/backend issues belong in the root troubleshooting reference; ordinary sampler/latent/decode failures belong in [core-generation](../../core-generation/SKILL.md); prompt/Gemma/API issues belong in [prompt-conditioning](../../prompt-conditioning/SKILL.md).

## IC-LoRA guide and model issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `LTXICLoRALoaderModelOnly` does not list the needed LoRA | LoRA file is not in ComfyUI's `models/loras` area or ComfyUI has not rescanned/restarted. | Place the safetensors in the loras model area, rescan or restart ComfyUI, and pick the family-specific LoRA. Do not substitute an unrelated LoRA family. |
| Loader returns `latent_downscale_factor=1.0` for a downscaled-reference LoRA | Safetensors metadata key `reference_downscale_factor` is missing, invalid, or unavailable. | If the workflow family documents a downscaled-reference variant, check the exact LoRA file. Otherwise keep `1.0` and size the guide normally. |
| `Latent spatial size WxH must be divisible by latent_downscale_factor F` | Target video latent width/height is not divisible by the LoRA's reference downscale factor. | Resize output dimensions so VAE latent spatial dimensions are divisible by `F`. Prefer connecting the loader's metadata output and using stricter width/height multiples such as 64 when uncertain. |
| `Conditioning frames exceed the length of the latent sequence` | Guide start frame plus guide latent length runs past the generated latent. | Shorten the guide, increase generated length, or move `frame_idx` earlier. For multi-frame guides, account for valid LTX frame indexing and negative-from-end behavior. |
| IC-LoRA has no visible effect | Returned conditioning/latent outputs were not propagated; wrong LoRA family; guide strength too low; guide image mismatched; prompt overwhelms guide. | Follow the guide node's returned positive, negative, and latent outputs into the sampler path. Verify LoRA family, guide resolution, `strength`, LoRA `strength_model`, and prompt pressure. |
| IC-LoRA overwhelms the prompt or copies the reference too strongly | Guide/model strength too high or advanced attention unmasked. | Lower `strength_model`, guide `strength`, or advanced `attention_strength`. Use `attention_mask` to localize influence. |
| Multiple references fight each other | All guides have full self-attention over the full frame. | Use `LTXAddVideoICLoRAGuideAdvanced` per guide and assign masks/attention strengths by region or importance. |
| Graph wires IC-LoRA guide after AV concat | Guide expects a video-only latent, not the final audio/video latent. | Move guide nodes before AV latent concatenation. Keep audio concat and audio freezing after IC-LoRA guide preparation. |

## Advanced guide attention and masks

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Attention mask has no effect | Mask is not connected to `LTXAddVideoICLoRAGuideAdvanced`, values are all zero/one unexpectedly, or graph uses the basic guide. | Use the advanced guide, inspect mask polarity/range, and ensure mask values are in `[0, 1]`. |
| Mask affects wrong area | Mask polarity or resize/crop alignment is wrong. | Invert upstream mask if necessary and resize it to match the reference guide image/video before feeding the guide. |
| Confusion between attention mask and inpaint mask | These masks affect different mechanisms. | Treat advanced `attention_mask` as guide self-attention weighting. Treat `LTXVPreprocessMasks`, `LTXVDilateVideoMask`, and `LTXVInpaintPreprocess` masks as latent/composite workflow masks unless deliberately reused. |

## Sparse track and motion-control issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `LTXVDrawTracks` outputs a blank guide | Empty, invalid, or incorrectly nested track JSON. | Run `../scripts/validate_sparse_tracks.py` on the JSON. Ensure it is a list of tracks, where each track is a list of `{x, y}` points. |
| Tracks draw outside the guide frame | Coordinates were authored for a different image size. | Validate with `--width` and `--height`, then rescale/recreate tracks against the actual reference image dimensions. |
| Motion appears too sparse or jerky | `points_to_sample` too low or track length does not match target temporal behavior. | Increase `points_to_sample` or redraw/subdivide splines. Check generated frame count and core sampler timing separately. |
| Motion-track workflow is slow | Too many tracks, too many sampled points, or very high guide resolution. | Reduce track count, reduce `points_to_sample`, or lower `LTXVDrawTracks` width/height. Native full workflow still requires CUDA/model assets. |
| Rendered colors look unusual | DrawTracks intentionally uses colored temporal trails and swaps color channel order to match training data. | Do not recolor tracks unless the chosen LoRA was trained for a different guide convention. |

## HDR and EXR issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| EXR save assertion says OpenCV does not support EXR by default | `OPENCV_IO_ENABLE_OPENEXR=1` was not set before ComfyUI startup / `cv2` import. | Stop ComfyUI, set the environment variable in the launch environment, restart, and run `../scripts/hdr_exr_preflight.py` before enabling `save_exr`. |
| EXR frames are not written but no assertion appears | `save_exr` is false, `opencv-python` is missing, or output directory permissions are invalid. | Enable `save_exr` only when needed, install optional OpenCV support, and choose a writable ComfyUI output-relative directory. |
| Tonemapped HDR preview looks clipped/flat | `tonemapped` is an SDR preview after exposure and Reinhard tonemap, not raw HDR. | Adjust `exposure`; inspect/use `hdr_linear` or saved EXR frames for grading. |
| HDR output looks like ordinary SDR | HDR IC-LoRA was not loaded, `LTXVHDRDecodePostprocess` was omitted/misplaced, or the wrong output was saved. | Confirm the HDR LoRA family, place postprocess after VAE decode, and use the correct `tonemapped` or `hdr_linear` output. |

## Text-to-audio and Dub-It issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| T2A sampler complains about missing video latent | The model still requires a video latent at input index 0. | Add `LTXVAudioOnlyEmptyVideoLatent` and concatenate it before the audio latent through the AV concat node. |
| T2A unexpectedly creates/uses video | `LTXVAudioOnlyModel` is missing or bypassed. | Patch the model with `LTXVAudioOnlyModel` before sampling. Remove the patch only for joint audio+video tasks. |
| Audio decode fails or produces silence | Wrong audio latent path, missing audio VAE, or sampler graph consumed the wrong latent. | Check audio latent creation, AV concat ordering, audio VAE decode, and core sampler settings. |
| Dub-It speaker identity is weak | Reference tokens were not attached to both conditioning branches or source audio is poor. | Use `LTXVSetAudioRefTokens` on positive and negative conditioning and verify downstream nodes consume the returned conditioning. Use a clean source audio segment. |
| Stage-2 Dub-It changes audio | Stage 2 uses a noised/new audio latent instead of frozen audio. | Feed `frozen_audio` from `LTXVSetAudioRefTokens` into the stage-2 AV concat. |
| Target dialogue is wrong language/text | Prompt/conditioning issue, not an audio utility node issue. | Route to [prompt-conditioning](../../prompt-conditioning/SKILL.md) and verify the target dialogue prompt and encoder path. |

## Mask, inpaint, outpaint, and blend issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Masks must be of shape (batch_size, H, W)` | Mask tensor has channel dimension or wrong rank. | Convert image-as-mask or squeeze channel dimension before `LTXVPreprocessMasks`. |
| `Masks batch size must have a multiple of ... masks + 1` | Mask sequence length does not match the VAE temporal grouping rule. | Use one first/conditioning mask plus a generated-frame count divisible by the VAE temporal scale factor. |
| Mask height/width multiple error | Mask dimensions are incompatible with VAE spatial downscale. | Resize masks and images to the same VAE-friendly multiple before preprocessing. |
| Green appears in the area that should stay original | Mask polarity is reversed. | Invert the mask before `LTXVInpaintPreprocess` or before dilation/preprocessing. |
| Green color leaks into output | Mask too wide/narrow, inadequate blend, or inpaint guide still visible after sampling. | Adjust dilation/growth/clamp values, use advanced attention mask, and blend with `LTXVLaplacianPyramidBlend`. |
| Laplacian blend raises frame count error | `image_a`, `image_b`, and `mask` have different frame counts and `trim_to_shortest` is false. | Enable `trim_to_shortest` or trim upstream tensors explicitly. |
| Laplacian blend raises spatial size error | Inputs/mask have different width/height. | Resize all three to the same spatial resolution before blending. |
| Import error references `kornia.geometry.transform.pyramid.pad` | Incompatible Kornia version. | Use the known compatible `kornia==0.7.1` for this custom node package. |

## Pixel spatial upscaler and ingredients issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Pixel upscaler output is not pixel-accurate | The pixel spatial upscaler LoRA is a creative generative upscaler, not an interpolating enhancer. | Set expectations: it synthesizes detail. Reduce prompt/guide strength if fidelity matters more than detail. |
| Upscaled output drifts too far from source | LoRA/guide strength, prompt, CFG, or steps allow too much creativity. | Lower creative pressure and verify the source clip is connected as the IC-LoRA guide. |
| Output keeps low-res artifacts | Reference is too dominant or target prompt lacks high-detail cues. | Increase creative detail in prompt and tune guide/LoRA strength; keep sampler choices in core-generation. |
| Ingredients appear but not where expected | Ingredients LoRA provides reference content, not exact layout constraints. | Add masks/advanced attention or more explicit prompt/layout conditioning; route prompt details to prompt-conditioning. |

## Boundary reminders

- Native specialized workflows require CUDA, ComfyUI, model weights, LoRA weights, audio/upscaler assets where applicable, and user media. Static checks cannot prove generation quality.
- Do not solve ordinary sampling/latent/decode questions here; route them to [core-generation](../../core-generation/SKILL.md).
- Do not solve Gemma/API prompt or conditioning cache questions here; route them to [prompt-conditioning](../../prompt-conditioning/SKILL.md).
- Do not solve Q8/STG/tricks questions here; route them to [advanced-control](../../advanced-control/SKILL.md).
