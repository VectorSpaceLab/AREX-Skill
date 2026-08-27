# InternVideo2.5 and InternVideo3 inference

This reference distills the release READMEs and quickstart snippets into self-contained operating guidance for future Researchers.

## Choose the model family

| Need | Prefer | Why |
|---|---|---|
| Open 8B long-video chat with compact visual tokens and strong short/long video benchmarks | InternVideo2.5 (`OpenGVLab/InternVideo2_5_Chat_8B`) | Built on InternVL2.5 with long and rich context (LRC) modeling and HiCo-style adaptive hierarchical token compression. The released 8B model reports 16 tokens per frame. |
| Compare HiCo token budgets independently of the full InternVideo2.5 chat model | InternVL2.5 + HiCo (`OpenGVLab/InternVL_2_5_HiCo_R16` or `..._R64`) | R16 and R64 variants trade visual detail for token count; R64 has a larger per-frame visual token budget. |
| InternVideo3-style long-horizon reasoning, MCR/M2LA, image/video/text chat, or agentic-video exploration planning | InternVideo3 (`yanziang/InternVideo3-8B-Instruct`) | Release describes Multimodal Contextual Reasoning (MCR), M2LA KV-cache compression, long-video training, and tool-interaction concepts. |

Use InternVideo2.5 for LRC/HiCo model-selection questions; use InternVideo3 when the task mentions MCR, M2LA, on-policy distillation, InternVideo3 SFT, or the InternVideo3 benchmark/evaluation suite.

## Minimal InternVideo3 loading checklist

Required user inputs:

- `<model-id-or-dir>`: a Hugging Face id or local checkpoint directory for the model.
- Optional `<processor-id-or-dir>`: default to the same value as the model unless the user split tokenizer/processor assets.
- CUDA GPU with enough memory for 8B bfloat16 inference; CPU-only use is not a realistic performance target.
- Python packages: `torch`, `transformers` at the 4.57.x generation used by the repo, and `qwen-vl-utils` for video/image preprocessing helpers.

The README quickstart loads InternVideo3 with `AutoModelForCausalLM`, bfloat16, `device_map="auto"`, `attn_implementation="sdpa"`, and `trust_remote_code=True`. Evaluation scripts usually switch to `attn_implementation=flash_attention_2`; only use that when FlashAttention is installed and compatible with the active CUDA/PyTorch stack.

```python
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

model_id = "<model-id-or-dir>"

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.bfloat16,
    attn_implementation="sdpa",  # use "flash_attention_2" only after verifying FlashAttention
    device_map="auto",
    trust_remote_code=True,
)
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
```

## Hugging Face processor message shapes

### Text-only conversation

```python
messages = [
    {
        "role": "user",
        "content": [{"type": "text", "text": "Please introduce yourself."}],
    }
]
```

### Image understanding

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "<image-file>"},
            {"type": "text", "text": "Describe this image in detail."},
        ],
    }
]
```

### Video understanding

```python
fps = 4
min_pixels = 128 * 2 * 32 * 32
max_pixels = 256 * 2 * 32 * 32

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "video",
                "video": "<video-file>",
                "fps": fps,
                "min_pixels": min_pixels,
                "max_pixels": max_pixels,
            },
            {"type": "text", "text": "Describe this video in detail."},
        ],
    }
]
```

Generation pattern:

```python
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt",
    # Include fps=fps for video prompts when using the README-style video template.
).to(model.device)

output = model.generate(**inputs, max_new_tokens=1024, use_cache=True)
generated_ids = [out[len(inp):] for inp, out in zip(inputs.input_ids, output)]
response = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(response)
```

## Pixel/frame budget guidance

- Start with the README video defaults (`fps=4`, moderate `min_pixels`/`max_pixels`) for a single short video.
- For long videos, reduce one dimension at a time: `fps`, `max_num_frames` when an evaluation harness supports it, then `max_pixels`.
- The InternVideo3 evaluation suite often uses `fps=4`, `min_pixels=max_pixels=256*32*32`, and benchmark-specific `max_num_frames` from 128 to 2048.
- M2LA is a cache-compression method described for long-context decoding; it does not remove the need to budget prefill memory, visual tokens, and video decode time.

## InternVideo3 concepts to preserve in task outputs

- **MCR (Multimodal Contextual Reasoning):** model behavior is framed as iterative observation, reasoning, action/tool use, feedback, memory update, and verification. If the user asks for an agentic workflow, separate the model call from external tools such as ASR, segmentation, search, temporal grounding, summarization, and verification.
- **M2LA:** compresses cached KV states while preserving the multimodal token stream. It is an efficiency mechanism for long rollouts; it should not be presented as a data preprocessing step.
- **Long-video training recipe:** continued pretraining after M2LA conversion, short-to-long SFT, rule-based RL, and on-policy distillation. The bundled SFT code evidence covers CPT/short/long SFT configs; treat RL/distillation implementation details as not fully covered by the inspected training files.

## SFT JSONL is a different schema

For InternVideo3 SFT annotations, do not use the Hugging Face `type: "video"` shape above. SFT JSONL records use OpenAI-like chat records with content items such as:

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "video_url",
          "video_url": {
            "url": "relative/video.mp4",
            "image_wh": [1920, 1080],
            "origin_video_length": 3600,
            "origin_fps": 30.0
          }
        },
        {"type": "text", "text": "<VIDEO_CONTEXT> What happens after the vehicle stops?"}
      ]
    },
    {"role": "assistant", "content": "The answer should be grounded in the sampled frames."}
  ]
}
```

Use the sibling `datasets` sub-skill and its validator before constructing SFT runs.
