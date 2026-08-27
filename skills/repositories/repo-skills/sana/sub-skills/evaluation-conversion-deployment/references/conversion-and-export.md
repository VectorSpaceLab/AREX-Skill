# Conversion and Export

This reference covers safe planning for Sana checkpoint conversion and export.
It does not run conversion jobs.

## Supported conversion families

| Family | Source | Destination | Planner concerns |
| --- | --- | --- | --- |
| Sana image | `.pth` checkpoint | Diffusers safetensors / pipeline directory | Model family, image size, dtype, and whether the full pipeline is requested |
| Sana video | `.pth` checkpoint | Diffusers video pipeline directory | Video size, task direction, scheduler, and dtype |
| SVDQuant / Nunchaku | Sana `.pth` checkpoint | quantization-ready diffusers pipeline | Model family, image size, dtype, and downstream quantization toolchain |

## Planning rules

### Image conversion
- Choose a model type that matches the checkpoint family.
- Supported image model types include `SanaMS_1600M_P1_D20`, `SanaMS_600M_P1_D28`, `SanaMS1.5_1600M_P1_D20`, `SanaMS1.5_4800M_P1_D60`, `SanaSprint_1600M_P1_D20`, `SanaSprint_600M_P1_D28`, and Sprint teacher variants when using the image converter.
- Supported image sizes are `512`, `1024`, `2048`, and `4096`.
- Use `bf16` only when the checkpoint family and downstream pipeline support it.
- `save_full_pipeline` expands the export to include the full pipeline, not just the transformer.
- Validate that the dump path is writable and empty or intentionally reused.
- When the checkpoint and `model_type` disagree, stop and correct the model selection first.
- Example planner call:
  ```bash
  python scripts/plan_conversion_command.py \
    --family sana-image \
    --orig-ckpt-path output/Sana_1600M_1024px_BF16/checkpoints/Sana_1600M_1024px_BF16.pth \
    --model-type SanaMS_1600M_P1_D20 --image-size 1024 --dtype bf16 \
    --dump-path output/Sana_1600M_1024px_BF16_diffusers --save-full-pipeline
  ```

### Video conversion
- `task` must be `t2v` or `i2v`.
- Supported video sizes are `480` and `720`.
- Scheduler choices are `flow-dpm_solver`, `flow-euler`, and `uni-pc`; `i2v` requires the flow-euler path.
- The `save_full_pipeline` flag controls whether the whole diffusers pipeline is written.
- The converted tree should contain the exported pipeline artifacts rather than a training checkpoint.
- Example planner call:
  ```bash
  python scripts/plan_conversion_command.py \
    --family sana-video \
    --orig-ckpt-path output/SANA-Video_2B_480p/checkpoints/SANA_Video_2B_480p.pth \
    --model-type SanaVideo --video-size 480 --task t2v --scheduler-type flow-dpm_solver \
    --dtype bf16 --dump-path output/SANA-Video_2B_480p_diffusers --save-full-pipeline
  ```

### SVDQuant / Nunchaku conversion
- Use this path only when preparing a quantized runtime pipeline.
- Supported SVDQuant planner model types are the image-family model types accepted by the SVDQuant converter: `SanaMS_1600M_P1_D20`, `SanaMS_600M_P1_D28`, `SanaMS1.5_1600M_P1_D20`, `SanaMS1.5_4800M_P1_D60`, `SanaSprint_1600M_P1_D20`, and `SanaSprint_600M_P1_D28`.
- `dtype` must match the intended runtime precision path.
- The planner should warn when the chosen model family is not one of the supported Sana image families.
- Treat the quantization toolchain as an extra dependency requirement rather than a direct runtime default.
- Example planner call:
  ```bash
  python scripts/plan_conversion_command.py \
    --family svdquant \
    --orig-ckpt-path output/SANA1.5_1.6B_1024px/checkpoints/SANA1.5_1.6B_1024px.pth \
    --model-type SanaMS1.5_1600M_P1_D20 --image-size 1024 --dtype bf16 \
    --dump-path output/SANA1.5_1.6B_1024px_svdquant_diffusers --save-full-pipeline
  ```

## Output-path validation

The planner must confirm:
- the output directory exists or can be created,
- the path is not the source checkpoint directory,
- the chosen destination will not overwrite an unrelated model export,
- the naming reflects the target family and precision.

## Common failure modes

- Wrong checkpoint path.
- `model_type` mismatch with the checkpoint family.
- Dtype mismatch between the source checkpoint and the downstream export.
- Missing write permission on the output path.
- Expecting conversion to perform inference or upload by itself.

## Safe command-planning behavior

The bundled planner should:
1. identify the requested conversion family,
2. map the family to the correct source script,
3. render a dry command line,
4. emit warnings about model family, dtype, scheduler, and output-path mismatches,
5. never start conversion or download missing weights automatically.

## Provenance labels

- `docs/model_zoo.md`
- `docs/4bit_sana.md`
- `tools/convert_scripts/convert_sana_to_diffusers.py`
- `tools/convert_scripts/convert_sana_video_to_diffusers.py`
- `tools/convert_scripts/convert_sana_to_svdquant.py`
