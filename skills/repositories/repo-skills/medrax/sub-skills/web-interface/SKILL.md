---
name: web-interface
description: "Operate and safely adapt the MedRAX Gradio chat interface around
  an initialized agent, including image and DICOM uploads, chat threads,
  tool-result images, and server configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MedRAX web interface

Use this skill when a researcher needs to run or modify the browser UI around an
already initialized MedRAX agent. This is an interface adapter, not a tool
implementation or an agent-graph tutorial.

## Operating contract

- Input: an initialized `agent` exposing `workflow.stream(...)`, plus a
  `tools_dict` mapping the selected tool names to initialized tool instances.
- Output: a Gradio `Blocks` demo that accepts a user message and optional image,
  streams assistant/tool events, and returns `(chat_history, image_path, text)`
  for the bound outputs.
- Keep the original uploaded path for tools and keep a separately viewable path
  for the UI. Never silently replace a DICOM path with its converted PNG when a
  downstream tool needs the DICOM.
- The interface is a convenience for analysis, not a diagnostic device. Do not
  present model output as a clinical conclusion; retain a visible safety notice
  appropriate to the deployment.

For the detailed event and upload sequence, read [workflows.md](references/workflows.md).
For launch and resource settings, read [configuration.md](references/configuration.md).
For failure diagnosis, read [troubleshooting.md](references/troubleshooting.md).

## Entrypoint and lifecycle

1. Load the medical system prompt and call the application initializer. Its
   configuration includes `tools_to_use`, `model_dir`, `temp_dir`, `device`,
   model name, temperature, top-p, and OpenAI-compatible keyword arguments.
2. Select only tools that are installed and affordable. The initializer's
   utility choices include `ImageVisualizerTool` and `DicomProcessorTool`; its
   model-backed choices include classification, segmentation, visual QA,
   report generation, grounding, LLaVA-Med, and generation. A selected tool
   must be present in both the agent tool list and `tools_dict`.
3. Call `create_demo(agent, tools_dict)`. It constructs `ChatInterface`, a
   `gr.Blocks` layout, a messages-style `Chatbot`, text input, image display,
   upload buttons, and Clear Chat/New Thread controls.
4. Bind text submission as two stages: `add_message` first appends the user
   image and text and disables the textbox; `process_message` then streams
   agent events and updates chatbot, display image, and textbox. Re-enable the
   textbox after completion, including failure.
5. Launch with explicit, reviewed server settings. A safe local default is
   loopback and `share=False`; do not inherit the example's broad bind and
   public share settings without a deployment decision.

`ChatInterface` currently stores `current_thread_id`, `original_file_path`, and
`display_file_path` on one Python object. That is adequate for a single-user
demo only. For concurrent users, put these values in per-session `gr.State` (or
a server-side session store), use a collision-resistant thread identifier, and
never let one browser's upload or thread be reused by another browser.

## Upload and path rules

- `UploadButton` is configured separately for ordinary images and DICOM. The
  current DICOM button accepts a generic file, so validate the lower-cased
  suffix before processing rather than trusting the widget.
- Copy uploads into a controlled temporary directory using a generated name.
  Preserve the original suffix; do not use the client filename as a path.
  Prefer a UUID plus suffix over a seconds-only timestamp to avoid collisions.
  Apply size, count, and suffix allowlists and clean old files deliberately.
- For an ordinary image, the copied path can serve both purposes after basic
  validation. For `.dcm`, call the selected `DicomProcessorTool` and read the
  returned display mapping's `image_path` for the UI.
- Keep `original_file_path` as the path sent in the textual `image_path:`
  message. Keep `display_file_path` as the PNG or other viewable conversion.
  If a multimodal payload is also built, encode the display path with its real
  MIME type; never label raw DICOM bytes as JPEG. This distinction is required
  even though the current implementation uses one fallback path for both.
- If DICOM is enabled, fail early with a clear configuration error when
  `tools_dict["DicomProcessorTool"]` is missing. Do not catch that as an
  unexplained chat failure.

## Message and event handling

Build the current request in the shape expected by the agent:

- Optional path message: `{"role": "user", "content": "image_path: <path>"}`.
- Optional multimodal message: a user content list containing an
  `image_url` data payload for the viewable image.
- Optional text message: a user content list containing
  `{"type": "text", "text": <message>}`.

The current LangGraph call is conceptually:

```python
agent.workflow.stream(
    {"messages": messages},
    {"configurable": {"thread_id": thread_id}},
)
```

The checkpointer and thread ID carry graph state; the visible Gradio history is
not itself the complete graph conversation. New threads must receive a new ID.
Clear Chat should also decide whether it is merely a visual reset or a new
conversation; make that choice explicit instead of leaving stale graph state.

Handle the stream defensively:

- For a `process` event, take the latest message content, format it as text,
  and append an assistant `ChatMessage`.
- For an `execute` event, iterate tool messages, use the emitted tool name, and
  display textual results plus any validated image result. The current image
  branch recognizes the emitted name `image_visualizer`; do not assume it is
  the same spelling/case as `ImageVisualizerTool` in `tools_dict`.
- Never use `eval` on tool output. Prefer structured tool returns; for a legacy
  serialized value, use a constrained parser and validate the result shape and
  path before rendering it.
- Every normal and error path must yield the same number and order of outputs:
  `(history, display_path, "")`. Do not expose raw temporary paths in assistant
  text, and do not put an unredacted provider exception or credential in chat.

## Reset, rendering, and assets

- Clear Chat should clear visible messages and the displayed image, remove or
  rotate the active session's upload references, and—if conversation reset is
  intended—rotate the thread ID too.
- New Thread should rotate only the conversation ID unless the product
  explicitly promises to remove the selected image. Document the behavior.
- Tool-generated images should be rendered only after checking that the path is
  an expected local result, not an arbitrary path returned by a model or tool.
- Resolve the avatar/logo from a packaged resource at runtime. If it is absent,
  use a no-avatar configuration instead of making startup depend on the
  process's current working directory.

## Resource-constrained adaptation

For a CPU-only utility demonstration, initialize only
`ImageVisualizerTool` and `DicomProcessorTool` with `device="cpu"` where the
initializer requires a device. This avoids local vision-model weight loading,
but the normal `process_message` still calls the configured chat model. A full
chat demo therefore still needs an accessible OpenAI-compatible model endpoint,
or a test/stub agent whose `workflow.stream` produces deterministic events.
Do not claim a no-weight, no-model setup can answer medical questions.

Use [configuration.md](references/configuration.md) for a minimal selection
matrix and [troubleshooting.md](references/troubleshooting.md) when an
optional model-backed tool prevents startup.

## Scope boundaries

Route tool signatures, image processing, DICOM conversion implementation, and
result schemas to `chest-xray-analysis` or `image-data-utilities`. Route
LangGraph agent construction, prompts, checkpointers, and tool binding to
`agent-orchestration`. Route benchmark execution and scoring to
`benchmark-evaluation`. This skill only adapts their initialized outputs to a
safe Gradio lifecycle.
