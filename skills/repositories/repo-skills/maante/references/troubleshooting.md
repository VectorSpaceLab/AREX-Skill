# Cross-Cutting Troubleshooting

## When To Read

Read this when a MaaNTE task fails to start, a task is missing from the UI, recognition loops forever, a Python action fails to import, controller input behaves differently than expected, or runtime logs need triage.

## Missing Task in UI

Symptoms:

- A task file exists but MXU/MaaFramework does not list it.
- Options are missing or a preset does not include the expected task.

Likely causes and checks:

1. The task JSON is not imported by `assets/interface.json`.
2. The task has a `controller` restriction and the selected controller does not match.
3. The task option references a missing i18n key or invalid JSON shape.
4. A preset file did not include the task or its required options.

Use:

```bash
python scripts/inspect_task_catalog.py --repo-root .
```

## Python Import or Registration Failure

Symptoms:

- MaaFramework logs show a custom action is unknown.
- Agent process exits before `AgentServer.start_up` completes.
- Python traceback mentions `ModuleNotFoundError`, `ImportError`, or an AttributeError at import time.

Likely causes:

- The action class is decorated but not imported from `agent/custom/action/__init__.py`.
- The Pipeline `custom_action` or `custom_recognition` string does not exactly match the decorator name.
- A platform-specific import runs too early, such as `ctypes.windll` on non-Windows or `soundcard` without a host audio backend.
- Dependencies from `requirements.txt` are missing in the runtime venv.

Use:

```bash
python sub-skills/custom-actions/scripts/check_custom_action_registry.py --repo-root .
python scripts/check_maante_environment.py --summary
```

## Recognition Fails or Loops Until Timeout

Symptoms:

- Repeated `Node.Recognition.Failed` in MaaFramework logs.
- Pipeline keeps returning through fallback nodes without reaching the business action.
- Task exits even though the visible game state looks close to expected.

Likely causes:

- Game is not 1280×720 or has display scaling/graphics effects that alter templates.
- User is in the wrong scene, or a popup/loading/dialog blocks the expected ROI.
- OCR expected text is incomplete, untranslated, or too strict for the current language.
- Template crop is stale after UI changes.
- A broad fallback is placed before the real business node in `next`.

Recommended fixes:

- Add a state-check node before action, not a blind retry.
- Include `[JumpBack]SceneAnyEnterWorld`, `[JumpBack]SceneClickBlankToExit`, or `[JumpBack]SceneLoading` when a task crosses common scene boundaries.
- Narrow/adjust ROI and threshold only after inspecting the actual screenshot or `save_draw` output.
- Keep OCR `expected` full-text where possible and update all five locale files when adding visible UI keys.

## Controller Mode Mismatch

Symptoms:

- Task appears in one controller but not another.
- Mouse/keyboard actions work only while the game is focused.
- Background screenshot does not match foreground behavior.

Likely causes:

- Task JSON restricts the controller to `Win32-Front` because it needs foreground/seize input.
- Game or cloud-game window regex differs from `assets/interface.json` controller definitions.
- A Python action uses direct Win32 APIs or low-level key states that are not portable.

Do not remove controller restrictions without testing the actual task in that controller mode.

## SoundDodge Audio Failure

Symptoms:

- Importing `soundcard` fails on Linux/headless systems.
- SoundDodge starts but never triggers or triggers constantly.
- Audio thresholds feel inverted.

Likely causes:

- No PulseAudio/PipeWire/loopback device on Linux inspection machines.
- Windows audio loopback device not available or wrong default device.
- Threshold too low causes false positives; threshold too high misses attacks.

Use the media sub-skill troubleshooting. In task options, lower thresholds are more sensitive.

## Navi / Coordinate Capture Failure

Symptoms:

- `position_backend=coordinate` fails immediately.
- Online map shows `position: null` or stale coordinates.
- Navigation turns but never converges.

Likely causes:

- Encrypted coordinate core `.pyd` requires matching Windows Python ABI and architecture.
- Npcap/WinPcap or pktmon backend unavailable or missing permissions.
- Route JSON uses unsupported point fields or wrong source map size.
- `tolerance` is too small for map-location error.

Use the navigation route validator for schema issues and the navigation sub-skill for backend selection.

## Logging Triage

When analyzing user logs, build a timeline across these files if available:

1. `mxu-tauri.log` for task start and task id.
2. `debug/maa.log` for Pipeline recognition/action transitions.
3. `debug/custom/*.log` or `runtime.log` for Python action details.
4. `mxu-agent-*.log` for user-visible child-agent output.
5. `on_error/` screenshots and `vision/` draw images for actual screen evidence.

Do not treat every historical ERROR as the failing run. Tie evidence to the active task id and reproduction time.
