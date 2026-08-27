# API and Config Reference

This reference is for API inspection and safe planning. Do not load model
weights just to answer signature or config questions.

## Verified import and signature facts

The following source modules imported in a CUDA-capable Python 3.11 inspection
environment after installing the core SUPIR dependency stack:

- `SUPIR.util`
- `SUPIR.models.SUPIR_model`
- `SUPIR.modules.SUPIR_v0`
- `sgm.util`
- `sgm.modules.diffusionmodules.sampling`
- `llava.llava_agent`
- `SUPIR.utils.face_restoration_helper`

`SUPIR.modules.SUPIR_v0` can print `no module 'xformers'. Processing without...`
when xformers is not installed. Treat that as a warning, not an import failure.

## `SUPIR.util` helpers

| API | Signature | Behavior and gotchas |
| --- | --- | --- |
| `create_model` | `(config_path)` | Loads an OmegaConf config, instantiates `config.model`, moves it to CPU, and prints the config path. Does not load Q/F SUPIR checkpoints. |
| `create_SUPIR_model` | `(config_path, SUPIR_sign=None, load_default_setting=False)` | Loads config, creates model, loads `SDXL_CKPT`, optional `SUPIR_CKPT`, then loads Q or F checkpoint when requested. Returns `(model, default_setting)` only when requested. |
| `load_QF_ckpt` | `(config_path)` | Loads `SUPIR_CKPT_F` and `SUPIR_CKPT_Q` into CPU state dicts for UI model switching. |
| `PIL2Tensor` | `(img, upsacle=1, min_size=1024, fix_resize=None)` | Converts PIL RGB-like image to `torch.float32` `[C,H,W]` tensor in `[-1,1]`; rounds model size to multiples of 64 and returns original target `h0,w0`. Parameter is misspelled `upsacle` in source. |
| `Tensor2PIL` | `(x, h0, w0)` | Converts `[C,H,W]` tensor in `[-1,1]` back to PIL after bicubic resize to original target size. |
| `HWC3` | `(x)` | Ensures a `uint8` HWC array has exactly 3 channels; handles grayscale and alpha composition. |
| `upscale_image` | `(input_image, upscale, min_size=None, unit_resolution=64)` | Resizes a uint8 image with LANCZOS for upscale and AREA otherwise; rounds to a unit resolution. |
| `fix_resize` | `(input_image, size=512, unit_resolution=64)` | Resizes so the shortest side reaches `size`, rounded to multiples of the unit resolution. |
| `Numpy2Tensor` | `(img)` | Converts `[H,W,C]` array in `[0,255]` to RGB tensor in `[-1,1]`. |
| `Tensor2Numpy` | `(x, h0=None, w0=None)` | Converts tensor back to HWC uint8, optionally resizing first. |
| `convert_dtype` | `(dtype_str)` | Supports `fp32`, `fp16`, and `bf16`; raises for any other string. |

## `SUPIRModel` methods

| Method | Signature | Behavior and gotchas |
| --- | --- | --- |
| Constructor | `(self, control_stage_config, ae_dtype='fp32', diffusion_dtype='fp32', p_p='', n_p='', *args, **kwargs)` | Extends the bundled SGM `DiffusionEngine`, loads the control model, copies denoise encoder, records sampler config and prompt suffixes. AE `fp16` raises `RuntimeError('fp16 cause NaN in AE')`. |
| `batchify_denoise` | `(self, x, is_stage1=False)` | Expects batch tensor `[N,3,H,W]` in `[-1,1]`; encodes via denoise encoder and decodes back to image tensor. |
| `batchify_sample` | `(self, x, p, p_p='default', n_p='default', num_steps=100, restoration_scale=4.0, s_churn=0, s_noise=1.003, cfg_scale=4.0, seed=-1, num_samples=1, control_scale=1, color_fix_type='None', use_linear_CFG=False, use_linear_control_scale=False, cfg_scale_start=1.0, control_scale_start=0.0, **kwargs)` | Main restoration call. Requires `len(x)==len(p)`. `color_fix_type` must be `Wavelet`, `AdaIn`, or `None`. `num_samples>1` requires one input image. Negative seed picks a random seed. Applies Wavelet or AdaIn color fix after decoding. |
| `init_tile_vae` | `(self, encoder_tile_size=512, decoder_tile_size=64)` | Replaces VAE encoder/decoder forwards with tiled hooks for memory-limited runs. |
| `prepare_condition` | `(self, _z, p, p_p, n_p, N)` | Builds SDXL-like conditioning with fixed 1024 size tuples. If `p[0]` is a list, local-prompt conditioning is active and batch size must be one. |

## `LLavaAgent`

| API | Signature | Notes |
| --- | --- | --- |
| Constructor | `(self, model_path, device='cuda', conv_mode='vicuna_v1', load_8bit=False, load_4bit=False)` | Expands model path, derives model name, calls `load_pretrained_model`, prepares a default image-question prompt with image tokens. |
| `gen_image_caption` | `(self, imgs, temperature=0.2, top_p=0.7, num_beams=1, qs=None)` | Accepts a list of PIL images, preprocesses them through LLaVA's vision tower, generates up to 512 new tokens, strips separator text, and returns one caption per input. |

LLaVA import depends on a compatible Transformers version. A newer stack that
already registers the `llava` model type can fail before any model is loaded.

## Config loading patterns

Use this order when writing or reviewing code:

1. Validate checkpoint/config paths with the root checkpoint validator.
2. Import APIs and inspect signatures with the API probe.
3. Choose dtype values: use `bf16` or `fp32` for AE, usually `fp16` for diffusion.
4. Construct the model with `create_SUPIR_model(config_path, SUPIR_sign='Q'|'F')`.
5. Move the model to the selected CUDA device.
6. Run denoise/caption/sample stages only after input tensors are normalized to `[-1,1]`.

## API-specific troubleshooting

- If `PIL2Tensor` returns unexpected target sizes, remember it rounds working
  dimensions to multiples of 64 while returning pre-rounded `h0,w0` for final
  output restoration.
- If `batchify_sample` asserts, check prompt batch length and `num_samples`.
- If `prepare_condition` asserts with a local prompt list, ensure there is only
  one input image in the batch.
- If LLaVA captioning fails but SUPIR imports work, disable LLaVA and provide a
  manual prompt to isolate the caption model.
