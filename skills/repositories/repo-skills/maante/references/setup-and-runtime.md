# Setup and Runtime Reference

## When To Read

Read this when preparing a MaaNTE checkout, choosing verification commands, diagnosing import/runtime failures, or deciding whether a workflow needs Windows, DirectML, audio services, game access, or MaaFramework resources.

## Repository Runtime Shape

MaaNTE is distributed as a MaaFramework resource/agent package:

- `assets/interface.json` registers controller modes, resources, task imports, locales, and the child agent command.
- `assets/resource/tasks/*.json` defines GUI-visible tasks and option-to-pipeline overrides.
- `assets/resource/base/pipeline/**/*.json` defines MaaFramework Pipeline nodes.
- `agent/main.py` is launched by MaaFramework/MXU and imports all `agent/custom/action` modules so decorated custom actions and recognitions register with `AgentServer`.
- `agent/utils` owns logging, PI environment helpers, i18n lookup, maafocus user messages, screen utilities, and Windows process helpers.

The package is Windows-oriented even though many static checks and imports can run on Linux. Real gameplay validation requires the NTE game window, MaaFramework resources, the selected controller, and 1280×720 rendering.

## Development Setup

Minimum development setup from repository evidence:

```bash
git submodule update --init --recursive
python -m venv .venv
# Windows activation: .venv\Scripts\activate
# POSIX activation for inspection-only work: source .venv/bin/activate
pip install -r requirements.txt
```

Important requirement families:

| Dependency | Why MaaNTE uses it |
| --- | --- |
| `maafw==v5.10.4` | MaaFramework Python bindings, `AgentServer`, `Context`, Pipeline types, CustomAction/CustomRecognition base classes. |
| `opencv-python`, `pillow`, `numpy`, `scipy`, `scikit-learn` | Template matching, image processing, map/Navi algorithms, dataset frames, and minigame perception. |
| `onnxruntime-directml` | Windows DirectML direction inference for navigation angle prediction. CPU `onnxruntime` can inspect APIs but does not prove DirectML gameplay performance. |
| `librosa`, `soundcard` | SoundDodge audio loading, loopback recording, and event detection. Requires a host audio backend/device. |
| `mido` | MIDI parsing for AutoPiano. |
| `scapy`, `pktmon-interface`, `websockets` | Navi coordinate capture alternatives and OnlineMapNavigation WebSocket service. |
| `loguru` | Preferred logging backend with standard logging fallback. |

## Build and Packaging Commands

The root `build.py` script creates a release package and downloads/assembles MaaFramework, MXU or MFAA, and Python runtime dependencies. Use these commands as maintainer workflows, not as cheap validation in a CI-less coding task:

```bash
python build.py
python build.py --mode=mxu
python build.py --mode=mfaa
python build.py --skip-download
python build.py --compress=false
python build.py --tag v1.0.0
```

`build.py` targets Python 3.12.10 for bundled release runtimes and references MaaFramework/MFAA/MXU release constants inside the script. Do not assume the inspection environment's Python version is the release runtime ABI, especially for the encrypted coordinate `.pyd` file.

## Safe Checks

Run these before or after source edits when practical:

```bash
python -m py_compile agent/custom/action/**/*.py
python scripts/inspect_task_catalog.py --repo-root .
python scripts/check_maante_environment.py --summary
```

The repository notes that automated node testing is not yet ready. Single Pipeline node tests are normally performed manually through a Maa Pipeline Support plugin and a live game window.

## Controller and Platform Constraints

`assets/interface.json` defines these controller families:

- `Win32`: background SendMessage mode with permission requirement.
- `Win32-Front`: foreground/seize mode; some tasks explicitly require it.
- `Win32-Background`: background PrintWindow/SendMessageWithWindowPos mode.
- `CloudGame-Front`: frontend mode for a cloud-game window regex.

Task JSON files may restrict controller types. Do not remove controller restrictions to make a task appear in more modes unless the input and screenshot method were tested there.

## Backend Verification Notes

The inspection run verified `maafw` 5.10.4 importability and MaaFramework Python binding signatures, plus CPU `onnxruntime` provider availability (`CPUExecutionProvider` and `AzureExecutionProvider`) in a private Linux inspection environment. This is enough for static/API guidance, but it is not proof of:

- DirectML navigation inference on Windows.
- Win32 game-window input behavior.
- `soundcard` loopback capture on a host with audio services.
- Npcap/WinPcap or pktmon coordinate capture.
- Actual OCR/template success against a live NTE frame.

Treat those as runtime requirements when users ask for real gameplay verification. Use synthetic checks and helper scripts only to validate guidance, parsers, route files, and task catalog consistency.

## Resolution and Asset Assumptions

- Coordinates, ROI rectangles, and screenshots assume 1280×720.
- Template images are stored under the resource image tree and are referenced relative to `resource/base/image` at runtime.
- Pipeline OCR `expected` values often include simplified Chinese, traditional Chinese, English regex, Japanese, and Korean variants.
- A path with Chinese/full-width characters is explicitly warned about in `agent/main.py`; prefer pure ASCII install paths for packaged runtime users.
