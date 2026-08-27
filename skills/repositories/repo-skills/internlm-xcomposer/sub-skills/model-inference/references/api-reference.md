# InternLM-XComposer Inference API Reference

This reference distills the model-loading and method-call facts needed to plan InternLM-XComposer inference without reopening the source repository or loading checkpoints. Treat every snippet as a user-edited example for a prepared runtime.

## Model family routing

| Target | Typical model id or path | Main backend | Use for | Notes |
| --- | --- | --- | --- | --- |
| InternLM-XComposer2.5 | `internlm/internlm-xcomposer2d5-7b` or a local equivalent | Transformers or LMDeploy | image/video understanding, multi-image chat, webpage and article composition | Current root README examples use `AutoModel`/`AutoTokenizer` with `trust_remote_code=True`, CUDA autocast, `model.chat(...)`, and composition methods. |
| InternLM-XComposer2.5 4-bit | `internlm/internlm-xcomposer2d5-7b-4bit` | LMDeploy AWQ | lower-memory accelerated inference | Source 4-bit examples use `TurbomindEngineConfig(model_format="awq", cache_max_entry_count=0.1)` and LMDeploy `pipeline`. |
| InternLM-XComposer2 4KHD/VL | `internlm/internlm-xcomposer2-4khd-7b`, `internlm/internlm-xcomposer2-vl-7b`, 1.8B variants, and 4-bit variants | Transformers, legacy LMDeploy docs, or legacy examples | legacy 2.0 chat, 4KHD, VL benchmarks, older Gradio demos | 2.0 examples use `model.chat(tokenizer, query=..., image=..., hd_num=55, history=..., do_sample=False, num_beams=3)` for 4KHD. |
| InternLM-XComposer 1.0 | `internlm/internlm-xcomposer-7b`, `internlm/internlm-xcomposer-vl-7b`, 4-bit GPTQ variant | Transformers/AutoGPTQ legacy code | legacy text-image composition and chat | 1.0 examples expose `model.generate(text[, image])` plus `model.chat(text=..., image=..., history=...)`; 4-bit uses an `AutoGPTQ` subclass, not LMDeploy AWQ. |
| OmniLive base | local `.../internlm-xcomposer2d5-ol-7b/base` | Transformers | OmniLive base VLM smoke checks only | Route audio, memory/video, and online OmniLive services to sibling `omnilive`; generic 2.5 inference can use this API shape. |

## Current 2.5 Transformers load shape

Source quickstarts follow this shape:

```python
import torch
from transformers import AutoModel, AutoTokenizer

torch.set_grad_enabled(False)
model_id = "internlm/internlm-xcomposer2d5-7b"
model = AutoModel.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
).cuda().eval().half()
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model.tokenizer = tokenizer
```

Operational notes:

- `trust_remote_code=True` is required for repository-defined methods such as `chat`, `write_webpage`, `resume_2_webpage`, `screen_2_webpage`, and `write_artical`.
- Use `AutoModel` for current 2.5 quickstarts. Gradio scripts use `AutoModelForCausalLM` because their UI code directly calls lower-level generation paths.
- Choose one execution dtype deliberately. The README chain `torch_dtype=torch.bfloat16` plus `.half()` is source evidence, but in a real runtime prefer bf16 on supported GPUs or fp16 on common CUDA cards.
- Set `model.tokenizer = tokenizer` before calling methods that rely on the model-stored tokenizer.

## `chat` API

Observed signature from the current 2.5 model code:

```python
response, history = model.chat(
    tokenizer,
    query: str,
    image=[],
    hd_num: int = 24,
    history=[],
    streamer=None,
    max_new_tokens: int = 1024,
    do_sample: bool = True,
    num_beams: int = 1,
    temperature: float = 1.0,
    top_p: float = 0.8,
    repetition_penalty: float = 1.005,
    infer_mode: str = "base",
    use_meta: bool = False,
    meta_instruction="...",
)
```

Return value: `(response: str, history: list[(query, response)])`.

Input conventions:

- `image` may be `None`, an empty list, or a list of image/video paths for current 2.5 snippets.
- If exactly one image/video is provided and the prompt has no `<ImageHere>` placeholder, the model code prepends an image placeholder internally.
- If multiple images are provided, put one `<ImageHere>` placeholder for each image and make the prompt explicit, e.g. `Image1 <ImageHere>; Image2 <ImageHere>; compare them`. The source code only prints a warning when placeholder count mismatches; plans should reject or fix the mismatch before execution.
- Current 2.5 code reduces effective high-definition tiling for multiple images. Use a smaller `hd_num` for many images when VRAM is tight; use a higher `hd_num` only for high-resolution single-image/document analysis.
- For video understanding, current examples pass a video file path inside the `image` list. Require Decord, working video codecs, and enough VRAM.
- `use_meta=True` enables the built-in InternLM-XComposer assistant meta prompt used by source quickstarts.

Common calls:

```python
# High-resolution image understanding
response, history = model.chat(tokenizer, "Analyze the image in detail", ["/data/dubai.png"], do_sample=False, num_beams=3, use_meta=True)

# Video understanding
response, history = model.chat(tokenizer, "Here are some frames of a video. Describe this video in detail", ["/data/liuxiang.mp4"], do_sample=False, num_beams=3, use_meta=True)

# Multi-image dialogue
query = "Image1 <ImageHere>; Image2 <ImageHere>; Image3 <ImageHere>; compare the cars"
images = ["cars1.jpg", "cars2.jpg", "cars3.jpg"]
response, history = model.chat(tokenizer, query, images, do_sample=False, num_beams=3, use_meta=True)
```

## Webpage and article composition APIs

These methods are documented in current 2.5 examples and implemented in the 2.5 model code. Spell the method names exactly.

### `write_webpage`

