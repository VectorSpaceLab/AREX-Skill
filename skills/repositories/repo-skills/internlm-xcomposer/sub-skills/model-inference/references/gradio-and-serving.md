# Gradio And Serving Notes

This reference distills the source Gradio demo scripts and serving-related inference notes into a non-executing plan. It does not launch listeners, download models, or open browsers.

## Gradio entry points from source

| Script | Purpose | Launch shape | Key flags |
| --- | --- | --- | --- |
| `gradio_demo/gradio_demo_chat.py` | Multimodal chat UI for single image, multiple images, and single video | `demo.queue().launch(share=True, server_name="0.0.0.0", server_port=args.port, max_threads=1)` | `--code_path`, `--private`, `--num_gpus`, `--port` |
| `gradio_demo/gradio_demo_composition.py` | Article/composition UI with image uploads, caption search, paragraph and image editing | `demo.queue().launch(share=False, server_name="127.0.0.1", server_port=args.port, max_threads=1)` when private, else `share=True` on `0.0.0.0` | `--code_path`, `--private`, `--num_gpus`, `--port` |

## Chat UI facts

Source behavior to preserve in a plan:

- The UI presents three modes: `Single Image`, `Multiple Images`, and `Single Video`.
- It uses `gr.File(file_count='multiple', file_types=['image'])` for image upload and `gr.Video(..., sources=["upload", "webcam"], format='mp4')` for video input.
- Single-image mode warns when the user uploads more than one image.
- The chat demo relies on `decord.VideoReader`, `PIL`, `torchvision`, `Stream`, and `Iteratorize` from the demo asset helpers.
- `GRADIO_TEMP_DIR` is redirected to a repo-local `tmp/` directory, and `no_proxy` is set to local hosts in the script.
- The code currently loads `AutoModelForCausalLM` on CUDA with `device_map='cuda'` and then calls `.half().eval()`.
- The visible port default is `7860`.

Planning notes:

- Keep `share=True` or `share=False` explicit. The source chat script always shares publicly; if that is not desired, treat it as a deliberate policy change rather than an implicit default.
- Because the script loads the model at startup, any plan must include a GPU and checkpoint path that can actually hold the model.
- The chat script is more than a bare textbox: it streams output, tracks history, and provides like/dislike and regenerate controls. Preserve those interactions when describing UI behavior.

## Composition UI facts

The composition demo is the article-writing and editing UI. Its key source behaviors are:

- It exposes an article generation tab with an instruction textbox, optional image upload area, image-number dropdown, seed slider, and advanced settings for beam size, repetition penalty, max output tokens, LLM-only mode, sampling, and meta prompt usage.
- It also exposes paragraph editing and image editing panes, plus a save-article flow that writes the edited article and copied images into a timestamped `databases/` folder.
- The source uses `requests.post('https://lingbi.openxlab.org.cn/image/similar', ...)` to fetch caption-relevant images for the image-edit workflow.
- The UI includes a `--private` switch that determines whether the Gradio app stays on `127.0.0.1` or shares publicly.
- The script prints and stores intermediate markdown and image assets; the main article body is generated before the editing UI is populated.

Planning notes:

- Do not describe the composition UI as a simple chat bot. It is a multi-stage article editor with image insertion and caption search.
- If the user does not want public sharing, treat `--private` as required and keep the launch host on loopback.
- The helper and source script both assume the model can load on CUDA before the interface opens.

## LMDeploy serving notes

Current source README only shows offline pipeline examples for 2.5, but the older 2.0 README documents an LMDeploy API-server flow that still informs service planning.

Plan shape:

```bash
lmdeploy serve api_server internlm/internlm-xcomposer2-4khd-7b --tp 2 --session-len 32768 --cache-max-entry-count 0.1
```

Service planning rules:

- Prefer API-server planning when the user wants an OpenAI-compatible endpoint rather than a local Python script.
- Keep tensor parallelism, session length, and cache ratio explicit.
- Confirm the installed LMDeploy CLI syntax with `lmdeploy serve api_server -h` in the target runtime; flags may vary slightly by release.
- For current 2.5 4-bit/AWQ, use the AWQ checkpoint and `TurbomindEngineConfig(model_format='awq', ...)` in offline or serving plans.

## Launch and exposure checklist

Before a Gradio or serving plan is considered ready, confirm:

1. The model id or local path is explicit.
2. The requested public/private exposure policy is explicit.
3. The chosen port does not conflict with another local service.
4. The runtime has the right GPU count and enough VRAM for startup.
5. Any `no_proxy` or LAN host assumptions are documented.
6. The plan states where generated HTML, article, or log files will be written.

## Bundled runnable Gradio entrypoints

The repaired skill packages the source Gradio demos under `entrypoints/gradio/`. Use these bundled paths instead of relying on a repository checkout:

```bash
cd entrypoints/gradio
MODEL=internlm/internlm-xcomposer2d5-7b PORT=7860 PRIVATE=1 ./run_gradio_chat.sh
MODEL=internlm/internlm-xcomposer2d5-7b PORT=7861 PRIVATE=1 ./run_gradio_composition.sh
```

The wrappers launch `gradio_demo/gradio_demo_chat.py` or `gradio_demo/gradio_demo_composition.py` from inside the bundle so `demo_asset/`, `gradio_demo/utils.py`, and `SimHei.ttf` resolve locally. They are real service entrypoints: run them only after model/cache, CUDA, package versions, port, and exposure policy are approved.

## Common source-equivalent launch patterns

If the user copies files into another working directory, the equivalent Python commands are:

### Chat demo

```bash
python gradio_demo/gradio_demo_chat.py --code_path internlm/internlm-xcomposer2d5-7b --num_gpus 1 --port 7860 --private
```

### Composition demo

```bash
python gradio_demo/gradio_demo_composition.py --code_path internlm/internlm-xcomposer2d5-7b --private --num_gpus 1 --port 7861
```

### LMDeploy offline inference before serving

```python
from lmdeploy import pipeline
from lmdeploy.vl import load_image
pipe = pipeline("internlm/internlm-xcomposer2d5-7b")
image = load_image("/data/dubai.png")
response = pipe(("describe this image", image))
```

These snippets are planning templates only; they are not intended to be executed from this sub-skill.
