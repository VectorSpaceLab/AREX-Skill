# XTuner data formats

This reference summarizes the dataset record shapes that XTuner V1 data loading and tokenization expect. Use the bundled validator before handing data to training or RL.

## Common JSONL rules

- One JSON value per line; blank or partially written lines are invalid.
- Use UTF-8 JSON. Keep newline characters inside JSON strings escaped as `\n`.
- XTuner only reads JSONL data for these flows. Directory inputs are expanded to contained `.jsonl` files by the training argument layer.
- Dataset samples are parsed line-by-line, so a single bad line can stop preprocessing or be converted to a fake multimodal sample depending on dataset class.

## SFT OpenAI messages

XTuner SFT supports OpenAI-style messages. A JSONL line may be either a bare list of messages or an object with `messages` or `dialogs`:

```json
[{"role":"user","content":"Give three tips."},{"role":"assistant","content":"Eat well, exercise, and sleep."}]
{"messages":[{"role":"system","content":"Be concise."},{"role":"user","content":"What are primary colors?"},{"role":"assistant","content":"Red, blue, and yellow."}]}
```

Supported message roles for OpenAI tokenization include `system`, `developer`, `user`, `assistant`, `tool`, and `pretrain`. `assistant` and `pretrain` content contributes to labels by default; `system`, `developer`, `user`, and `tool` are masked unless template-specific logic changes that. A message can set `loss: false` to suppress assistant supervision when the selected template supports that path.

Common role/content variants:

| Variant | Meaning | Recommended action |
|---|---|---|
| `{"from":"human","value":"..."}` | user message in legacy conversation exports | Normalize to `{"role":"user","content":"..."}` when possible. |
| `{"from":"gpt","value":"..."}` | assistant message in legacy conversation exports | Normalize to `{"role":"assistant","content":"..."}`. |
| `{"from":"assistant","value":"..."}` | assistant role using value field | Accepted by the validator as a variant; prefer `role`/`content` for strict OpenAI tokenization. |
| `reasoning_content` / `thinking` | reasoning text for reasoning templates | `thinking` is only valid on assistant messages. GPT-OSS keeps only the last assistant thinking field by default. |

## MLLM SFT and pretraining records

Use an object with `messages`; `id` is optional. Multimodal records should use `DatasetConfig(class_name="VLMJsonlDataset", media_root="...")` so media paths are passed to the multimodal tokenizer.

### Old OpenAI media style

```json
{"id":1,"messages":[{"role":"user","content":[{"type":"image_url","image_url":{"url":"images/dog.jpg","image_wh":[375,500]}},{"type":"text","text":"<IMG_CONTEXT> What color is the dog?"}]},{"role":"assistant","content":"Brown."}]}
```

For video, replace `image_url` with `video_url` and provide `video_url.url`. Optional video metadata includes `image_wh`, `origin_video_length`, `origin_fps`, `processed_video_length`, `processed_fps`, and `frames_timestamp`.

### New media style

```json
{"messages":[{"role":"user","content":[{"type":"image","image":{"url":"images/dog.jpg","image_wh":[375,500]}},{"type":"text","text":"What color is the dog?"}]},{"role":"assistant","content":"Brown."}]}
{"messages":[{"role":"user","content":[{"type":"video","video":{"url":"videos/clip.mp4","image_wh":[1280,720]}},{"type":"text","text":"Describe the video."}]},{"role":"assistant","content":"People are playing tennis."}]}
```

### HF-style path item

Some fixtures use `{"type":"video","path":"clip.mp4"}` or `{"type":"image","path":"image.jpg"}`. Treat these as local media references and validate them against the intended `media_root`.

### Multimodal pretraining

Pretraining uses a single `pretrain` message and content can be a mixed list of media and text items:

```json
{"messages":[{"role":"pretrain","content":[{"type":"image","image":{"url":"images/a.jpg","image_wh":[640,480]}},{"type":"text","text":"A caption or interleaved text."}]}]}
```

For old-style InternVL/Intern-S1 prompts, `<IMG_CONTEXT>` and `<VIDEO_CONTEXT>` placeholders may appear in text. Newer Qwen VL-style records can omit those placeholders because the tokenizer inserts vision tokens from content items.

## RL / GSM8K reward records

RL text data is converted into rollout state from the `prompt` field. For GSM8K-style rule reward, `reward_model.ground_truth` is required.

```json
{
  "data_source": "openai/gsm8k",
  "prompt": [
    {"role": "user", "content": "Natalia sold clips ... Let's think step by step and output the final answer after \"####\"."}
  ],
  "ability": "math",
  "reward_model": {"style": "rule", "ground_truth": "72"},
  "extra_info": {
    "split": "train",
    "index": 0,
    "answer": "...\n#### 72",
    "question": "Natalia sold clips ..."
  }
}
```

Tool-agent GSM8K records can add a system prompt and `extra_info.tools_kwargs.calc_gsm8k_reward.create_kwargs.ground_truth`. Keep `reward_model.ground_truth` present even when tool metadata is present.

## DatasetConfig snippets

SFT text:

```python
from xtuner.v1.datasets.config import DatasetConfig
from xtuner.v1.datasets.sft_tokenize_fn import OpenaiTokenizeFunctionConfig

datasets = [
    {
        "dataset": DatasetConfig(
            name="sft",
            anno_path="data/openai_sft.jsonl",
            cache_dir="work_dir/dataset_cache",
            cache_tag="sft-v1",
        ),
        "tokenize_fn": OpenaiTokenizeFunctionConfig(chat_template="qwen3", max_length=4096),
    }
]
```

MLLM:

```python
from xtuner.v1.datasets.config import DatasetConfig

datasets = [
    {
        "dataset": DatasetConfig(
            name="vlm",
            anno_path="data/mllm.jsonl",
            class_name="VLMJsonlDataset",
            media_root="media",
            cache_dir="work_dir/vlm_cache",
            cache_tag="vlm-v1",
        ),
        "tokenize_fn": ...,  # model-specific MLLM tokenize config
    }
]
```

RL text:

```python
from xtuner.v1.datasets.config import DatasetConfig, DataloaderConfig
from xtuner.v1.datasets.rl_tokenize_fn import RLTextTokenizeFnConfig

dataset_cfg = [
    {
        "dataset": DatasetConfig(name="gsm8k", anno_path="data/gsm8k/train.jsonl"),
        "tokenize_fn": RLTextTokenizeFnConfig(max_length=1024),
    }
]
dataloader_cfg = DataloaderConfig(dataset_config_list=dataset_cfg, pack_level="none", group_by_length=False)
```

## Validator commands

```bash
python ./scripts/validate_xtuner_jsonl.py data/openai_sft.jsonl --mode sft
python ./scripts/validate_xtuner_jsonl.py data/mllm.jsonl --mode mllm --media-root media
python ./scripts/validate_xtuner_jsonl.py data/gsm8k/train.jsonl --mode rl
```

Use `--max-length N` for a tokenizer-free approximate truncation warning, then confirm with the real tokenizer in the training or RL workflow.
