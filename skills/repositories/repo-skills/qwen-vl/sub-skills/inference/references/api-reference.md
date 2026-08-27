# Inference API reference

Use this as a quick lookup for Qwen-VL local inference APIs. For full task recipes, see [workflows.md](workflows.md).

## Dependency baseline

Documented base inference packages include:

- `transformers==4.32.0`
- `accelerate`
- `tiktoken`
- `einops`
- `transformers_stream_generator==0.0.4`
- `scipy`
- `torchvision`
- `pillow`
- `tensorboard`
- `matplotlib`

For CUDA users, PyTorch 2.x and CUDA 11.4+ are recommended. CPU can load the code path, but practical inference is slow.

Optional Int4 inference extras:

- `optimum`
- an AutoGPTQ build/wheel compatible with the host CUDA/PyTorch stack

The verified construction environment did not install AutoGPTQ/optimum, so treat Int4 execution as an optional, separately prepared path.

## Model IDs and capabilities

| Model ID | Provider form | Capability | Primary API | Caveat |
| --- | --- | --- | --- | --- |
| `Qwen/Qwen-VL` | Hugging Face | Pretrained vision-language base model | `model.generate(...)` | Not aligned for assistant-style chat. |
| `Qwen/Qwen-VL-Chat` | Hugging Face | Aligned multimodal assistant | `model.chat(...)` | Default for chat/VQA/grounding. |
| `Qwen/Qwen-VL-Chat-Int4` | Hugging Face | Int4 quantized chat model | `model.chat(...)` | Requires AutoGPTQ/optimum-compatible stack. |
| `qwen/Qwen-VL` | ModelScope | Snapshot mirror of base model | Load snapshot, then Transformers/ModelScope classes | Use `trust_remote_code=True`. |
| `qwen/Qwen-VL-Chat` | ModelScope | Snapshot mirror of chat model | Load snapshot, then `model.chat(...)` | Use `trust_remote_code=True`. |
| `qwen/Qwen-VL-Chat-Int4` | ModelScope | Snapshot mirror of Int4 chat model | Load snapshot, then `model.chat(...)` | Optional quantization stack. |

## Loading with Transformers

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig

model_id = "Qwen/Qwen-VL-Chat"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="cuda",       # "cuda", "auto", or "cpu"
    trust_remote_code=True,
).eval()
model.generation_config = GenerationConfig.from_pretrained(
    model_id,
    trust_remote_code=True,
)
```

Precision flags supported by the Qwen-VL custom loader examples:

```python
AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", trust_remote_code=True, bf16=True)
AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", trust_remote_code=True, fp16=True)
AutoModelForCausalLM.from_pretrained(model_id, device_map="cpu", trust_remote_code=True)
```

## Loading through ModelScope snapshots

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

If `tokenizer.model_dir` is missing after a ModelScope load, set it to the snapshot directory before inference:

```python
if not hasattr(tokenizer, "model_dir"):
    tokenizer.model_dir = model_dir
```

## Multimodal input format

Preferred structured form:

```python
query = tokenizer.from_list_format([
    {"image": "image_or_url_1.jpg"},
    {"image": "image_or_url_2.jpg"},
    {"text": "Compare these two images."},
])
```

Equivalent explicit-tag form for a single image:

```python
query = "<img>image_or_url.jpg</img>What is in this image?"
```

Rules:

- Each image entry can be a local path or URL.
- Place images before text when asking about those images.
- For follow-up questions about the previous image, omit the image and pass the prior `history`.
- Use user-provided files or URLs; do not assume any demo assets are present.

## Chat API

```python
response, history = model.chat(
    tokenizer,
    query=query,
    history=None,       # first turn
)

response, history = model.chat(
    tokenizer,
    query="Frame the dog in the image.",
    history=history,    # follow-up turn
)
```

Use `Qwen/Qwen-VL-Chat` or `Qwen/Qwen-VL-Chat-Int4` for this API. If `model.chat` is missing or behavior is not instruction-following, verify that the loaded model is a chat checkpoint and that `trust_remote_code=True` was used.

## Base generation API

```python
query = tokenizer.from_list_format([
    {"image": "image.jpg"},
    {"text": "Generate the caption in English with grounding:"},
])
inputs = tokenizer(query, return_tensors="pt")
inputs = inputs.to(model.device)
pred = model.generate(**inputs)
response = tokenizer.decode(pred.cpu()[0], skip_special_tokens=False)
```

Use `Qwen/Qwen-VL` for this base-model pattern. It may echo prompt markup and special tokens; keep `skip_special_tokens=False` if you need `<img>`, `<ref>`, and `<box>` markers for grounding inspection.

## GenerationConfig and parameter overrides

Load model-specific defaults when available:

```python
from transformers.generation import GenerationConfig
model.generation_config = GenerationConfig.from_pretrained(model_id, trust_remote_code=True)
```

Common overrides for controlled runs:

```python
model.generation_config.max_new_tokens = 512
model.generation_config.do_sample = False
model.generation_config.temperature = 0.8
model.generation_config.top_p = 0.8
```

Notes:

- The official examples set a torch random seed for reproducibility, but outputs can still vary by hardware and library versions.
- For deterministic-ish behavior, set `do_sample=False` and a seed; for creative answers, set `do_sample=True` and tune `temperature`/`top_p`.
- If a newer Transformers version already loads generation config automatically, explicit assignment is still a safe way to document intended defaults.

## Grounding markup

Qwen-VL responses can contain XML-like grounding tags:

```xml
<ref>object name</ref><box>(x1,y1),(x2,y2)</box>
```

The tutorial also anticipates optional quadrilateral tags:

```xml
<quad>(x1,y1),(x2,y2),(x3,y3),(x4,y4)</quad>
```

Interpretation:

- `<ref>...</ref>` names the object/region.
- `<box>(x1,y1),(x2,y2)</box>` gives a rectangular region.
- Coordinates are model output markup intended for Qwen-VL's tokenizer renderer; do not silently reinterpret them without checking the displayed result.

## Drawing boxes

Chat response:

```python
image = tokenizer.draw_bbox_on_latest_picture(response, history)
if image is not None:
    image.save("boxed.jpg")
```

Base-model response:

```python
image = tokenizer.draw_bbox_on_latest_picture(response)
if image is not None:
    image.save("boxed.jpg")
```

If `image` is `None`, either the model produced no valid box markup or the tokenizer could not find the latest picture context.

## Cleaning box markup for plain text

Use this only when the user wants caption text without annotations:

```python
import re

clean_response = re.sub(
    r"<ref>(.*?)</ref>(?:<box>.*?</box>)*(?:<quad>.*?</quad>)*",
    r"\1",
    response,
).strip()
```

Do not clean before box rendering; the renderer needs the original response.

## Int4 loading pattern

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen-VL-Chat-Int4"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    trust_remote_code=True,
).eval()
```

Before using this path, confirm AutoGPTQ and optimum are installed and compatible with the current PyTorch/CUDA stack. If not, switch to `Qwen/Qwen-VL-Chat` or prepare the optional quantization environment first.
