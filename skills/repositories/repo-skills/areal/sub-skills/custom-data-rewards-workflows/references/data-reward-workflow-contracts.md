# Data, Reward, and RolloutWorkflow Contracts

This reference is self-contained operating guidance for AReaL dataset, reward, and rollout-workflow customization. It is safe to use without reopening the source checkout.

## 1. Dataset loading contract

AReaL consumes HuggingFace `datasets.Dataset`-style rows. The exact row keys depend on the trainer/workflow.

Primary helper:

```python
from areal.dataset import get_custom_dataset

dataset = get_custom_dataset(
    split="train",                 # usually "train" or "test"
    dataset_config=config.train_dataset,
    tokenizer=tokenizer,            # text workflows
    processor=processor,            # VLM workflows
)
```

Dataset config fields used by the helper:

| Field | Purpose |
|---|---|
| `path` | HuggingFace dataset name, local dataset path, saved-to-disk Dataset/DatasetDict path, or built-in dataset identifier. |
| `type` | Training/data family such as `sft`, `rl`, `rw`, or `dpo`. |
| `split` | Dataset split. Train defaults to `train`; validation defaults to `test`. |
| `batch_size`, `shuffle`, `drop_last`, `num_workers`, `pin_memory` | Dataloader behavior. |
| `max_length` | Optional token-length filter performed by built-in loaders. |
| `dataset_kwargs` | Extra dataset loader arguments. |
| `scheduling_spec` | Optional remote data-service loading. If the user's problem is data-service lifecycle, route to `services-cli-operations`. |

Custom dataset options:

1. Preprocess to a HuggingFace `Dataset` in the user's training script and pass the dataset directly to the trainer.
2. Save a processed dataset with `dataset.save_to_disk(...)` and configure `dataset_config.path` to that directory; AReaL's helper falls back to `load_from_disk` for unsupported built-in names.
3. Keep network downloads and large preprocessing outside validation. The bundled checker validates sample shape only; it does not download datasets.

## 2. Built-in dataset families

| Family | `type` | Rows expected/produced | Notes |
|---|---:|---|---|
| `gsm8k` | `sft` | `input_ids`, `loss_mask` | Tokenizes question+answer; completion tokens are marked in `loss_mask`. |
| `gsm8k` | `rl` | `messages`, `answer` | `messages` is an OpenAI-style chat list; `answer` is passed to the reward. |
| `geometry3k` | `sft` | `input_ids`, `loss_mask`, `multi_modal_input`, optional `mm_token_type_ids` | Requires a VLM processor. |
| `geometry3k` | `rl` | `messages`, `messages_chat`, `images`, `answer` | VLM RLVR row; `messages` is processor chat-template text, `messages_chat` is OpenAI/VLM shape for vLLM. |
| `clevr_count_70k` | `sft` | `input_ids`, `loss_mask`, `multi_modal_input`, optional `mm_token_type_ids` | Requires a VLM processor. |
| `clevr_count_70k` | `rl` | `messages`, `images`, `answer` | VLM RLVR row. |
| `virl39k` | `rl` | `messages`, `messages_chat`, `images`, `answer` | Loads parquet data plus images. Pre-stage image folders before multi-node use. |
| `hh-rlhf` | `rw` | `chosen_ids`, `rejected_ids` | Reward-model data. |
| `hh-rlhf` | `dpo` | `chosen_ids`, `rejected_ids`, `chosen_loss_mask`, `rejected_loss_mask` | DPO data with response-token masks. |
| `torl_data` | `rl` | `messages`, `answer` | Built-in helper may download canonical parquet files into a temporary runtime cache; pre-stage in controlled environments. |

## 3. Sample schema by training family

### SFT rows

After preprocessing, rows passed to LM training should contain:

```json
{
  "input_ids": [101, 102, 103, 2],
  "loss_mask": [0, 0, 1, 1]
}
```

Rules:

- `input_ids` and `loss_mask` must be equal-length integer arrays.
- `loss_mask=1` marks tokens that participate in the language-modeling loss.
- `attention_mask` is commonly added later during padding/collation.
- VLM SFT rows also carry `multi_modal_input` and sometimes `mm_token_type_ids` from the processor.

### RLVR rows

Rows used by `RLVRWorkflow` should contain a prompt and reward data:

```json
{
  "messages": [
    {"role": "user", "content": "What is 2 + 2? Put the answer in \\boxed{}."}
  ],
  "answer": "4"
}
```

Rules:

- `messages` is consumed by the workflow prompt extractor. By default it is a list of chat messages.
- All extra dataset fields are forwarded to the reward function as keyword arguments.
- Avoid dataset keys named `prompt`, `completions`, `prompt_ids`, or `completion_ids` when using the stock RLVR workflow; those names are already provided positionally to the reward function.

