# Web-interface configuration

## Initializer settings

The application initializer accepts these interface-relevant settings:

- `prompt_file`: prompt source used to construct the agent.
- `tools_to_use`: selected tool-name list; an omitted or falsey value expands to
  the full tool set, which can initialize expensive models.
- `model_dir` and `temp_dir`: model/cache and private generated-file roots.
- `device`: normally `cuda` for model-backed tools, or `cpu` for utility-only
  demonstrations where supported.
- `model`, `temperature`, `top_p`, and `openai_kwargs`: chat-model settings.
  Environment values commonly provide `OPENAI_API_KEY` and optional
  `OPENAI_BASE_URL`; do not print their values.

Keep the selected names exact. The initializer's map includes
`ImageVisualizerTool` and `DicomProcessorTool` as utility tools, along with
model-backed classification, segmentation, visual QA, report-generation,
grounding, LLaVA-Med, and X-ray-generation entries. A tool omitted from
`tools_to_use` is not added to `tools_dict` and cannot service the corresponding
upload or stream event.

## Minimal resource profiles

| Goal | Suggested tools | Notes |
|---|---|---|
| Upload/display smoke test | `ImageVisualizerTool`, optionally `DicomProcessorTool` | No local vision weights, but the normal chat callback still needs a chat model or a stub agent. |
| Lightweight CXR utility demo | Utilities plus `ChestXRayClassifierTool` | Classification may still load/download weights; verify memory and cache availability first. |
| Broader analysis | Add only the requested model-backed tools | LLaVA-Med, grounding, report, VQA, and generation can dominate memory/startup time. |

For CPU-only work, set `device="cpu"` for tools that support it and omit
quantized/GPU-only tools. If a selected tool requires unavailable weights,
remove it rather than allowing startup to fail after the UI is built. A
no-remote-model-weights demo can exercise upload and conversion with a stubbed
`workflow.stream`, but it cannot produce real medical answers without an
inference endpoint.

## Upload and temporary-file settings

Use a private writable `temp_dir` and separate subdirectories for uploads and
converted/tool-result files when possible. Generated basenames should contain
no user-supplied path components. Allow only the image formats your deployment
actually handles and `.dcm` for DICOM. Bound file size and retention, and
clean files only when no active request can reference them.

DICOM requires `DicomProcessorTool` in `tools_dict`. Its adapter contract is
that `_run(path)` returns two values, with the first value containing an
`image_path` used for display. Treat this as an adapter boundary: validate the
returned path before passing it to Gradio, and keep the original `.dcm` path
for the agent's path message.

## Gradio launch settings

The example entrypoint launches on port `8585` with `server_name="0.0.0.0"`
and `share=True`. Those values are not safe defaults for a private medical
image demo:

```python
demo.launch(
    server_name="127.0.0.1",
    server_port=8585,
    share=False,
)
```

Choose a different port only when the port is permitted and unused. Bind
`0.0.0.0` only behind an intentionally configured, authenticated network
boundary. `share=True` should be an explicit temporary exposure decision, not
a convenience switch. Never expose patient images or tool outputs through a
public tunnel by default. If remote access is required, use the deployment's
approved gateway, authentication, TLS, and retention controls.

The interface references an avatar image in the working directory in its
unadapted form. Resolve assets relative to a packaged resource or make the
avatar optional; do not rely on the caller's current directory. Verify the
installed Gradio API supports `ChatMessage`, `Chatbot(type="messages")`,
`UploadButton`, and the chained event methods before launch. The dependency
metadata contains multiple Gradio lower bounds, so test against the actually
installed version and pin a known-compatible version for reproducibility.

Run the safe checker from any directory as a preflight, for example:

```bash
python /path/to/check_gradio_config.py \
  --server-name 127.0.0.1 --server-port 8585 --share false \
  --tools ImageVisualizerTool --tools DicomProcessorTool \
  --enable-dicom
```

The checker validates values and required environment-variable presence without
launching Gradio, reading uploads, or printing secrets. Use `--strict` to make
broad binds and sharing a hard failure in automated checks.
