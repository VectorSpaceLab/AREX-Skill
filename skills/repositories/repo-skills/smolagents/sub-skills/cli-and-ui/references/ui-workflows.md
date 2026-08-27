# UI Workflows

## Gradio UI

`GradioUI` is exported by smolagents and wraps an existing `MultiStepAgent` in a Gradio `ChatInterface`.

```python
from smolagents import CodeAgent, GradioUI, InferenceClientModel, WebSearchTool

model = InferenceClientModel(model_id="meta-llama/Llama-3.3-70B-Instruct", provider="fireworks-ai")
agent = CodeAgent(
    tools=[WebSearchTool()],
    model=model,
    planning_interval=3,
    name="example_agent",
    description="Example agent",
    stream_outputs=True,
)
GradioUI(agent, file_upload_folder="uploads", reset_agent_memory=True).launch(share=False)
```

### Constructor Options

- `agent`: any `MultiStepAgent` such as `CodeAgent` or `ToolCallingAgent`.
- `file_upload_folder`: enables multimodal input and stores uploaded files in that folder; when omitted, upload support is disabled.
- `reset_agent_memory`: when `True`, each UI turn calls the agent with `reset=True`.

### Launch Behavior

- `GradioUI.launch(share=True, **kwargs)` delegates to Gradio `launch(debug=True, share=share, **kwargs)`. Pass `share=False` for local-only demos.
- `create_app()` returns the Gradio app if the caller wants to mount or customize it before launch.
- The chat title comes from `agent.name`; description metadata can be kept on the agent for humans even though the UI primarily renders the title.

### File Upload Behavior

- Default upload allow-list is `.pdf`, `.docx`, and `.txt`.
- Uploaded filenames are sanitized by replacing non-word, non-dot, non-hyphen characters with `_` before copying.
- The prompt sent to the agent includes `You have been provided with these files: [...]` when files are present and upload storage is enabled.
- To change allowed extensions, call `upload_file(..., allowed_file_types=[...])` in a custom UI wrapper; the stock `ChatInterface` path uses the default allow-list.

### Streaming And Step Display

- `stream_to_gradio(agent, task, task_images=None, reset_agent_memory=False, additional_args=None)` yields incremental text for `ChatMessageStreamDelta` events and structured messages for action, planning, and final-answer steps.
- `pull_messages_from_step(...)` formats action steps, tool calls, execution logs, images, errors, token usage, and duration footnotes as Gradio chat messages.
- If `agent.stream_outputs` is true, model output embedded in completed steps is skipped to avoid duplicate display after streaming deltas.
- `AgentImage` and `AgentAudio` final answers are converted to file payloads for Gradio rendering.

## `launch_gradio_demo`

`launch_gradio_demo(tool)` is a convenience helper for a single `Tool`, not a full agent chat UI. The tool must define `inputs` and `output_type`; the helper maps supported input/output types (`boolean`, `image`, `audio`, `string`, `integer`, `number`) to Gradio components and launches a Gradio `Interface` using the tool name and description. If the user needs an agent conversation, upload folders, reset policy, local-only serving, custom Gradio kwargs, or app mounting, use `GradioUI` directly.

## Starlette/Uvicorn Server Pattern

The server example is a reference pattern for a custom web app:

```python
from anyio import to_thread
from starlette.responses import JSONResponse

async def chat(request):
    data = await request.json()
    message = data.get("message", "").strip()
    result = await to_thread.run_sync(agent.run, message)
    return JSONResponse({"reply": str(result)})
```

Key points:

- Do not call blocking `agent.run(...)` directly in an async request handler; use a worker thread or a job queue.
- Disconnect external clients, such as MCP clients, in application shutdown hooks.
- Keep model credentials in environment variables or secret managers; do not hard-code them into UI/server files.
- Install serving dependencies explicitly, for example `starlette`, `anyio`, and `uvicorn`, plus any smolagents extras required by the tools.

## UI Monitoring

For production debugging, combine a UI/server with telemetry. The documented patterns use OpenTelemetry instrumentation through Phoenix, MLflow, or Langfuse. Initialize instrumentation before constructing/running agents, then inspect traces in the chosen backend. Route detailed telemetry setup to the observability or agent-runtime guidance if that exists in the parent skill.
