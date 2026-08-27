# Qwen-VL inference workflows

This reference gives task-level recipes for direct inference. It assumes the user has accepted any model download/licensing/network cost before running code. For exact API details, see [api-reference.md](api-reference.md); for failures, see [troubleshooting.md](troubleshooting.md).

## 1. Choose the right model and call style

| User intent | Recommended model ID | Main call | Notes |
| --- | --- | --- | --- |
| Multimodal assistant, VQA, Chinese/English chat, multi-turn history, grounding by instruction | `Qwen/Qwen-VL-Chat` | `model.chat(tokenizer, query=..., history=...)` | Default choice for novice inference tasks. |
| Lower-memory chat inference when AutoGPTQ/optimum stack is available | `Qwen/Qwen-VL-Chat-Int4` | `model.chat(...)` | Same chat interface; optional quantization extras are required. |
| Pretrained base model captioning or generation experiments | `Qwen/Qwen-VL` | `model.generate(...)` | Not an aligned assistant; do not expect ChatML-style instruction following. |
| Public hosted products such as Qwen-VL-Plus/Max | Not this local sub-skill | Provider/API route | These are not the local repository checkpoint workflow covered here. |

## 2. Transformers chat workflow

Use this for ordinary multimodal chat and grounding.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig

model_id = "Qwen/Qwen-VL-Chat"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="cuda",          # or "auto" / "cpu"
    trust_remote_code=True,
).eval()
model.generation_config = GenerationConfig.from_pretrained(
    model_id,
    trust_remote_code=True,
)

query = tokenizer.from_list_format([
    {"image": "image.jpg"},
    {"text": "What is in this image?"},
])
response, history = model.chat(tokenizer, query=query, history=None)
print(response)
```

Operational notes:

- `trust_remote_code=True` is required for Qwen-VL tokenizer/model methods such as `from_list_format`, `chat`, and box rendering.
- The image value can be a local file path or a URL. Prefer user-supplied images; do not assume example assets exist.
- Keep the returned `history` for follow-up questions about the same image.
- If reproducibility matters, set `torch.manual_seed(seed)` before generation, but expect hardware and library differences to affect outputs.

## 3. Multi-turn and multi-image prompts

Qwen-VL-Chat supports history and multiple images in one query.

```python
query = tokenizer.from_list_format([
    {"image": "city_a.jpg"},
    {"image": "city_b.jpg"},
    {"text": "Compare these two city skyline images."},
])
response, history = model.chat(tokenizer, query=query, history=None)

follow_up = tokenizer.from_list_format([
    {"text": "Which image has more visible high-rise buildings?"},
])
response, history = model.chat(tokenizer, query=follow_up, history=history)
```

Use `history=None` for the first turn. Pass the current `history` for subsequent turns so the model can refer back to previously supplied images.

## 4. Grounding and bounding-box rendering

The chat model can answer with markup such as:

```xml
<ref>high five</ref><box>(536,509),(588,602)</box>
```

To request grounding, ask explicitly for boxes or regions:

```python
response, history = model.chat(
    tokenizer,
    query="Frame the person holding the cup.",
    history=history,
)
image = tokenizer.draw_bbox_on_latest_picture(response, history)
if image is not None:
    image.save("boxed_output.jpg")
```

Rendering rules:

- For chat: pass both `response` and `history` to `draw_bbox_on_latest_picture`.
- For base-model generation: pass only `response` unless you have a compatible history object.
- If rendering returns `None`, the response likely contains no valid `<box>` markup or no latest image is available in history.
- Preserve raw markup when coordinates matter. Clean it only for plain-language output; see [api-reference.md](api-reference.md).

## 5. Base-model generation workflow

Use `Qwen/Qwen-VL` when the user specifically asks for the pretrained base model or wants to inspect non-chat generation behavior.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen-VL"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="cuda",
    trust_remote_code=True,
).eval()

query = tokenizer.from_list_format([
    {"image": "image.jpg"},
    {"text": "Generate the caption in English with grounding:"},
])
inputs = tokenizer(query, return_tensors="pt").to(model.device)
pred = model.generate(**inputs)
response = tokenizer.decode(pred.cpu()[0], skip_special_tokens=False)
print(response)

boxed = tokenizer.draw_bbox_on_latest_picture(response)
if boxed is not None:
    boxed.save("base_boxes.jpg")
```

Do not diagnose weak instruction-following in `Qwen/Qwen-VL` as a generic model failure until checking whether the user intended `Qwen/Qwen-VL-Chat`.

## 6. ModelScope fallback workflow

When Hugging Face downloads are blocked or a user prefers ModelScope, download a snapshot and then load the local directory with the same Qwen remote code:

```python
from modelscope import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

model_dir = snapshot_download("qwen/Qwen-VL-Chat")
tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_dir,
    device_map="cuda",
    trust_remote_code=True,
).eval()
```

If using ModelScope's compatibility classes, keep the same semantics: snapshot first, load from the snapshot directory, and still enable `trust_remote_code=True` because the Qwen-VL custom code is not plain upstream Transformers.

## 7. Device and precision choices

- `device_map="cuda"`: direct CUDA placement; good for a single visible GPU when memory is sufficient.
- `device_map="auto"`: let Accelerate partition/place weights; useful for multi-GPU or mixed placement.
- `device_map="cpu"`: functional CPU fallback; expect slow startup and generation.
- `bf16=True`: good on Ampere/Hopper-class GPUs when supported.
- `fp16=True`: common CUDA half-precision fallback and required by the Q-LoRA path in the training workflow.
- Avoid combining quantized Int4 assumptions with a non-quantized model ID. `Qwen/Qwen-VL-Chat-Int4` is the released chat Int4 checkpoint.

## 8. Use the bundled helper

The bundled helper wraps the chat/base workflows without hard-coded example assets:

```bash
python scripts/qwen_vl_chat_example.py \
  --model-id Qwen/Qwen-VL-Chat \
  --image image.jpg \
  --prompt "What is visible in the picture?" \
  --device-map cuda
```

For base-model generation:

```bash
python scripts/qwen_vl_chat_example.py \
  --mode base \
  --model-id Qwen/Qwen-VL \
  --image image.jpg \
  --prompt "Generate the caption in English with grounding:" \
  --output-image boxes.jpg
```

For ModelScope snapshot loading:

```bash
python scripts/qwen_vl_chat_example.py \
  --source modelscope \
  --model-id qwen/Qwen-VL-Chat \
  --image image.jpg \
  --prompt "Describe this image" \
  --device-map auto
```