```python
html = model.write_webpage(
    inst: str,
    image=[],
    max_new_tokens=4800,
    do_sample=True,
    num_beams=2,
    temperature=1.0,
    repetition_penalty=3.0,
    seed=-1,
    use_meta=False,
    task="Instruction-aware Webpage Generation",
)
```

- Use for instruction-to-webpage generation.
- It writes `task.replace(" ", "_") + ".html"` in the current working directory and returns the generated HTML string.
- The implementation rewrites Unsplash random image URLs to `picsum.photos` placeholders by default.

### `resume_2_webpage`

```python
html = model.resume_2_webpage(
    inst="/path/to/resume.md",
    image=[],
    max_new_tokens=4800,
    do_sample=True,
    num_beams=2,
    temperature=1.0,
    repetition_penalty=3.0,
    seed=202,
    task="Resume-to-Personal Page",
)
```

- `inst` is a path to a resume in Markdown format. Validate the file before execution; source code prints a warning on read failure but can continue unsafely.
- The method generates HTML, then a second pass of JavaScript events, and inserts the JS into the HTML when possible.
- It writes `Resume-to-Personal_Page.html` by default and returns the final HTML string.

### `screen_2_webpage`

```python
html = model.screen_2_webpage(
    inst="Generate the HTML code of this web image with Tailwind CSS.",
    image=["/path/to/screenshot.jpg"],
    max_new_tokens=4800,
    do_sample=True,
    num_beams=2,
    temperature=1.0,
    repetition_penalty=3.0,
    seed=202,
    task="Screenshot-to-Webpage",
)
```

- Requires at least one image. If no image is provided, the method prints `No image is provided, skip` and returns an empty string.
- The implementation overwrites `inst` with the fixed Tailwind CSS screenshot-to-webpage prompt.
- It writes `Screenshot-to-Webpage.html` by default.

### `write_artical`

```python
article = model.write_artical(
    inst: str,
    image=[],
    hd_num=25,
    history=[],
    max_new_tokens=1024,
    do_sample=True,
    num_beams=1,
    temperature=1.0,
    top_p=0.8,
    repetition_penalty=1.005,
    max_length=8192,
    seed=8192,
    use_meta=False,
)
```

- The method name is misspelled as `write_artical` in source. Use that exact name.
- It returns generated article text. The root README examples print the returned Chinese essay/blog text rather than showing a default file write.
- If `history` is passed, the method prints that only `chat` supports multi-round history and ignores history in article mode.

## LMDeploy and AWQ API shape

The current 2.5 README and 4-bit examples use LMDeploy for accelerated VLM inference:

```python
from lmdeploy import pipeline
from lmdeploy.vl import load_image

pipe = pipeline("internlm/internlm-xcomposer2d5-7b")
image = load_image("examples/dubai.png")
response = pipe(("describe this image", image))
print(response.text)
```

For the 4-bit AWQ model:

```python
from lmdeploy import TurbomindEngineConfig, pipeline
from lmdeploy.vl import load_image

engine_config = TurbomindEngineConfig(model_format="awq", cache_max_entry_count=0.1)
pipe = pipeline("internlm/internlm-xcomposer2d5-7b-4bit", backend_config=engine_config)
image = load_image("examples/dubai.png")
response = pipe(("describe this image", image))
print(response.text)
```

Operational notes:

- Install `lmdeploy`; repo install notes say the default package depends on CUDA 12.x and CUDA 11.x needs the LMDeploy installation guide.
- `cache_max_entry_count` lowers KV-cache memory at the cost of capacity/performance.
- Use AWQ only with the corresponding 4-bit checkpoint.
- LMDeploy is the documented 2.5 4-bit/AWQ path. Legacy 1.0 4-bit used AutoGPTQ and is not interchangeable with current AWQ snippets.

## Multi-GPU Transformers dispatch

Current and legacy examples import `accelerate.dispatch_model` and a repo utility named `auto_configure_device_map(num_gpus)`:

```python
from accelerate import dispatch_model

device_map = auto_configure_device_map(num_gpus)
model = dispatch_model(model, device_map=device_map)
```

Planning constraints:

- Install `accelerate` before execution.
- Do not call `.cuda()` after `dispatch_model`.
- Verify module names for the selected family. Current 2.5 uses keys like `vit`, `vision_proj`, `model.layers.N`, `output`; legacy 2.0/1.0 use keys like `visual_encoder`, `Qformer`, `internlm_model.model.layers.N`.

## Legacy compatibility notes

### InternLM-XComposer2 / 2.0

Typical 2.0 image-chat snippet:

```python
model = AutoModel.from_pretrained("internlm/internlm-xcomposer2-vl-7b", trust_remote_code=True).eval()
model.half().cuda()
tokenizer = AutoTokenizer.from_pretrained("internlm/internlm-xcomposer2-vl-7b", trust_remote_code=True)
text = "<ImageHere>Please describe this image in detail."
image = "examples/image1.webp"
response, history = model.chat(tokenizer, query=text, image=image, history=[], do_sample=False)
```

2.0 4KHD examples add `hd_num=55`, `num_beams=3`, and pass image paths.

### InternLM-XComposer 1.0

Typical 1.0 snippets:

```python
model = AutoModel.from_pretrained("internlm/internlm-xcomposer-7b", trust_remote_code=True).cuda().eval()
tokenizer = AutoTokenizer.from_pretrained("internlm/internlm-xcomposer-7b", trust_remote_code=True)
model.tokenizer = tokenizer

response = model.generate("Please introduce Einstein", "examples/images/aiyinsitan.jpg")
response, history = model.chat(text="Who is in the picture?", image="examples/images/aiyinsitan.jpg", history=None)
response, history = model.chat(text="What did he achieve?", image=None, history=history)
```
