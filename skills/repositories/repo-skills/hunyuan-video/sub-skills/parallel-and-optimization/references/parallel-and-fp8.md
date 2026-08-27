# Parallel and FP8 Workflows

## xDiT multi-GPU command shape

The xDiT path uses `torchrun` and the same bundled sampling runner:

```bash
torchrun --nproc_per_node=4 sub-skills/inference/scripts/run_sample_video.py \
  --model-base ckpts \
  --video-size 720 1280 \
  --video-length 129 \
  --infer-steps 50 \
  --prompt "A cat walks on the grass, realistic style." \
  --seed 42 \
  --embedded-cfg-scale 6.0 \
  --flow-shift 7.0 \
  --flow-reverse \
  --ulysses-degree 2 \
  --ring-degree 2 \
  --save-path ./results
```

Do not add `--use-cpu-offload` in distributed mode.

## Supported degree patterns

The repository documentation provides supported degree patterns for 129-frame runs. Representative examples:

| Resolution | Valid degree products |
| --- | --- |
| `1280 720` or `720 1280` | 8 GPUs: `8x1`, `4x2`, `2x4`, `1x8`; 4 GPUs: `4x1`, `2x2`, `1x4`; 2 GPUs: `2x1`, `1x2` |
| `1104 832` or `832 1104` | 4, 3, or 2 GPU variants listed in the docs |
| `960 960` | 6, 4, 3, or 2 GPU variants listed in the docs |
| `960 544` or `544 960` | 6, 4, 3, or 2 GPU variants listed in the docs |
| `720 720` | 5 or 3 GPU variants listed in the docs |

The implementation also checks that the spatial split is even. If a custom resolution cannot be split by the sequence-parallel world size, it raises an error mentioning that the video sequence cannot be split evenly.

## FP8 command shape

FP8 reduces model memory by using quantized DIT weights:

```bash
python sub-skills/inference/scripts/run_sample_video.py \
  --model-base ckpts \
  --dit-weight ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states_fp8.pt \
  --use-fp8 \
  --video-size 720 1280 \
  --video-length 129 \
  --infer-steps 50 \
  --prompt "A cat walks on the grass, realistic style." \
  --seed 42 \
  --embedded-cfg-scale 6.0 \
  --flow-shift 7.0 \
  --flow-reverse \
  --use-cpu-offload \
  --save-path ./results
```

The FP8 map file is derived by replacing `.pt` with `_map.pt`. For the file above, the required map is:

```text
ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states_fp8_map.pt
```

If the map is missing, `convert_fp8_linear()` raises an invalid FP8 map path error before useful generation begins.

## Builder helper

Use `scripts/build_optimized_command.py` for preflight validation:

```bash
python sub-skills/parallel-and-optimization/scripts/build_optimized_command.py multi-gpu --nproc-per-node 4 --ulysses-degree 2 --ring-degree 2 --prompt "..."
python sub-skills/parallel-and-optimization/scripts/build_optimized_command.py fp8 --dit-weight ckpts/.../mp_rank_00_model_states_fp8.pt --prompt "..."
```
