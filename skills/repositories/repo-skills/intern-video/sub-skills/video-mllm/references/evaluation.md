# InternVideo3 evaluation reference

InternVideo3 evaluation files are benchmark launchers rather than lightweight tests. Treat them as command-shape evidence unless the user provides benchmark data, model checkpoints, CUDA resources, and approval to run.

## Evaluation families

### Aggregated LMMS-Eval family

The aggregate launcher runs this subset: MVBench, LVBench, VideoMME, VideoMMMU, VSIBench, MLVU, and LongVideoBench. The common command shape is:

```bash
export MODEL_PATH=<model-id-or-dir>
export OUTPUT_DIR=<output-dir>
export HF_DATASETS_OFFLINE=1

accelerate launch --num_processes=<gpu-count> \
  -m lmms_eval \
  --model internvideo3 \
  --model_args pretrained=${MODEL_PATH},min_pixels=<min>,max_pixels=<max>,fps=4,max_num_frames=<frames>,attn_implementation=flash_attention_2 \
  --tasks <benchmark-task> \
  --batch_size 1 \
  --log_samples \
  --log_samples_suffix internvideo3 \
  --output_path ${OUTPUT_DIR}/<benchmark>/internvideo3
```

The scripts install or edit the local `lmms-eval` package before launch. In production, prefer a prebuilt evaluation environment and run the command shape directly.

### Thinking variants

Several scripts append `enable_thinking=true` to `model_args`: LongVideoBench, LVBench, MLVU, MVBench, VideoMME, VideoMMMU, and VSIBench. Use a thinking variant only when the comparison target expects reasoning traces or the user explicitly asks to evaluate that mode.

### Torchrun Python evaluators

Some benchmarks use dedicated Python scripts under `torchrun --nproc_per_node=8` instead of LMMS-Eval task names:

- Temporal grounding over ActivityNet/Charades/QVHighlights style JSON files; outputs per-rank JSONL, then merged IoU metrics (`mIoU`, `R@0.3`, `R@0.5`, `R@0.7`).
- NExT-QA; reads a `val.csv`, indexes videos by id, and reports overall/type accuracy.
- TempCompass, Tomato, VideoMME v2, and VNBench; scripts use model path/output directory args and may require `qwen-vl-utils` plus benchmark-specific data layouts.

Check each Python evaluator for data-root arguments before running. Some defaults are placeholders or fixed paths and must be parameterized in the user's working copy.

## Benchmark task map

| Script family | Task name or target | Typical frame cap in launcher | Notes |
|---|---:|---:|---|
| MVBench | `mvbench` | 256 | Has normal and thinking launchers. |
| LVBench | `lvbench` | 1024 | Has normal and thinking launchers. |
| VideoMME | `videomme` | 1024 | Has normal and thinking launchers; VideoMME v2 uses a separate Python evaluator with optional subtitles. |
| VideoMMMU | `video_mmmu` | 256 | Has normal and thinking launchers. |
| VSIBench | `vsibench` | 256 | Has normal and thinking launchers. |
| MLVU | `mlvu_dev` | 2048 | Has normal and thinking launchers. |
| LongVideoBench | `longvideobench_val_v` | 2048 | Has normal and thinking launchers. |
| EgoSchema | `egoschema` | 2048 | LMMS-Eval family. |
| HRBench | `hrbench` | 256 | LMMS-Eval family. |
| MotionBench | `motionbench` | 1024 | LMMS-Eval family. |
| Perception Test | `perceptiontest_val_mc` | 512 | LMMS-Eval family. |
| MMMU | `mmmu_val` | 128 | A separate MLA-named script uses the same benchmark task. |
| MMSI | `mmsi_bench` / `mmsi_video` | 256 | Separate image/video variants. |
| DSI | `dsi_bench` | 1024 | LMMS-Eval family. |
| Charades temporal grounding | `temporal_grounding_charades` or dedicated grounding evaluator | 512 in LMMS-style script | Verify whether the task expects temporal-span output or multiple choice. |
| NExT-QA | dedicated Python evaluator | default `fps=4`, pixel args in parser | Requires a CSV plus videos arranged by id. |

## Data and environment caveats

- `HF_DATASETS_OFFLINE=1` is set in LMMS-Eval scripts. Pre-cache or locally stage every benchmark; otherwise evaluation fails even with network access.
- Benchmark datasets are license- and storage-heavy. Do not download automatically without explicit user approval.
- LMMS-Eval scripts assume `accelerate`, a local/equivalent `lmms_eval` package, `transformers==4.57.3`, and FlashAttention-compatible CUDA when `attn_implementation=flash_attention_2` is used.
- Dedicated Python evaluators load `AutoModelForCausalLM`/`AutoProcessor` with bfloat16 and `attn_implementation="sdpa"` in code, but the shell wrappers may still install 4.57.3 and `qwen-vl-utils` at runtime.
- Many outputs are per-rank JSON/JSONL and require a rank-0 merge step. Always inspect partial result files before interpreting metrics.

## Minimal evaluation readiness checklist

1. Confirm `MODEL_PATH` resolves to a compatible InternVideo3 checkpoint and processor.
2. Confirm benchmark data is already staged and the evaluator points to it through supported args/env vars or a user-approved local config edit.
3. Decide normal versus `enable_thinking=true` mode before comparing against paper numbers.
4. Choose an appropriate `max_num_frames`/pixel budget for the user's GPUs.
5. Pre-install evaluation packages rather than allowing scripts to mutate the environment during evaluation.
6. Log task name, model args, output directory, package versions, and whether benchmark data were offline/pre-cached.
