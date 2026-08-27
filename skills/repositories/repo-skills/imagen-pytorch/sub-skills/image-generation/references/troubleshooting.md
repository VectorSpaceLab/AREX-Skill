# Image Generation Troubleshooting

## Assertion and runtime fixes

| Symptom or message | Likely cause | Fix |
|---|---|---|
| `the images you pass in must be a square` | Training image tensor has `height != width`. | Resize/crop to square before calling `Imagen.forward` / `ElucidatedImagen.forward`. For image tasks use `(B, C, S, S)`. |
| `you must specify which unet you want trained` | Cascading model has multiple unets and training was called without `unet_number`. | Train one stage at a time: `imagen(images, ..., unet_number=1)`, then `unet_number=2`, etc. Use the trainer route for full loops. |
| `invalid text embedding dimension` | `text_embeds.shape[-1]` differs from wrapper `text_embed_dim`. | Set `Imagen(..., text_embed_dim=D)` / `ElucidatedImagen(..., text_embed_dim=D)` and construct unets with `text_embed_dim=D`, or regenerate embeddings with the expected dimension. |
| `text cannot be empty` | A `texts` list contains an empty string. | Remove empty captions or switch to precomputed embeddings and masks. |
| T5 download/cache surprise when using `texts` | Passing text strings invokes the package T5 tokenizer/encoder path. Some imports or defaults may also consult T5 configuration. | For no-network operation, prefer `condition_on_text=False` for unconditional tasks or pass precomputed `text_embeds`/`text_masks` with explicit `text_embed_dim`. Route embedding preparation to `data-and-text-conditioning`. |
| `text or text encodings must be passed` | Wrapper has `condition_on_text=True`, but no `texts` or `text_embeds` were supplied. | Pass `text_embeds`/`text_masks`, pass non-empty `texts`, or construct with `condition_on_text=False` for unconditional use. |
| `decoder specified not to be conditioned on text` / `imagen specified not to be conditioned on text, yet it is presented` | Unconditional wrapper received `text_embeds` or text-related inputs. | Remove text inputs, or rebuild the wrapper with `condition_on_text=True` and matching text dimensions. |
| `null unet cannot and should not be trained` | Training targeted a `NullUnet` placeholder. | For super-resolution-only branches, train the real upsampler stage, usually `unet_number=2`. |
| `one cannot sample from null / placeholder unets` / `cannot sample from null unet` | Sampling entered a `NullUnet` stage. | Skip placeholder stages with `start_at_unet_number=2` and pass `start_image_or_video` of the previous stage size. |
| `starting image or video must be supplied if only doing upscaling` | `start_at_unet_number > 1` was set without low-resolution input. | Pass `start_image_or_video` shaped `(B, C, previous_size, previous_size)` for image upscaling. |
| `inpaint images and masks must be both passed in` | Only one of `inpaint_images` or `inpaint_masks` was supplied. | Supply both. Images: `(B, C, H, W)`; masks: `(B, H, W)` bool-like. |
| `number of inpainting images must be equal...` | Inpainting batch does not match `batch_size` or text embedding batch. | Align `inpaint_images.shape[0]`, `inpaint_masks.shape[0]`, `batch_size`, and `text_embeds.shape[0]`. |
| `you did not supply the correct number of u-nets` | `len(unets)` differs from `len(image_sizes)`. | Provide one `image_sizes` entry for every cascade stage, including `NullUnet` placeholders. |
| Low-resolution conditioning assertion on construction | A manually configured unet cascade has an invalid low-res condition pattern. | Usually leave `lowres_cond` unset; the wrapper casts first stage to false and later stages to true. If constructing custom unets, ensure only upsamplers are low-res-conditioned. |
| `images tensor needs to be floats` | Images are integer tensors or unsupported dtype. | Use float tensors in `[0, 1]`. `Imagen` can cast `uint8` to float and accepts float/half; `ElucidatedImagen` requires `torch.float`. |
| `the number of channels on the conditioning image...` | `cond_images` channels do not match `cond_images_channels`. | Rebuild the unet with the intended `cond_images_channels`, or pass conditioning images with exactly that channel count. |
| `imagen was not trained with conditional dropout... cond_scale` | `cond_scale != 1` but `cond_drop_prob` was `0`, so classifier-free guidance was not enabled during training. | Train conditional models with `cond_drop_prob > 0`, or sample with `cond_scale=1.0`. |
| Very slow or out-of-memory on CPU | Diffusion sampling/training is compute-heavy; predefined unets are CUDA-scale. | Use the tiny smoke helper on CPU only for API checks. For real training/generation, use CUDA, smaller batches, `max_batch_size` via trainer, fewer sample steps for debugging, and `use_one_unet_in_gpu=True` during sampling. |
| `return_pil_images=True` fails for video | Automatic video-to-file/PIL conversion is not supported in these image wrappers. | Use image-only models here. Route video tensors and saving strategy to `video-and-inpainting`. |

## Decision checks before coding

- Is the task unconditional? Set `condition_on_text=False`, omit all text inputs, and keep `cond_scale=1`.
- Is the task text-conditioned but offline? Use precomputed `text_embeds` and explicit `text_embed_dim`; do not pass `texts`.
- Is there more than one unet? Pass `unet_number` during every training loss call.
- Is a `NullUnet` present? Skip it for both training and sampling.
- Is the requested output PIL? Confirm the model is image-only, not `Unet3D`/video.
- Is this a quality claim? Do not infer quality from a smoke check; it only proves that construction and tensor calls execute.

