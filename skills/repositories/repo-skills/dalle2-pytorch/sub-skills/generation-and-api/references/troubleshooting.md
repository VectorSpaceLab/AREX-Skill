# Generation/API troubleshooting

Use this table when public `dalle2_pytorch` generation APIs, CLIP adapters, the tokenizer, inpainting, latent diffusion, or `dream` fail.

## Install and import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'dalle2_pytorch'` | Package is not installed in the active Python environment. | Install the public package: `python -m pip install dalle2-pytorch`. Then run `python scripts/check_dalle2_runtime.py --mode imports`. |
| `ModuleNotFoundError` for `torchvision`, `einops`, `kornia`, `open_clip`, `clip`, or `x_clip` | Partial or broken install. | Reinstall the package normally so `install_requires` resolves dependencies. Use `python -m pip check` to find conflicts. |
| `pkg_resources` warning or failure when importing CLI/CLIP packages | `clip-anytorch` still imports `pkg_resources`; very new setuptools versions may remove it. | A deprecation warning is harmless. If it is an error, install a setuptools version that still provides `pkg_resources`, or install the compatibility package recommended by your environment. |
| `torch` / `torchvision` binary mismatch | PyTorch and torchvision builds do not match CPU/CUDA variants. | Install a matched PyTorch/torchvision pair for the selected backend before installing or reinstalling `dalle2-pytorch`. |

## CLIP adapter and network/cache failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `OpenAIClipAdapter(...)` or `OpenClipAdapter(...)` hangs or tries to reach the internet | Adapter construction downloads pretrained weights through `clip-anytorch` or `open-clip-torch`. | Use a network-enabled environment, pre-populate the model cache, or avoid constructing adapters in no-network checks. The bundled `imports` and `tiny-forward` modes intentionally avoid adapters. |
| Latent dimension assertion involving CLIP and prior network | `DiffusionPriorNetwork.dim`, `DiffusionPrior.image_embed_dim`, and CLIP `dim_latent` do not match. | Recreate the prior network with the CLIP latent dimension used by the checkpoint, for example 768 for many `ViT-L/14` setups. |
| Image channel or image size assertion in a CLIP adapter | Input images do not match adapter expectations or are smaller than the CLIP input resolution. | Pass RGB images with channels matching `clip.image_channels` and size at least `clip.image_size`; the adapter resizes down when possible. |

## Prior and decoder guidance failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `the model was not trained with conditional dropout... cond_scale anything other than 1` | `cond_scale > 1` was requested for a model not trained with conditional dropout. | Use `cond_scale=1`, or use a checkpoint trained with nonzero conditional dropout. For prior, both text and image conditional dropout must support guidance. |
| Prior `.sample(...)` fails with missing `clip` / `embed_text` | The prior was constructed without a CLIP adapter. | Use `.forward(text_embed=..., image_embed=...)` for precomputed-embedding loss checks, or reconstruct the prior with the correct CLIP adapter for prompt sampling. |
| `text encodings must be present` | `condition_on_text_encodings=True` but no CLIP/text encodings were supplied. | Pass raw `text` with a CLIP adapter, pass `text_encodings`, or construct with `condition_on_text_encodings=False` only if that matches training. |
| Decoder `.sample(...)` says image embed must be present | Conditional decoder sampling requires a CLIP image embedding. | Pass `image_embed=...`, or use a decoder trained with `unconditional=True`. |
| Decoder reports wrong number of Unets for resolutions | `len(unets)` and `len(image_sizes)` differ. | Provide one `image_sizes` entry per Unet. Keep order low-to-high resolution. |
| Cascaded decoder output/resolution is unexpected | `image_sizes` are sorted by the decoder and used as cascade stage sizes. | Pass explicit low-to-high resolutions and checkpoint-compatible Unets. Do not assume tuple order can encode unsorted sizes. |
| Tiny custom Unet hits tensor token shape mismatch | `cond_dim`, `num_image_tokens`, and `num_time_tokens` produce incompatible token widths for a very small model. | For tiny CPU checks use the bundled script defaults (`dim=16`, `cond_dim=8`, one resolution stage). For real models, follow the checkpoint/config architecture. |

