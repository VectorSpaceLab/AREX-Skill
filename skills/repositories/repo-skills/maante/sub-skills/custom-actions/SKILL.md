---
name: custom-actions
description: "Guides MaaNTE Python CustomAction and CustomRecognition
  development, MaaFramework binding usage, registration, logging, maafocus,
  controllers, and registry checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Custom Actions

## Use This When

Use this sub-skill for work under `agent/custom/action/`, `agent/utils/`, or `agent/main.py`, especially when adding or debugging MaaFramework Python custom actions/recognitions.

Typical prompts:

- Add a new Python action for Pipeline logic that JSON cannot express.
- Diagnose an unknown `custom_action` or missing registration.
- Fix action parameter parsing, long-running loop stop behavior, key release, or screenshot handling.
- Decide whether code belongs in Pipeline JSON or Python.
- Use MaaFramework `Context`, direct recognition, controller APIs, logging, or maafocus messages.

## Read First

1. [references/custom-action-api.md](references/custom-action-api.md) for architecture, verified signatures, parameter parsing, controller calls, and registration rules.
2. [references/logging-and-user-messages.md](references/logging-and-user-messages.md) for `utils.logger`, `maafocus.PrintT`, and why `print()` is usually wrong in actions.
3. [references/troubleshooting.md](references/troubleshooting.md) for platform imports, optional dependencies, stuck loops, and custom action mismatch symptoms.
4. Run [scripts/check_custom_action_registry.py](scripts/check_custom_action_registry.py) to scan decorators, Pipeline references, and `__all__` exports.

## Architecture Rule

Pipeline owns flow control. Python owns the hard parts: image algorithms, state machines, audio/MIDI processing, path navigation, network/route services, and cross-node data persistence. Do not move ordinary screen transitions into Python unless Pipeline cannot express the logic.

## Registration Checklist

- Decorate with exactly the name used by Pipeline:

  ```python
  @AgentServer.custom_action("my_action")
  class MyAction(CustomAction): ...
  ```

- For recognitions:

  ```python
  @AgentServer.custom_recognition("my_recognition")
  class MyRecognition(CustomRecognition): ...
  ```

- Import the module in `agent/custom/action/__init__.py` and add public classes to `__all__` when they are part of the registry surface.
- Ensure a Pipeline node calls the same `custom_action` or `custom_recognition` string.

## Implementation Checklist

- Parse `argv.custom_action_param` as `None`, dict, or JSON string; reject invalid types gracefully.
- Use `context.tasker.controller.post_screencap().wait()` or `.wait().get()` consistently, then read the cached/current image shape before indexing.
- Check `context.tasker.stopping` in long loops and release held keys/buttons in `finally`.
- Return `CustomAction.RunResult(success=True/False)`; do not leak uncaught tracebacks to users.
- Use `context.run_recognition` or `run_recognition_direct` when Python must reuse Pipeline recognizers.
- Keep coordinates and ROI assumptions at 1280×720.
- Avoid platform-specific imports at module import time when possible; wrap Windows/audio/backend imports or document the platform requirement.

## High-Risk Existing Patterns

- `auto_piano/maa_keyboard.py` imports `ctypes.windll.user32` at module import time; it is Windows-only.
- `SoundTrigger/SoundListener.py` imports `soundcard`, which may fail on headless Linux without an audio service.
- Navi coordinate capture depends on a Windows `.pyd` and capture backend; import/runtime errors need clear messages.
- PinkPaw Heist actions hold keys/buttons and use long timed route sequences; always preserve stop checks and release logic.
- Dataset recording uses `ctypes.windll.user32.GetAsyncKeyState` and writes image sequences; it is not a harmless import-only workflow on non-Windows.

## Validation

Use safe checks first:

```bash
python sub-skills/custom-actions/scripts/check_custom_action_registry.py --repo-root .
python -m py_compile agent/custom/action/**/*.py
```

A successful import or compile does not prove a live game action works. For actual task verification, use the relevant gameplay/navigation/media sub-skill and a Windows MaaFramework runtime.
