# Qwen-VL benchmark reference

This sub-skill groups the official Qwen-VL evaluation entrypoints, data converters, and score helpers.

## Core benchmark map

| Benchmark / family | Script or helper | Dataset key / input | Metric / output | Notes |
| --- | --- | --- | --- | --- |
| Flickr30K captioning | `scripts/evaluate_caption.py` | `flickr` | COCO caption metrics via `pycocoevalcap` | Distributed GPU inference |
| Nocaps captioning | `scripts/evaluate_caption.py` | `nocaps` | COCO caption metrics via `pycocoevalcap` | Distributed GPU inference |
| VQAv2 / OKVQA / TextVQA / VizWiz / DocVQA / ChartQA / GQA / OCRVQA / AI2D / RefCOCO family | `scripts/evaluate_vqa.py`, `scripts/evaluate_grounding.py` | dataset-specific `ds` values | VQA score, ANLS, relaxed accuracy, exact accuracy, IoU@0.5 | Dataset/layout-sensitive |
| ScienceQA image multiple choice | `scripts/evaluate_multiple_choice.py` | `scienceqa_test_img` | top-1 accuracy | Distributed GPU inference |
| MMBench dev/test | `scripts/mmbench/evaluate_multiple_choice_mmbench.py` | `mmbench_dev_20230712`, `mmbench_test_20230712` | JSON predictions, then `mmbench_evaluation.py` / `mmbench_evaluation_tricky.py` / submission conversion | CPU utility plus GPU inference |
| SEED-Bench image/video | `scripts/seed_bench/trans.py`, `scripts/seed_bench/eval.py` | `image_input.jsonl`, `video_input_4.jsonl` or configured output | prediction JSONL | Image conversion is CPU-friendly; video decoding may need Decord |
| MME | `mme/eval.py`, `mme/get_images.py` | external MME release | benchmark-specific scoring from external tool | Reference-only or external-layout dependent |
| TouchStone | `touchstone/README.md` | external dataset + judge workflow | GPT-4-style judge score | Methodology/reference-only; no bundled scorer |

## Distributed launch pattern

The official benchmark scripts generally use one of these forms:

```bash
python -m torch.distributed.launch --use-env \
  --nproc_per_node ${NPROC_PER_NODE:-8} \
  --nnodes ${WORLD_SIZE:-1} \
  --node_rank ${RANK:-0} \
  --master_addr ${MASTER_ADDR:-127.0.0.1} \
  --master_port ${MASTER_PORT:-12345} \
  <script> ...
```

or `torchrun` when the user prefers that launcher. The scripts in this repo are written for NCCL/CUDA inference and expect GPUs for the model forward pass.

## Output conventions

- `evaluate_caption.py`: writes a time-stamped JSON result file on rank 0.
- `evaluate_vqa.py`: writes a result file named from dataset, timestamp, few-shot value, and seed.
- `evaluate_grounding.py`: prints Precision@1 for RefCOCO-style IoU evaluation.
- `evaluate_multiple_choice.py`: prints `Acc@1`.
- `mmbench` scripts: write JSON predictions and can be converted to submission spreadsheets.
- `seed_bench/eval.py`: writes per-rank JSONL shards that are concatenated after the distributed run.

## When to use the helpers

- Use the CPU-capable MMBench converters and InfographicsVQA scorer when you already have the raw TSV/JSON inputs.
- Use `scripts/vqa.py` and `scripts/vqa_eval.py` for VQA-style scoring when the dataset uses the standard VQA annotation layout.
- Use the SEED-Bench converter before `scripts/seed_bench/eval.py` when your input is a JSON question file plus local image/video assets.
