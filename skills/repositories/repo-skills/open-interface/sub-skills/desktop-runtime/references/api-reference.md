# Desktop Runtime API Reference

## Purpose

Read this when you need to identify which Open Interface component owns a
runtime behavior, validate the LLM command schema, or reason about the safe
computer-use action mapping without launching the app.

## Component map

| Component | Responsibility | Practical notes |
|---|---|---|
| `App` | Wires `Core` and `UI`, starts two daemon bridge threads, and forwards status/user-request queue messages. | `run()` starts both bridge threads and enters the Tk main loop. `cleanup()` delegates to the LLM cleanup path. |
| `Core` | Stops prior requests, obtains LLM instructions, executes each step through `Interpreter`, recurses until `done`, and reports status. | `execute(user_request, step_num=0)` retries once with an explicit valid-JSON reminder when the model returns `{}`. It returns early on interrupt, interpreter failure, missing LLM, or exceptions. |
| `UI` | Tk/ttkbootstrap windows for user request entry, settings, advanced settings, status display, stop button, theme changes, and queueing user requests. | UI settings save operations require app restart for model/provider changes to take effect. |
| `LLM` | Reads settings, builds prompt context from the bundled context resource plus local app/OS/screen facts, and constructs the selected model backend. | Default model name is `gpt-5.2` unless settings override it. Base URL defaults to an OpenAI-style `/v1/` endpoint. |
| `Interpreter` | Converts model-provided JSON steps into `sleep(...)` or `pyautogui` calls. | It accepts bare function names or `pyautogui.<name>` strings. It has special handling for `write`, `press`, and `hotkey`. |
| `Settings` | Persists and loads UI/provider settings. | The `api_key` value is base64-encoded in the settings file; it is not a secure secret store. |
| `Screen` | Uses pyautogui to query screen size and capture screenshots as image objects, base64 strings, temp files, or a persistent screenshot file. | Import and screenshot behavior can fail on headless Linux or systems without screen-recording permissions. |
| `ModelFactory` | Chooses provider backend class from the configured model name. | GPT-4o/mini, GPT-5 family, GPT-4 vision/turbo/custom OpenAI-style, Gemini family, and `computer-use-preview` are routed differently. |

## Important signatures

These signatures were verified from source/import inspection with GUI calls
stubbed for headless safety:

```text
App.run() -> None
App.send_status_from_core_to_ui() -> None
App.send_user_request_from_ui_to_core() -> None
Core.execute_user_request(user_request: str) -> None
Core.stop_previous_request() -> None
Core.execute(user_request: str, step_num: int = 0) -> Optional[str]
Interpreter.process_commands(json_commands: list[dict[str, Any]]) -> bool
Interpreter.process_command(json_command: dict[str, Any]) -> bool
Interpreter.execute_function(function_name: str, parameters: dict[str, Any]) -> None
LLM.get_settings_values() -> tuple[str, str, str]
LLM.read_context_txt_file() -> str
LLM.get_instructions_for_objective(original_user_request: str, step_num: int = 0) -> dict[str, Any]
Settings.get_dict() -> dict[str, str]
Settings.save_settings_to_file(settings_dict) -> None
Settings.load_settings_from_file() -> dict[str, str]
Screen.get_size() -> tuple[int, int]
Screen.get_screenshot_in_base64() -> str
OpenAIComputerUse.convert_action_to_steps(action: Any) -> list[dict[str, Any]]
OpenAIComputerUse.normalize_key_name(key: str) -> str
```

## LLM request/response contract

The model receives the original user request, a `step_num`, and a screenshot.
For non-computer-use backends, the screenshot is supplied either as a base64
image block or an uploaded file, depending on the backend class. The app expects
the model to return only valid JSON shaped like this:

```json
{
  "steps": [
    {
      "function": "press",
      "parameters": {"key": "enter"},
      "human_readable_justification": "Submit the focused form."
    }
  ],
  "done": null
}
```

Required response keys:

- `steps`: list of command objects. Use an empty list when no more actions are
  needed.
