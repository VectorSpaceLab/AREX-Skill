# EasyR1 data and reward formats

This reference distills the EasyR1 data loader, prompt-template, and reward-manager contracts into reusable operating guidance. It is self-contained: do not depend on the original checkout when preparing a new dataset or reward function.

## Backend boundary

Data and reward contract checks are CPU-safe when they avoid remote dataset/model downloads. End-to-end EasyR1 training still requires the full CUDA training stack, including flash-attn, vLLM, Ray workers, a compatible model, and enough GPU memory. A passing reward or row-shape smoke test only proves that the local contract is well formed.

## Dataset path and split syntax

EasyR1 accepts a dataset identifier in configuration keys such as `data.train_files` and `data.val_files`.

- Use `dataset_name@split` to select a split; if `@split` is omitted, EasyR1 treats the split as `train`.
- A local directory is loaded as a dataset builder directory. The first file extension determines the loader type, with `jsonl` normalized to `json`.
- A local file is loaded by extension. For newline-delimited JSON, use a `.jsonl` extension.
- Any non-local identifier is treated as a remote dataset name. This can trigger network access and cache requirements during dataset construction.

Keep train and validation schemas identical. The easiest pattern is to keep all configured columns present on every row, using empty lists for missing media instead of omitting media keys on some rows.

## Core data configuration keys

| Key | Meaning | Practical guidance |
| --- | --- | --- |
| `data.prompt_key` | Column containing the user task text. | Default examples use names such as `problem`; make this a string column. |
| `data.answer_key` | Column containing the ground-truth answer. | The loader renames this value to `ground_truth` for reward functions. |
| `data.image_key` | Column containing image entries. | If present on a row, EasyR1 builds a multimodal image prompt by splitting the prompt text on `<image>`. |
| `data.video_key` | Column containing video entries. | If present on a row, EasyR1 builds a video prompt by splitting the prompt text on `<video>`. |
| `data.image_dir` | Optional media root for relative string media paths. | In this EasyR1 version, this prefix is also used for relative video strings. Use one shared media root if videos are relative. |
| `data.video_fps` | FPS used when fetching video frames. | Default is `2.0`; increase only when the model and runtime can afford the tokens. |
| `data.min_pixels` / `data.max_pixels` | Image/video resize bounds. | Tune these together with `data.max_prompt_length`; too many pixels create more vision tokens. |
| `data.max_prompt_length` | Left-padded prompt length after tokenization/processing. | Set high enough for chat wrapper plus media tokens, or filter/truncate deliberately. |
| `data.max_response_length` | Rollout response length. | Reward functions receive `response_length`; DAPO overlong penalties usually need this value. |
| `data.format_prompt` | Jinja file applied to `content` before chat-template wrapping. | Render exactly one prompt string; do not include model-specific chat tokens here unless you intentionally override the chat template. |
| `data.override_chat_template` | Optional tokenizer chat-template replacement. | Use only when the tokenizer's default chat template is wrong for the model. |
| `data.filter_overlong_prompts` | Whether overlong prompts are filtered during dataset construction. | Filtering can invoke tokenizers/processors and may require model files or cached processors. |

## Row schemas

### Text-only rows

```json
{"problem": "What is 2 + 2?", "answer": "4"}
```

Text-only rows are converted to a single user chat message whose content is the formatted prompt string. The tokenizer then applies the model chat template with `add_generation_prompt=True`.

### Image or multi-image rows

```json
{
  "problem": "<image>\nWhat object is highlighted?",
  "images": ["sample_0001.png"],
  "answer": "triangle"
}
```

Rules:

- Put one `<image>` placeholder in the prompt for each expected image item.
- `images` may contain relative strings, absolute strings, bytes-like image records from a dataset loader, or already decoded image objects. String paths are optionally prefixed by `data.image_dir`.
- For multi-image data, use a list such as `"images": ["left.png", "right.png"]` and include two `<image>` placeholders.
- For text-image mixed datasets that share an `images` column, use `"images": []` for text-only rows and avoid `<image>` in those prompts.
- After loading, EasyR1 stores original media references under `multi_modal_data` for rollout workers.

### Video rows

```json
{
  "problem": "<video>\nDescribe the final state.",
  "videos": ["clip_0001.mp4"],
  "answer": "the door is open"
}
```

Rules:

- Use `<video>` placeholders in the prompt for video items.
- Keep video strings reachable from the training process. In this version, the media-root key used for relative video strings is still `data.image_dir`.
- Video processing depends on the installed vision utility stack and may consume substantial CPU/GPU memory before training starts.

## Prompt template patterns

A prompt template is a Jinja template rendered with `content=<row[prompt_key]>`. Keep templates deterministic and model-agnostic.

### Math format

```jinja
{{ content | trim }} You FIRST think about the reasoning process as an internal monologue and then provide the final answer. The reasoning process MUST BE enclosed within <think> </think> tags. The final answer MUST BE put in \boxed{}.
```

Pair this with a math reward that checks both boxed-answer correctness and formatting.

### R1-V format

```jinja
{{ content | trim }} A conversation between User and Assistant. The user asks a question, and the Assistant solves it. The assistant first thinks about the reasoning process in the mind and then provides the user with the answer. The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively.
```

