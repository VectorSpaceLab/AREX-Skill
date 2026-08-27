# Bundled XComposer Gradio Entrypoints

This directory packages the source-derived Gradio chat and composition demos plus their local support modules/assets so a future agent does not need the original source checkout to start a demo.

## Contents

- `gradio_demo/gradio_demo_chat.py` — multimodal chat UI for single-image, multi-image, and video prompts.
- `gradio_demo/gradio_demo_composition.py` — article/webpage/composition UI.
- `demo_asset/` — source demo helpers and example UI assets used by the demos.
- `SimHei.ttf` — local font used for multi-frame/multi-image labelling; bundled to avoid a runtime font download for that path.
- `run_gradio_chat.sh` and `run_gradio_composition.sh` — self-contained launch wrappers that `cd` to this bundle before starting Python.

## Execution gates

These are real service entrypoints. Run them only after model/cache, CUDA, Gradio, and exposure policy are approved. They load the model passed through `MODEL`/`--code_path`, allocate CUDA memory, and may bind a browser-visible service. The composition demo's optional image-search-assisted editing path calls the documented external image-search endpoint; disable or avoid that path in offline/private environments.

## Examples

```bash
# Local/private chat demo, using a local or hub model id.
MODEL=internlm/internlm-xcomposer2d5-7b PORT=7860 PRIVATE=1 ./run_gradio_chat.sh

# Composition demo. PRIVATE=1 maps to the source `--private` flag.
MODEL=/models/internlm-xcomposer2d5-7b PORT=7861 PRIVATE=1 ./run_gradio_composition.sh
```

The wrappers stay inside this bundle; generated articles/databases/tmp files are written relative to the bundle unless the demo code is edited before execution.