### VLM RLVR rows

Rows used by `VisionRLVRWorkflow` should contain processor-formatted text plus images:

```json
{
  "messages": "<chat-template-rendered text with image placeholder>",
  "messages_chat": [
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": ""}},
        {"type": "text", "text": "Solve the visual question."}
      ]
    }
  ],
  "images": ["<PIL image object, bytes, or preloaded image placeholder>"],
  "answer": "42"
}
```

Rules:

- `VisionRLVRWorkflow` expects `messages` and `images`.
- `messages_chat` is optional but useful for vLLM VLM backends; an empty URL is a placeholder in this direct workflow path because the workflow passes image bytes separately.
- For proxy-agent VLM calls, do **not** use empty image URLs. Provide a real HTTP(S) URL or `data:image/...;base64,...` URI in the OpenAI request.

### Agent workflow rows

Proxy agent workflows receive the raw dataset row in `run(data, **extra_kwargs)`. A conventional row is:

```json
{
  "messages": [{"role": "user", "content": "Solve the task."}],
  "answer": "expected output",
  "metadata": {"difficulty": "easy"}
}
```

Rules:

- The agent decides which keys to consume.
- If the agent calls OpenAI-compatible chat APIs, `messages` or `messages_chat` should follow OpenAI message rules.
- Rewards returned from `run()` are either one scalar for the latest completion or a dict mapping captured completion/response IDs to reward floats.

## 4. Reward function contract

The stock RLVR workflows are easiest to use with this synchronous, picklable, module-level function shape:

```python
def reward_fn(
    prompt: str,
    completions: str,
    prompt_ids: list[int],
    completion_ids: list[int],
    **kwargs,
) -> float:
    answer = kwargs["answer"]
    return 1.0 if is_correct(completions, answer) else 0.0
```

Important details:

- `RLVRWorkflow` and `VisionRLVRWorkflow` wrap the reward in `AsyncRewardWrapper` and run it in a process pool.
- The function and all arguments must be picklable.
- Keep imports light at module import time; place heavyweight verifiers or SDK clients behind lazy initialization where possible.
- Return a scalar `float` or numeric value convertible to float. Lists, tensors with more than one element, coroutine objects, and dicts are not valid stock RLVR rewards.
- If the reward is naturally async, either make a custom `RolloutWorkflow` that awaits it directly, or provide a synchronous wrapper for stock RLVR.

`AsyncRewardWrapper` behavior:

| Parameter | Default | Effect |
|---|---:|---|
| `timeout_seconds` | `15` | Timeout per reward attempt. |
| `max_workers` | auto | Shared process-pool size. Auto uses CPU/device count heuristics. |
| `max_retries` | `3` | Retries after timeout, broken pool, or exception. |

Failure behavior:

- Timeout after final retry returns `0`.
- Regular reward exceptions are retried and then re-raised.
- Broken process pools are recreated before retry when possible.
- Executors are shared by `max_workers` and cleaned up at process exit.

## 5. `RolloutWorkflow` contract

Core interface:

```python
from areal.api.workflow_api import RolloutWorkflow

class MyWorkflow(RolloutWorkflow):
    async def arun_episode(self, engine, data: dict):
        ...
```

Accepted return types:

| Return type | Meaning |
|---|---|
| `dict[str, torch.Tensor]` | Direct training tensor dictionary. |
| `dict[str, InteractionWithTokenLogpReward]` | Token-level agent interactions, exported by AReaL OpenAI integration. |
| `None` | Reject this trajectory; it is excluded from training. |

Standard tensor dictionary fields:

| Field | Shape | Required | Meaning |
|---|---:|---:|---|
| `input_ids` | `[batch, seq]` | yes | Prompt plus completion tokens. |
| `attention_mask` | `[batch, seq]` | yes | Valid-token mask. |
| `loss_mask` | `[batch, seq]` | usually | `1` for generated tokens to train on; `0` for prompt/tool context. |
| `logprobs` | `[batch, seq]` | usually | Per-token rollout logprobs; prompt positions usually `0.0`. |
| `rewards` | `[batch]` | RL | Per-sequence reward. |
| `versions` | `[batch, seq]` | async RL | Weight version per generated token; prompt positions often `-1`. |
| `multi_modal_input` | list/dict | VLM | Processor outputs such as `pixel_values`, `image_grid_thw`. |
| `mm_token_type_ids` | `[batch, seq]` | VLM-dependent | VLM token type IDs when supplied by the processor. |

Minimal custom workflow skeleton:

```python
import uuid
import torch
from areal.api import ModelRequest, RolloutWorkflow

class MyWorkflow(RolloutWorkflow):
    def __init__(self, tokenizer, gconfig, reward_fn):
        self.tokenizer = tokenizer
        self.gconfig = gconfig.new_with_stop_and_pad_token_ids(tokenizer)
        self.reward_fn = reward_fn

    async def arun_episode(self, engine, data):
        input_ids = self.tokenizer.apply_chat_template(
            data["messages"], tokenize=True, add_generation_prompt=True
        )
        req = ModelRequest(
            rid=uuid.uuid4().hex,
            input_ids=input_ids,
            gconfig=self.gconfig.new(n_samples=1),
            tokenizer=self.tokenizer,
        )
        resp = await engine.agenerate(req)
        reward = float(self.reward_fn(
            self.tokenizer.decode(input_ids),
            self.tokenizer.decode(resp.output_tokens),
            resp.input_tokens,
            resp.output_tokens,
            **data,
        ))
        seq = resp.input_tokens + resp.output_tokens
        loss_mask = [0] * resp.input_len + [1] * resp.output_len
        return {
            "input_ids": torch.tensor([seq], dtype=torch.int32),
            "attention_mask": torch.ones(1, len(seq), dtype=torch.bool),
            "loss_mask": torch.tensor([loss_mask], dtype=torch.int32),
            "logprobs": torch.tensor([[0.0] * resp.input_len + resp.output_logprobs], dtype=torch.float32),
            "versions": torch.tensor([[-1] * resp.input_len + resp.output_versions], dtype=torch.int32),
            "rewards": torch.tensor([reward], dtype=torch.float32),
        }
```

## 6. Stock RLVR workflows

### `RLVRWorkflow`

Constructor shape:

```python
from areal.workflow.rlvr import RLVRWorkflow

RLVRWorkflow(
    reward_fn,                 # callable or dotted import path
    gconfig,                   # GenerationHyperparameters
    tokenizer,                 # tokenizer object or tokenizer path
    enable_thinking=False,
    get_input_ids_fn=...,      # optional callable or import path
    data_extract_prompt_fn=...,# optional callable or import path
)
```

Default behavior:

- Extracts prompt from `data["messages"]`.
- Applies chat template with `add_generation_prompt=True`.
- Calls `engine.agenerate()` with `n_samples=1`; grouped rollout is handled outside by the trainer/controller.
- Decodes completion and calls the reward with `prompt`, `completions`, token IDs, and all dataset fields.
- Returns a one-row tensor dictionary.

### `VisionRLVRWorkflow`

Constructor shape:

```python
from areal.workflow.vision_rlvr import VisionRLVRWorkflow

VisionRLVRWorkflow(
    reward_fn,
    gconfig,
    tokenizer,
    processor,
    enable_thinking=False,
)
```

Default behavior:

- Processes `data["messages"]` and `data["images"]` with the VLM processor.
- Passes base64 image data into `ModelRequest.image_data`.
- If present, passes `data["messages_chat"]` for vLLM VLM request formatting.
- Includes VLM processor outputs in `multi_modal_input` and may include `mm_token_type_ids`.

## 7. Grouped rollout and reward normalization

AReaL uses `gconfig.n_samples` as the rollout group size for RL trainers. When `group_size > 1`, the workflow runs multiple times for the same input prompt and merges valid results.

Rules:

- Tensor-dict workflows are padded/concatenated along batch dimension.
- Agent interaction dicts are merged by completion/response ID.
- `None` rejects a trajectory. If all group entries are `None`, the whole prompt is rejected.
- `gconfig.drop_incomplete_group=True` discards the entire group if any member fails.
- `gconfig.reward_normalization=True` normalizes one scalar reward per group member and requires a complete group. It is intended for interaction-dict workflows and is not a substitute for training-time reward normalization.

## 8. Safe validation commands

Validate a sample JSON file only:

```bash
python scripts/check_workflow_contract.py \
  --sample-json sample.json \
  --mode rlvr \
  --require answer
```

Validate import paths without instantiating workflows or calling rewards:

```bash
python scripts/check_workflow_contract.py \
  --workflow my_package.workflows.MyWorkflow \
  --reward my_package.rewards.my_reward \
  --sample-json sample.json \
  --mode rlvr
```

Explicitly execute a reward function on a sample only when the user accepts arbitrary code execution in that import path:

```bash
python scripts/check_workflow_contract.py \
  --reward my_package.rewards.my_reward \
  --sample-json sample.json \
  --mode rlvr \
  --execute-reward \
  --completion "The answer is \\boxed{4}."
```
