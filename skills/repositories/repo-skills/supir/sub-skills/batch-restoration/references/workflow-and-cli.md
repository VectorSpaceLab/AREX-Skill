# Batch Workflow and CLI Reference

This reference distills the repo's folder-based restoration workflow. Use the
bundled wrapper for dry-run validation before any expensive model loading.

## Source workflow shape

The batch workflow performs these stages for every image in the input folder:

1. Select CUDA devices: SUPIR on `cuda:0`; LLaVA on `cuda:1` when two GPUs are
   visible, otherwise same GPU; abort if no CUDA.
2. Load the SUPIR model from the default YAML and the selected Q/F checkpoint.
3. Optionally enable half parameters and tiled VAE hooks.
4. Optionally load `LLavaAgent` for caption generation.
5. Convert the input image to a model tensor at the requested upscale/minimum
   size.
6. Make a 512-side preview, run stage1 denoise, and caption that preview with
   LLaVA unless captioning is disabled.
7. Run `batchify_sample` with prompt suffixes, sampler settings, seed, CFG,
   stage control, and color-fix options.
8. Save each sample as `<input_stem>_<i>.png` in the output directory.

## Core flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--img_dir` | required | Directory of input images. Validate it before running long jobs. |
| `--save_dir` | required | Created if missing. Outputs are PNGs named from input stems and sample indices. |
| `--upscale` | `1` | Input resolution multiplier before minimum-size adjustment. |
| `--SUPIR_sign` | `Q` | `Q` for default/general quality; `F` for light-degradation fidelity. |
| `--seed` | `1234` | Use `-1` only when random seed behavior is intentional. |
| `--min_size` | `1024` | Short side is raised to at least this before rounding to a multiple of 64. |
| `--edm_steps` | `50` | Larger values cost more time and GPU memory. |
| `--num_samples` | `1` | Multiple samples require a single input image in the model API. |
| `--no_llava` | false | Skip captioning and pass empty captions. Use when LLaVA weights are absent. |

## Guidance and prompt flags

| Flag | Default | Effect |
| --- | --- | --- |
| `--a_prompt` | photorealistic positive suffix | Appended to generated/manual caption. |
| `--n_prompt` | negative prompt for artifacts | Used as unconditional text in the condition batch. |
| `--s_cfg` | `4.0` | Text guidance scale. README quality settings use higher values. |
| `--spt_linear_CFG` | `1.0` | Start point when linear CFG is enabled. |
| `--linear_CFG` | true in source argparse | Increases CFG over the sampler schedule. |
| `--s_stage1` | `-1` | Stage1 restoration control; negative is a documented invalid/disabled value. |
| `--s_stage2` | `1.0` | Stage2 control; lower slightly for visual quality, keep high for fidelity. |
| `--linear_s_stage2` | false | Linearly increase stage2 control when enabled. |
| `--s_churn` | `5` | EDM sampler churn. |
| `--s_noise` | `1.01` | EDM noise multiplier. |
| `--color_fix_type` | `Wavelet` | `Wavelet`, `AdaIn`, or `None`. |

## Memory and dtype flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--ae_dtype` | `bf16` | CLI accepts `fp32` or `bf16`; internal model rejects AE `fp16`. |
| `--diff_dtype` | `fp16` | Diffusion dtype: `fp32`, `fp16`, or `bf16`. |
| `--loading_half_params` | false | Converts loaded model parameters to half precision. |
| `--use_tile_vae` | false | Enables tiled VAE hooks. Useful for memory pressure but can slow runs. |
| `--encoder_tile_size` | `512` | Encoder tile size when tiled VAE is enabled. |
| `--decoder_tile_size` | `64` | Decoder tile size when tiled VAE is enabled. |
| `--load_8bit_llava` | false | Reduces LLaVA memory use if bitsandbytes/device support is available. |

## Example dry-run command

```bash
python sub-skills/batch-restoration/scripts/supir_batch_restore.py \
  --img_dir inputs --save_dir outputs --SUPIR_sign Q --upscale 2 \
  --edm_steps 50 --color_fix_type Wavelet --dry-run
```

If the dry run is satisfactory, checkpoints are ready, and the active Python
environment can import `SUPIR`/`sgm` (plus `llava` only when captioning is
enabled), add `--run`. Pass `--llava_model_path` or set
`SUPIR_LLAVA_MODEL_PATH` when using LLaVA outside a source checkout that provides
`CKPT_PTH.py`.

## Batch troubleshooting

| Symptom | Fix |
| --- | --- |
| Wrapper reports missing input directory | Create or mount the image directory before any model load. |
| Input folder contains unsupported files | Pre-filter or create a manifest; do not let a long run fail halfway on a text/hidden file. |
| SUPIR and LLaVA share one GPU and OOM | Use `--no_llava`, `--load_8bit_llava`, lower output size, or move to a two-GPU host. |
| Results look over-sharpened or lower fidelity | Lower guidance, try `SUPIR_sign F`, use `s_stage2=1.0`, and record seed/checkpoint. |
| Results are visually pleasing but drift from the input | Increase fidelity controls, reduce CFG, compare Q vs F, and keep the same seed. |
| Outputs missing or overwritten | Check `--save_dir` permissions and image stem collisions. |

## Native verification candidate

A strict end-to-end batch native check needs a tiny input image, CUDA, all
checkpoints, and user approval for model loading. A safe pre-check can validate
syntax, imports, argument mapping, input folder existence, and checkpoint paths
without generating an image.