## Tokenization failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Input ... is too long for context length` | Package tokenizer prompt exceeds `context_length`, default 256. | Shorten the prompt or call `tokenizer.tokenize(..., truncate_text=True)` when truncation is acceptable. |
| Different token IDs than OpenAI CLIP examples | High-level `DALLE2.forward` uses `dalle2_pytorch.tokenizer.tokenizer`; some prior/data examples use `clip.tokenize`. | Use the tokenizer expected by the model's CLIP/training pipeline. Do not mix tokenizers for a trained checkpoint unless documented. |

## Inpainting failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Assertion says `inpaint_image` and `inpaint_mask` must both be given | Only one of the two inpainting arguments was passed. | Pass both arguments or neither. |
| Mask shape error or unexpected broadcasting | `inpaint_mask` was passed as `[B, 1, H, W]` or non-boolean data. | Pass a boolean tensor of shape `[B, H, W]`. The decoder internally adds the channel dimension. |
| Preserved and repainted regions are inverted | Mask semantics were misunderstood. | `True` means keep pixels from `inpaint_image`; `False` means synthesize/repaint. |
| Inpainting on cascaded/latent decoder gives odd results | Mask/image are resized per stage, and latent stages encode images before denoising. | Verify batch size and spatial dimensions, start with a single-stage pixel decoder, then re-enable cascade/latent stages once semantics are confirmed. |

## `dream` CLI failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `model not found at ...` | The `--model` file path does not exist. | Pass an existing trained DALLE2 checkpoint path. `dream --help` works without a checkpoint; generation does not. |
| Checkpoint key errors during `dream` | The file is not a `dream`-compatible DALLE2 model checkpoint. | The command expects `version`, `init_params.prior`, `init_params.decoder`, and `model_params`. Trainer checkpoints may need conversion or trainer-specific load logic. |
| Generated PNG is written somewhere unexpected | `dream` saves to the current working directory with a prompt-derived slug. | Run from the desired output directory or move the generated PNG afterward. |
| `--cond_scale 2.5` behaves unexpectedly in the shell | The Click option was declared with integer default and no explicit float type. | Prefer integer-looking CLI values for `dream`. Use Python API for precise floating-point `cond_scale`. |
| CPU generation is extremely slow or OOM | Real prior/decoder sampling is compute- and memory-heavy. | Use GPU for real generation. Reduce `sample_timesteps`, image sizes, batch size, and number of Unets only if compatible with the trained model/checkpoint. |

## Latent diffusion/VQGAN failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| VGG weights download during VQGAN creation | `VQGanVAE(use_vgg_and_gan=True)` constructs torchvision VGG16 if no `vgg` object is supplied. | Use cached weights, provide `vgg`, or set `use_vgg_and_gan=False` for architecture checks that do not train perceptual/GAN losses. |
| Latent Unet channel mismatch | The Unet/checkpoint was trained for RGB channels but is being used with a VQGAN encoded channel width, or vice versa. | Align the VAE tuple and Unet checkpoints exactly with the training architecture. |
| Interactive deletion prompt appears in VQGAN training | `VQGanVAETrainer` asks before clearing non-empty results folders. | Do not run VQGAN training by default. If explicitly training, choose an empty results folder or handle the prompt deliberately. |

## Escalation routes

- If the failure involves JSON config validation, trainer APIs, training CLI launchers, EMA/checkpoints during training, Accelerate/DeepSpeed, or evaluation metrics, route to `../training-and-configs/SKILL.md`.
- If the failure involves WebDataset shards, image/text embedding sidecars, `embedding-reader`, tracker save/load backends, W&B/HuggingFace/S3 credentials, or data splits, route to `../data-and-tracking/SKILL.md`.