Pair this with a sequential reward that extracts `<answer>...</answer>`.

### DAPO format

```jinja
Solve the following math problem step by step. The last line of your response should be of the form Answer: $Answer (without quotes) where $Answer is the answer to the problem.

{{ content | trim }}

Remember to put your answer on its own line after "Answer:".
```

Pair this with a reward that returns both raw accuracy and a normalized filter key such as `accuracy_normalized`.

### Android GUI format

The Android GUI template asks the model to inspect a screenshot, identify a traffic-light color, apply a number-selection rule, and output only a single digit position `0`, `1`, or `2`. See [Android GUI cookbook](android-gui-cookbook.md) for the full distilled workflow.

## Reward function contract

Configure a reward target as `worker.reward.reward_function=./module.py:function_name` or another path visible to the training process. If the function name is omitted, EasyR1 looks for `main`. The module may define:

```python
REWARD_NAME = "short_metric_family"
REWARD_TYPE = "batch"  # or "sequential"
```

If `REWARD_TYPE` is absent, EasyR1 treats the function as `batch`. The configured `worker.reward.reward_function_kwargs` dictionary is partially applied to the reward function before calls.

### Reward input

Every reward input contains:

```python
{
    "response": "decoded model response",
    "response_length": 123,
    "ground_truth": "row answer after data.answer_key mapping",
}
```

The response is decoded from valid response tokens using the configured `skip_special_tokens` flag.

### Batch reward

```python
from typing import Any

REWARD_NAME = "my_task"
REWARD_TYPE = "batch"

def compute_score(reward_inputs: list[dict[str, Any]]) -> list[dict[str, float]]:
    scores = []
    for item in reward_inputs:
        ok = item["response"].strip() == item["ground_truth"].strip()
        scores.append({"overall": 1.0 if ok else 0.0, "accuracy": 1.0 if ok else 0.0})
    return scores
```

Return exactly one score dictionary per input. Every dictionary must include numeric finite `overall`; EasyR1 writes `overall` to the final response token and logs every score key as a metric list.

### Sequential reward

```python
from typing import Any

REWARD_NAME = "my_task"
REWARD_TYPE = "sequential"

def compute_score(reward_input: dict[str, Any]) -> dict[str, float]:
    ok = reward_input["response"].strip() == reward_input["ground_truth"].strip()
    return {"overall": 1.0 if ok else 0.0, "accuracy": 1.0 if ok else 0.0}
```

Use sequential mode when the reward is easier to express per item or uses per-item side effects. Prefer batch mode for pure Python scoring because it matches the default manager behavior.

## Distilled built-in reward examples

| Example family | Type | Expected score keys | Contract detail |
| --- | --- | --- | --- |
| Math | `batch` | `overall`, `format`, `accuracy` | Checks `<think>...</think>` plus boxed final answer; `overall` is a weighted combination. |
| R1-V | `sequential` | `overall`, `format`, `accuracy` | Checks `<think>...</think><answer>...</answer>` and grades the answer text against the ground truth. |
| DAPO | `batch` | `overall`, `accuracy`, `overlong`, `accuracy_normalized` | Extracts a final `Answer:` line, adds a soft overlong penalty, and exposes a normalized online-filtering key. |
| Android GUI | `batch` | `overall`, `accuracy` | Extracts digit `0`, `1`, or `2`; correct choice scores `1.0`, otherwise `0.0`. |

## Validation commands

Run the bundled script from the generated root skill directory or another convenient working directory:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py
```

Validate a custom batch reward:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py \
  --target ./my_reward.py:compute_score \
  --mode batch \
  --expect-keys overall,accuracy
```

Validate a custom sequential reward:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py \
  --target ./my_reward.py:compute_score \
  --mode sequential
```

Validate a DAPO-style reward with kwargs:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py \
  --target ./dapo_reward.py:compute_score \
  --mode batch \
  --kwargs-json '{"max_response_length":20480,"overlong_buffer_length":4096,"overlong_penalty_factor":1.0}' \
  --expect-keys overall,accuracy_normalized,overlong
```

Expected success signal: the script exits `0` and prints a JSON summary with `status: "ok"`. If a score dictionary lacks `overall`, the script exits nonzero for custom targets; the default run includes an internal negative guard that proves this failure is caught.

## Pre-launch checklist

- [ ] Train and validation rows use the configured `prompt_key` and `answer_key` consistently.
- [ ] Media placeholders match media lists; text-only mixed rows use empty media lists and no media placeholders.
- [ ] Relative media paths are resolvable from the training process, preferably through `data.image_dir`.
- [ ] Prompt template renders a single prompt string and does not accidentally escape required tags.
- [ ] Reward function target includes the correct `module.py:function` suffix or defines `main`.
- [ ] Reward module metadata sets `REWARD_TYPE` deliberately.
- [ ] Batch rewards return a list whose length equals the input batch length.
- [ ] Every score dictionary contains finite numeric `overall` and any online-filtering metric key required by the training config.
- [ ] CPU smoke checks pass, and full training is still treated as CUDA/full-runtime work.
