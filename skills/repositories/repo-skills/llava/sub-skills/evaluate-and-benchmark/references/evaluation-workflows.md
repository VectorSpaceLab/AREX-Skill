# Evaluation Workflows

## When to read

Read this before building custom evaluation commands or selecting a benchmark script family.

## Prompt families from the repo docs

The repo documents three general prompt families:

1. **Short-answer**: ask for a single word or short phrase.
2. **Option-only multiple choice**: include answer options and require the option letter directly.
3. **Natural QA**: no special postprocessing is needed.

These prompt families are the basis for all custom benchmark command templates in this sub-skill.

## Generic evaluation workflow

1. Convert or stage the dataset into the repo's question-file format.
2. Pick the correct `--conv-mode` for the model family.
3. If the dataset is large, use `--num-chunks` and `--chunk-idx`.
4. Write answers to a JSONL file.
5. Merge answer chunks when needed.
6. Convert or upload the final output only after validating the JSONL shape.

## Main command families

### `model_vqa.py`

Use for generic image-question evaluation where each row contains `question_id`, `image`, and `text`.

### `model_vqa_loader.py`

Use when the benchmark script expects chunked processing and a data loader over the question list.

### `model_vqa_mmbench.py`

Use for TSV-based multiple-choice evaluation with optional `--single-pred-prompt` and `--lang`.

### `model_vqa_science.py`

Use for ScienceQA-style JSON or JSONL evaluation, including image-backed and text-only examples.

## Output shape to remember

The common answer JSONL output used by LLaVA evaluation modules includes:

- `question_id`
- `prompt`
- `text`
- `answer_id`
- `model_id`
- `metadata`

MMBench-style output additionally records round metadata and options.

## Chunked inference pattern

The loader-based VQAv2 and ScienceQA scripts often use this pattern:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash scripts/v1_5/eval/<name>.sh
```

The script splits the question list into per-device chunks, launches one worker per chunk, and concatenates the outputs after all chunks finish.

## Model family prompt choice

Use the same conversation-mode logic described in the chat sub-skill. For benchmark runs, the wrong conv mode can change the exact prompt and therefore the score.

## Safe validation before launch

- validate the question JSON/TSV/JSONL shape first
- validate the answer JSONL shape before conversion or upload
- check that all image files referenced by the benchmark exist
- check that the chosen checkpoint family matches the benchmark command family
