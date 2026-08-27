# OmniLive Benchmark Workflow Reference

Use this reference to plan OmniLive audio/video benchmark runs. Do not launch benchmark jobs from a Creator/session that is only validating the skill. These workflows need full checkpoints, datasets, CUDA, and task-specific Python dependencies.

## Common planning steps

1. Validate the model root:

```bash
python scripts/check_omnilive_layout.py /models/internlm-xcomposer2d5-ol-7b --workflow benchmark-video --require-weights
python scripts/check_omnilive_layout.py /models/internlm-xcomposer2d5-ol-7b --workflow benchmark-audio --require-weights
```

2. Decide GPU sharding. The reference launchers split work by `CUDA_VISIBLE_DEVICES`; each visible GPU becomes one chunk process.
3. Keep output folders unique per benchmark, e.g. `outputs/mlvu`, `outputs/mvbench`, `outputs/video_mme`, `outputs/streamingbench`.
4. Treat `--max-frame` as a VRAM/coverage knob. It caps the selected frames after uniform video sampling. Lower values reduce memory and latency but may miss short evidence.

## Audio ASR benchmarks

Supported dataset keys in the reference ASR evaluator:

| Key | Language | Expected manifest |
| --- | --- | --- |
| `librispeech` | English | JSONL with `audio`, `source`, `gt` fields. |
| `wenet_test_meeting` | Chinese | JSONL with `audio`, `source`, `gt` fields. |
| `wenet_test_net` | Chinese | JSONL with `audio`, `source`, `gt` fields. |

Planning command shape:

```bash
export TOKENIZERS_PARALLELISM=False
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
CHECKPOINT=/models/internlm-xcomposer2d5-ol-7b/audio
DATASET=wenet_test_net
NPROC_PER_NODE=8

python -m torch.distributed.launch --use_env \
  --nproc_per_node ${NPROC_PER_NODE:-8} --nnodes 1 \
  evaluate_asr.py \
  --checkpoint "$CHECKPOINT" \
  --dataset "$DATASET" \
  --batch-size 20 \
  --num-workers 4
```

Evaluator behavior to preserve when adapting:

- Uses `Qwen2AudioForConditionalGeneration` and `AutoProcessor` from the `audio/` checkpoint.
- Builds a chat-style audio prompt: `Detect the language and recognize the speech.`
- Reads audio bytes locally or over HTTP(S), decodes with ffmpeg, and computes WER after language-specific normalization.
- Distributed workers gather predictions; rank 0 writes a timestamped JSON result and prints per-source WER.
- The manifest root is a dataset-local configuration detail. Ensure paths resolve before launching; do not leave placeholders such as `IMAGE_DIR` in a production plan.

## MLVU video benchmark

Expected video root layout:

```text
video_root/
  1_plotQA/
  2_needle/
  3_ego/
  4_count/
  5_order/
  6_anomaly_reco/
  7_topic_reasoning/
```

Launcher shape:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
VIDEO_ROOT=/datasets/mlvu
MODEL_PATH=/models/internlm-xcomposer2d5-ol-7b/base
OUT=outputs/mlvu

# One process per visible GPU; each process receives --num-chunks and --chunk-idx.
python -m benchmarks.mlvu.mlvu \
  --ixc-model-path "$MODEL_PATH" \
  --video-folder "$VIDEO_ROOT" \
  --save-folder "$OUT" \
  --max-frame 64 \
  --task all \
  --num-chunks 4 \
  --chunk-idx 0
```

After all chunks complete, merge/evaluate the output folder with an `eval_mlvu`-equivalent aggregator. MLVU samples 16 frames per clip, uses at least 5 clips and at most 32 clips, and formats multiple-choice prompts as `The answer is`.

## Video-MME benchmark

Expected video root layout: flat `*.mp4` files named by Video-MME video IDs. The evaluator reads task metadata from a parquet table and appends `.mp4` to each video ID.

Launcher shape:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
VIDEO_ROOT=/datasets/video_mme
MODEL_PATH=/models/internlm-xcomposer2d5-ol-7b/base
OUT=outputs/video_mme

python -m benchmarks.video_mme.video_mme \
  --ixc-model-path "$MODEL_PATH" \
  --video-folder "$VIDEO_ROOT" \
  --save-folder "$OUT" \
  --max-frame 64 \
  --task all \
  --num-chunks 4 \
  --chunk-idx 0
```

