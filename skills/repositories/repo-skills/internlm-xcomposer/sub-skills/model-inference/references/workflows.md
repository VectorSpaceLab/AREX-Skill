# Model Inference Workflows

This reference turns the source README snippets and example scripts into non-executing planning recipes. Use it to choose the right backend, prompt shape, and safety checks before a user runs anything in their own environment.

## Workflow selection summary

| Need | Recommended path | Why |
| --- | --- | --- |
| Current image/video chat, high-resolution image understanding, multi-image dialogue | Transformers | Closest to the documented `chat` API and the most flexible for `history`, `hd_num`, and placeholder control. |
| Low-memory accelerated inference or serving | LMDeploy | Source README and 4-bit examples explicitly recommend LMDeploy for acceleration and AWQ. |
| Generated webpage or article output | Transformers | Current model code exposes `write_webpage`, `resume_2_webpage`, `screen_2_webpage`, and `write_artical` directly. |
| Legacy 2.0/1.0 compatibility | Transformers | The older examples use model-native `chat`/`generate` APIs and different device-map keys. |
| Gradio chat/composition demo planning | Gradio | Current demo scripts provide the UI, arguments, and launch modes; this sub-skill only plans them. |

## Safe renderer usage

The bundled helpers do not import heavy ML packages. Use them to produce a user-editable starting point or to validate prompt/placeholder structure.

```bash
python scripts/render_transformers_example.py --task chat --image /data/dubai.png --query "Analyze the image" --num-gpus 1
python scripts/render_transformers_example.py --task multi-image --image cars1.jpg --image cars2.jpg --image cars3.jpg --query "Image1 <ImageHere>; Image2 <ImageHere>; Image3 <ImageHere>; compare them" --num-gpus 2
python scripts/render_transformers_example.py --task write-webpage --query "A website for a research lab" --image logo.png --image project1.png
python scripts/render_lmdeploy_example.py --quantization awq --mode offline --image /data/dubai.png
python scripts/render_lmdeploy_example.py --quantization fp16 --mode server --tp 2 --session-len 32768
```

Renderer behavior:

- `render_transformers_example.py` validates placeholder count against image count for `--task multi-image` and renders source-shaped Python examples for chat, webpage, resume, screenshot, article, and legacy tasks.
- `render_lmdeploy_example.py` renders an LMDeploy offline-pipeline snippet or an API-server command plan for FP16 or AWQ checkpoints.
- Both helpers are stdlib-only and do not touch model weights.

## Current Transformers quickstart workflow

1. Pick the correct current model id or local checkpoint.
2. Decide whether the task is chat, video, multi-image, webpage generation, or article writing.
3. Decide the prompt format:
   - single-image chat can omit `<ImageHere>` and let the source code inject it;
   - multi-image chat should include one `<ImageHere>` placeholder per image;
   - web/article prompts are free-form instructions, but `resume_2_webpage` expects a Markdown resume file path.
4. Select `use_meta=True` if you want the built-in persona prompt used by the README examples.
5. Keep `torch.autocast(device_type="cuda", dtype=torch.float16)` or a reviewed bf16 equivalent in the execution plan.
6. Treat `num_beams`, `do_sample`, `top_p`, `repetition_penalty`, and `max_new_tokens` as prompt-quality controls, not backend selectors.

Example plan:

```python
import torch
from transformers import AutoModel, AutoTokenizer

model_id = "internlm/internlm-xcomposer2d5-7b"
model = AutoModel.from_pretrained(model_id, torch_dtype=torch.bfloat16, trust_remote_code=True).cuda().eval().half()
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model.tokenizer = tokenizer

query = "Analyze the given image in a detailed manner"
image = ["/data/dubai.png"]
with torch.autocast(device_type="cuda", dtype=torch.float16):
    response, history = model.chat(tokenizer, query, image, do_sample=False, num_beams=3, use_meta=True)
```

## Multi-image chat workflow

Use this when the user needs image-by-image reasoning or comparison.

1. Count the images.
2. Insert one `<ImageHere>` placeholder per image.
3. Keep the prompt wording aligned with the image order.
4. Prefer a lower `hd_num` than single-image high-resolution analysis when memory is tight.
5. If you are rendering or validating a prompt, stop when the count and placeholder positions are consistent.

Example shape:

```python
query = "Image1 <ImageHere>; Image2 <ImageHere>; Image3 <ImageHere>; I want to compare the cars one by one"
image = ["cars1.jpg", "cars2.jpg", "cars3.jpg"]
response, history = model.chat(tokenizer, query, image, do_sample=False, num_beams=3, use_meta=True)
```

If the prompt says `Image4 <ImageHere>` but only three images are present, treat it as a planning error and fix the mismatch before execution.

## Video understanding workflow

Current README examples pass a video file path in the `image` list and ask for a detailed description or a follow-up question.

Planning steps:

1. Confirm the runtime has Decord and working video codecs.
2. Keep the video path inside the same list form used by current examples.
3. Use a low-temperature, low-sampling plan for factual descriptions.
4. Ask for a follow-up question only after carrying forward the returned `history`.

Example shape:

```python
query = "Here are some frames of a video. Describe this video in detail"
image = ["/data/liuxiang.mp4"]
response, history = model.chat(tokenizer, query, image, do_sample=False, num_beams=3, use_meta=True)
```

## Webpage and article composition workflow

The current 2.5 model code exposes direct generation methods for content creation.

### Instruction-to-webpage

- Use `write_webpage` for a prompt describing the site layout, style, and content blocks.
- Expect a generated HTML file named from `task.replace(" ", "_") + ".html"`.
- Keep the output directory controlled, because the method writes to the current working directory.
- Mention whether placeholder imagery should be random or local before execution.