- `done`: `null` while the app should request another screenshot and continue;
  a string when the user request is complete.

Required or common step keys:

- `function`: pyautogui function name, optionally prefixed with `pyautogui.`,
  or `sleep` for a wait step.
- `parameters`: object passed to the function; omitted parameters default to an
  empty object.
- `human_readable_justification`: status text shown to the user while the step
  runs.

If `done` is omitted or left `null` after the task is complete, the app keeps
asking for more screenshots and can loop. If the JSON cannot be parsed, `Core`
asks the model once more to reply in valid JSON.

## Interpreter command behavior

`Interpreter.execute_function()` accepts two broad command families:

1. `sleep` with a `secs` parameter, implemented with `time.sleep`.
2. Any function name present on pyautogui, after stripping a leading
   `pyautogui.` prefix.

Special parameter handling:

- `write`: accepts `string`, `text`, or `message` and passes the chosen text with
  an `interval` default of `0.1`.
- `press`: accepts `keys` or `key`; `presses` defaults to `1`; `interval`
  defaults to `0.2`.
- `hotkey`: accepts a `keys` or `key` list and splats it as positional key
  arguments; a single string is also accepted.
- Other pyautogui calls receive the `parameters` object as keyword arguments.

Before executing the chosen function, the interpreter sends a warm-up
`pyautogui.press("command", interval=0.2)`. That behavior is intentional in the
source, but it can be surprising on non-macOS hosts or in tests; prefer the
bundled contract helper for schema validation because it does not touch the
real keyboard.

## Provider backend routing

| Model setting | Backend class | Transport style | Notes |
|---|---|---|---|
| `gpt-4o`, `gpt-4o-mini` | `GPT4o` | OpenAI Assistants API with uploaded screenshot files | Keeps assistant/thread state and cleans uploaded image files during cleanup. |
| starts with `gpt-5` | `GPT5` | OpenAI Responses API with `input_text` and `input_image` blocks | Default model is `gpt-5.2`. |
| `gpt-4-vision-preview`, `gpt-4-turbo`, or unknown custom model | `GPT4v` | OpenAI-compatible chat completions with base64 image URL | Used for custom OpenAI-style endpoints such as local Llava/Llama adapters. |
| starts with `gemini` | `Gemini` | Google GenAI client with inline image data | Uses the API key value from settings; no OpenAI base URL is used. |
| `computer-use-preview` | `OpenAIComputerUse` | OpenAI Responses API computer-use preview tool | Converts model computer actions into the app's normal pyautogui-style step dictionaries. |

## Computer-use action mapping

The bundled helper implements the same conversion table without importing the
runtime module or pyautogui:

| Computer-use action | Generated step(s) |
|---|---|
| `click` | `click(x, y, button=<button or left>, clicks=1)` |
| `double_click` | `click(x, y, button="left", clicks=2)` |
| `move` | `moveTo(x, y)` |
| `scroll` | `scroll(clicks=-scroll_y)` because pyautogui uses negative values for scrolling down. |
| `type` | `write(string=<text or empty>, interval=0.03)` |
| `wait` | `sleep(secs=1)` |
| `keypress` with one normalized key | `press(key=<normalized>)` |
| `keypress` with multiple normalized keys | `hotkey(keys=[...])` |
| `drag` with at least two path points | `moveTo(start_x, start_y)` then `dragTo(end_x, end_y, duration=0.2, button="left")` |
| `screenshot` | `[]` because the next app loop supplies a new screenshot. |
| unsupported or malformed action | `[]` after logging/diagnosis in the runtime path. |

Key normalization maps `ctrl`/`control` to `ctrl`, `cmd`/`command` to
`command`, `return` to `enter`, `arrowleft` to `left`, `arrowright` to `right`,
`arrowup` to `up`, `arrowdown` to `down`, and preserves other lowercased key
names.

Run `python scripts/inspect_action_map.py --pretty` from this sub-skill to
validate built-in examples, or pass `--input-json` for a saved action/response.