Task values are `short`, `medium`, `long`, or `all`. The reference evaluator catches per-sample exceptions and continues, so inspect skipped/error counts rather than trusting a successful exit alone.

## MVBench benchmark

Expected video root layout is a collection of task-specific subtrees under one `video_root`, such as Charades/STAR, Something-Something, Moments in Time, FunQA, CLEVRER, Perception, STA, SceneQA, NTU RGB+D, VLNQA, and TVQA frame folders. Some tasks use video files; `Episodic Reasoning` uses frame folders.

Launcher shape:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
VIDEO_ROOT=/datasets/mvbench
MODEL_PATH=/models/internlm-xcomposer2d5-ol-7b/base
OUT=outputs/mvbench

python -m benchmarks.mvbench.mvbench \
  --ixc-model-path "$MODEL_PATH" \
  --video-folder "$VIDEO_ROOT" \
  --save-folder "$OUT" \
  --max-frame 32 \
  --task all \
  --num-chunks 4 \
  --chunk-idx 0
```

MVBench uses at most 4 clips by default and inserts an image prefix in the prompt. The dataset map contains many nested expected subdirectories; validate each task-specific root before launch.

## StreamingBench

Expected root layout for the `real` task:

```text
StreamingBench_root/
  real/
    sample_1/
      video.mp4
    sample_10/
      video.mp4
    ...
```

Launcher shape:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
VIDEO_ROOT=/datasets/StreamingBench
DATA_FILE=benchmarks/streamingbench/src/data/questions_real.json
MODEL_PATH=/models/internlm-xcomposer2d5-ol-7b/base
OUT=outputs/streamingbench/real_output_IXC2d5_OL_0.json

python -m benchmarks.streamingbench.src.eval \
  --model_name IXC2d5_OL \
  --benchmark_name Streaming \
  --video_folder "$VIDEO_ROOT" \
  --data_file "$DATA_FILE" \
  --output_file "$OUT" \
  --num_chunks 4 \
  --chunk_id 0 \
  --ixc-model-path "$MODEL_PATH" \
  --max-frame 64
```

Notes:

- The `IXC2d5_OL` model wrapper loads `base/` with `AutoModelForCausalLM` and returns only the first generated character for multiple-choice scoring.
- The benchmark framework can also route `StreamingProactive` or `StreamingSQA` if the task data and evaluator are present.
- Some helper code creates clipped videos for timestamps; ensure write permissions for the benchmark work/output directories.

## MMBench-Video through VLMEvalKit

The supported MMBench-Video plan uses VLMEvalKit by changing the `XComposer2d5` model path from the non-OmniLive 2.5 model to the OmniLive `base/` component, then launching:

```bash
torchrun --nproc-per-node=8 run.py --data MMBench-Video --model XComposer2d5 --nframe 64
```

Plan this as an external-evaluator integration, not a bundled OmniLive script. Confirm VLMEvalKit version, model config edit, dataset license/access, and output submission format before launch.

## Benchmark troubleshooting signals

- Immediate `trust_remote_code`/configuration errors usually mean the selected model path points at the model root instead of `base/` for video benchmarks, or at the root instead of `audio/` for ASR.
- `decord` or ffmpeg errors usually indicate a video/audio codec issue or missing system packages.
- CUDA OOM: lower `--max-frame`, reduce batch size for ASR, reduce visible GPU contention, or shard across more chunks.
- Suspiciously high WER/low video accuracy: verify dataset roots and multiple-choice label parsing before blaming the model.
- Empty output chunks: check `CUDA_VISIBLE_DEVICES` chunk indexing, dataset size versus `num_chunks`, and exception swallowing in per-sample loops.
