# Evaluation Workflows

`swift eval` wraps EvalScope and can evaluate local model IDs/directories or an existing OpenAI-compatible service. The Python API equivalent is `swift.eval_main(EvalArguments(...))`.

## Environment and Backends

Install evaluation extras before using `swift eval`:

```bash
pip install ms-swift[eval] -U
```

Backends:

| Backend | Best for | Dataset examples | Notes |
| --- | --- | --- | --- |
| `Native` | Text benchmarks, custom MCQ/QA, result visualization | `gsm8k`, `arc`, `mmlu`, `general_mcq`, `general_qa` | Default backend and the only backend for custom MCQ/QA folders. |
| `OpenCompass` | Text benchmarks through OpenCompass | `gsm8k`, `mmlu`, `ceval`, `humaneval` | Uses chat/completions endpoint internally. `--local_dataset true` may create a `data` directory in the current working directory. |
| `VLMEvalKit` | Multimodal / vision-language benchmarks | `RealWorldQA`, `MMBench`, `OCRBench`, `MMMU_DEV_VAL` | Requires VLMEvalKit-related optional dependencies and may fail on missing `cv2` or multimedia packages. |

`swift eval --help` can fail in a minimal install because `swift.pipelines.eval` imports EvalScope at module import time. Treat that as an optional dependency issue, not as evidence that the base `swift` CLI is broken.

## Basic CLI Patterns

Local text evaluation:

```bash
CUDA_VISIBLE_DEVICES=0 swift eval \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --eval_backend Native \
  --infer_backend transformers \
  --eval_limit 10 \
  --eval_dataset gsm8k
```

Existing service evaluation:

```bash
swift eval \
  --model Qwen2.5-service-name \
  --eval_backend OpenCompass \
  --eval_url http://127.0.0.1:8000/v1 \
  --eval_limit 100 \
  --eval_dataset gsm8k
```

Complex Native evaluation:

```bash
CUDA_VISIBLE_DEVICES=0 swift eval \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --eval_backend Native \
  --infer_backend transformers \
  --eval_limit 10 \
  --eval_dataset gsm8k \
  --eval_dataset_args '{"gsm8k": {"few_shot_num": 0, "filters": {"remove_until": "</think>"}}}' \
  --eval_generation_config '{"max_tokens": 512, "temperature": 0}' \
  --extra_eval_args '{"ignore_errors": true, "debug": true}'
```

Important `EvalArguments` fields:

- `eval_dataset`: one or more benchmark names. Names are validated per backend and case-normalized against EvalScope registries.
- `eval_backend`: `Native`, `OpenCompass`, or `VLMEvalKit`; default is `Native`.
- `infer_backend`: local inference backend such as `transformers`, `vllm`, `sglang`, or `lmdeploy` when `--eval_url` is not supplied.
- `eval_url`: existing service base URL. If it contains `/chat/completions`, ms-swift strips that suffix and stores the base URL.
- `eval_limit`: sample cap per dataset for smoke tests and bounded debugging.
- `eval_dataset_args`, `eval_generation_config`, `extra_eval_args`: JSON strings parsed by ms-swift.
- `eval_output_dir`: output root. ms-swift writes backend-specific subdirectories under it.
- `eval_num_proc`: maximum concurrent eval clients; default is 16.
- `result_jsonl`: initialized under a result directory and appended with the evaluation report.

## Custom Native MCQ Dataset

Custom multiple-choice evaluation uses `general_mcq` and `Native` only.

Folder shape:

```text
mcq/
├── example_dev.csv   # optional few-shot examples
└── example_val.csv   # required evaluation examples
```

CSV header shape:

```text
id,question,A,B,C,D,answer
1,Question text,Option A,Option B,Option C,Option D,C
```

Rules:

- File names must be `{subset}_val.csv` for evaluation data and optional `{subset}_dev.csv` for few-shot examples.
- Required columns are `question`, at least two option columns from `A` through `J`, and `answer`.
- `id` is optional.
- `answer` must be one of the present option letters.
- A subset name is the part before `_val.csv` or `_dev.csv`.

Launch pattern:

```bash
python scripts/validate_eval_dataset.py mcq ./mcq --subset example

CUDA_VISIBLE_DEVICES=0 swift eval \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --eval_backend Native \
  --infer_backend transformers \
  --eval_dataset general_mcq \
  --eval_dataset_args '{"general_mcq": {"local_path": "./mcq", "subset_list": ["example"]}}'
```

## Custom Native QA Dataset

Custom QA evaluation uses `general_qa` and `Native` only.

Folder shape:

```text
qa/
└── example.jsonl
```

JSONL shape:

```json
{"query": "What is the capital of China?", "response": "The capital of China is Beijing."}
```

Rules:

- File names are `{subset}.jsonl`.
- Every non-empty JSONL line must be an object with non-empty string `query` and `response` fields.
- The subset list uses the file stem, such as `example`.

Launch pattern:

```bash
python scripts/validate_eval_dataset.py qa ./qa --subset example

CUDA_VISIBLE_DEVICES=0 swift eval \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --eval_backend Native \
  --infer_backend transformers \
  --eval_dataset general_qa \
  --eval_dataset_args '{"general_qa": {"local_path": "./qa", "subset_list": ["example"]}}'
```

## Evaluation During Training

Training commands can delegate periodic evaluation to EvalScope by adding EvalScope flags to `swift sft` or related training routes:

```bash
CUDA_VISIBLE_DEVICES=0 swift sft \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --tuner_type lora \
  --dataset AI-ModelScope/alpaca-gpt4-data-zh#100 \
  --eval_strategy steps \
  --eval_steps 5 \
  --eval_use_evalscope true \
  --eval_dataset gsm8k \
  --eval_dataset_args '{"gsm8k": {"few_shot_num": 0}}' \
  --eval_limit 10
```

Use this sub-skill only for the EvalScope-related flags. Route optimizer, LoRA rank, batch size, save strategy, dataset schema, and distributed launch choices to their owning sub-skills.

## Programmatic API

```python
from swift import EvalArguments, eval_main

report = eval_main(EvalArguments(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    eval_dataset="arc",
    infer_backend="transformers",
    eval_backend="Native",
    eval_limit=10,
    eval_generation_config={"max_new_tokens": 128, "temperature": 0.1},
    extra_eval_args={"ignore_errors": False},
))
```

For a service URL:

```python
from swift import EvalArguments, eval_main

report = eval_main(EvalArguments(
    model="service-display-name",
    eval_url="http://127.0.0.1:8000/v1",
    eval_dataset=["gsm8k"],
    eval_backend="OpenCompass",
    eval_limit=100,
))
```
