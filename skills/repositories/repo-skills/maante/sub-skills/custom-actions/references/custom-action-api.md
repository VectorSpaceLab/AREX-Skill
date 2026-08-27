# CustomAction API Reference

## Purpose

This reference captures MaaNTE's Python action architecture and the MaaFramework binding facts verified during skill creation.

## Runtime Bootstrap

`agent/main.py` is the child process launched by MaaFramework/MXU. It:

1. Sets the working directory to the project root.
2. Inserts the `agent/` directory into `sys.path` so `utils` and `custom` imports work.
3. Configures logging.
4. Ensures/relaunches into the repo-managed `.venv` when needed.
5. Imports `custom`, which imports `custom.action`, which imports all registered action modules.
6. Starts `AgentServer` with the identifier provided by MaaFramework.

If an action module fails during import, all registrations after it can be lost.

## Verified MaaFramework Signatures

```python
AgentServer.custom_action(name: str)
AgentServer.custom_recognition(name: str)
CustomAction.RunResult(success: bool)
CustomRecognition.AnalyzeResult(box, detail: dict)
Context.run_task(entry: str, pipeline_override: dict = {})
Context.run_action(entry: str, box=(0, 0, 0, 0), reco_detail="", pipeline_override={})
Context.run_recognition(entry: str, image, pipeline_override: dict = {})
Context.run_recognition_direct(reco_type, reco_param, image)
Context.get_node_data(name: str) -> dict | None
Context.override_next(name: str, next_list: list[str]) -> bool
Context.set_anchor(anchor_name: str, node_name: str) -> bool
```

Important Pipeline parameter classes include `JOCR`, `JTemplateMatch`, `JColorMatch`, `JDirectHit`, `JAnd`, `JOr`, and `JCustomRecognition`.

## Parameter Parsing

MaaNTE actions see several parameter styles:

- No parameter: `None`, `{}`, or empty string.
- JSON string from MaaFramework.
- Already decoded dict from tests or newer runtime paths.

Use or mimic `Common.utils.load_params`:

```python
def load_params(custom_action_param) -> dict:
    if not custom_action_param:
        return {}
    if isinstance(custom_action_param, dict):
        return custom_action_param
    try:
        params = json.loads(custom_action_param)
    except Exception:
        return {}
    return params if isinstance(params, dict) else {}
```

Do not call `.get()` on raw `argv.custom_action_param` before normalizing it.

## Controller Patterns

Typical screenshot:

```python
controller = context.tasker.controller
controller.post_screencap().wait()
image = controller.cached_image
```

Some code uses `controller.post_screencap().wait().get()`. Check for `None` and image shape before indexing. Convert BGRA to BGR when needed for OpenCV:

```python
if len(frame.shape) == 3 and frame.shape[2] == 4:
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
```

Common input calls:

- `controller.post_click(x, y).wait()`
- `controller.post_touch_down(x, y).wait()` / `post_touch_up().wait()`
- `controller.post_key_down(vk).wait()` / `post_key_up(vk).wait()`
- `controller.post_relative_move(dx, dy).wait()`
- `controller.post_input_text(text).wait()`

Use 1280×720 coordinates and Win32 virtual key codes.

## Reusing Pipeline Recognition in Python

Use a configured Pipeline node:

```python
image = context.tasker.controller.post_screencap().wait().get()
result = context.run_recognition("SomeNode", image)
if result is not None and result.hit:
    ...
```

Override a recognition-only OCR node:

```python
result = context.run_recognition(
    "NodeOCR",
    image,
    pipeline_override={"NodeOCR": {"recognition": {"param": {"only_rec": True}}}},
)
```

Build a direct recognition:

```python
from maa.pipeline import JRecognitionType, JOCR
result = context.run_recognition_direct(JRecognitionType.OCR, JOCR(roi=[0, 0, 100, 40]), image)
```

## Module-Level State

MaaNTE uses module globals for small cross-call state:

- Tetris round counters and task config.
- BagelSpam cached index and LLM-generated title/body.
- Shared Navi assets and route sessions.

When adding module state, provide an explicit reset action if the state crosses task runs or can become stale.

## Stop and Cleanup

Long loops should follow this pattern:

```python
try:
    while not context.tasker.stopping:
        ...
finally:
    release_keys_or_close_services()
```

PinkPaw, Navi, SoundDodge, Rhythm, Tetris, and dataset recording are all long-running or hold external resources. A failure path that does not release keys, audio threads, WebSocket servers, OpenCV windows, or capture providers is a user-facing bug.