### Resume-to-webpage

- Pass a Markdown resume file path to `resume_2_webpage`.
- Verify the file exists and is Markdown before planning execution.
- The method does two passes: HTML, then JavaScript events.
- Plan to inspect the emitted HTML file before opening it in a browser.

### Screenshot-to-webpage

- Provide at least one screenshot image.
- The method overrides the prompt to the fixed Tailwind CSS screenshot-to-webpage instruction.
- It writes `Screenshot-to-Webpage.html` by default.

### Article writing

- Use `write_artical` for long-form article or essay generation.
- Keep the exact misspelling in the API name.
- Plan for long prompt lengths and seed-based reproducibility.
- The method returns article text; it does not automatically write a file in the source examples.

Example planning sketch:

```python
html = model.write_webpage("A website for Research institutions ...", seed=202, task="Instruction-aware Webpage Generation")
resume_html = model.resume_2_webpage("./resume.md", seed=202)
screen_html = model.screen_2_webpage("Generate the HTML code of this web image with Tailwind CSS.", ["screenshot.jpg"], seed=202)
article = model.write_artical("Write a blog about French pastries", seed=8192)
```

## Multi-GPU dispatch workflow

Use multi-GPU dispatch only when a single GPU cannot hold the model or the desired `hd_num`/video resolution.

1. Render a `device_map` with the repo utility name from the source example.
2. Install `accelerate` in the target runtime.
3. Call `dispatch_model(model, device_map=device_map)` only after the base model is loaded.
4. Keep module names aligned with the chosen family.

Source-derived device-map hints:

- current 2.5: visual/front modules on GPU 0, transformer layers split across GPUs, norm/output on the last GPU;
- 2.0/1.0: similar strategy, but with `visual_encoder`, `Qformer`, `internlm_model.*` keys instead of current 2.5 keys.

Dispatching by layer count is an approximation; do not assume the map is valid for every checkpoint variant without a module-name check.

## LMDeploy offline and server workflow

LMDeploy is the source-recommended acceleration path for current 2.5 4-bit/AWQ usage and for serving-oriented planning.

### Offline pipeline

```python
from lmdeploy import pipeline
from lmdeploy.vl import load_image

pipe = pipeline("internlm/internlm-xcomposer2d5-7b")
image = load_image("/data/dubai.png")
response = pipe(("describe this image", image))
print(response.text)
```

### AWQ / 4-bit pipeline

```python
from lmdeploy import TurbomindEngineConfig, pipeline
from lmdeploy.vl import load_image

engine_config = TurbomindEngineConfig(model_format="awq", cache_max_entry_count=0.1)
pipe = pipeline("internlm/internlm-xcomposer2d5-7b-4bit", backend_config=engine_config)
image = load_image("/data/dubai.png")
response = pipe(("describe this image", image))
print(response.text)
```

Planning notes:

- The source install notes say LMDeploy wheels default to CUDA 12.x; treat CUDA 11.x as a special compatibility path.
- Lower `cache_max_entry_count` reduces memory pressure.
- Use AWQ only with the corresponding 4-bit checkpoint.
- If a user wants an API server instead of offline inference, keep the same model id and add a service plan rather than running it here.

### API server plan

The legacy 2.0 README documents the CLI style:

```bash
lmdeploy serve api_server internlm/internlm-xcomposer2-4khd-7b --tp 2 --session-len 32768 --cache-max-entry-count 0.1
```

Treat the exact CLI flags as installation-dependent and confirm `lmdeploy serve api_server -h` in the target runtime before execution. The bundled renderer uses `--mode server` and can emit an AWQ model-format flag for review.

## Legacy compatibility workflow

### 2.0 image chat and 4KHD

Use when the user explicitly references 2.0 checkpoints or older `hd_num`/`AutoModel` examples.

```python
model = AutoModel.from_pretrained("internlm/internlm-xcomposer2-vl-7b", trust_remote_code=True).eval()
model.half().cuda()
tokenizer = AutoTokenizer.from_pretrained("internlm/internlm-xcomposer2-vl-7b", trust_remote_code=True)
text = "<ImageHere>Please describe this image in detail."
image = "examples/image1.webp"
response, history = model.chat(tokenizer, query=text, image=image, history=[], do_sample=False)
```

The 2.0 4KHD docs use `hd_num=55` for high-resolution chat and document analysis.

### 1.0 image chat and generation

Use when the user explicitly needs the original model family or an old repo-era snippet.

```python
model = AutoModel.from_pretrained("internlm/internlm-xcomposer-7b", trust_remote_code=True).cuda().eval()
tokenizer = AutoTokenizer.from_pretrained("internlm/internlm-xcomposer-7b", trust_remote_code=True)
model.tokenizer = tokenizer
response = model.generate("请介绍下爱因斯坦的生平")
response, history = model.chat(text="图片里的人是谁？", image="examples/images/aiyinsitan.jpg", history=None)
```

## Gradio workflow

Use Gradio only as a planning target here. The source scripts expose two current entry points:

- `python gradio_demo/gradio_demo_chat.py`
- `python gradio_demo/gradio_demo_composition.py`

The current scripts accept `--code_path`, `--private`, `--num_gpus`, and `--port`.

Planning split:

- `gradio_demo_chat.py` is the multimodal chat UI with single-image, multi-image, and single-video modes.
- `gradio_demo_composition.py` is the article/composition UI with optional material images and image-search-assisted editing.
- The chat script launches with `share=True` and `server_name="0.0.0.0"`.
- The composition script launches with `share=False` when `--private` is set and `share=True` otherwise.

Keep the launch host, port, and share policy explicit in any plan. Do not assume a public share link is acceptable.
