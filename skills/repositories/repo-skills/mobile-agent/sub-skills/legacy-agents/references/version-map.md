# Legacy Version Map

| Version | Execution surface | Key settings | Main risk |
|---|---|---|---|
| v1 local | `Mobile-Agent-v1/run.py` | `--instruction`, `--adb_path`, `--api` | Downloads/loads GroundingDINO, OCR, CLIP, and ModelScope-style models. |
| v1 hosted API | `Mobile-Agent-v1/run_api.py` | `--instruction`, `--adb_path`, `--url`, `--token` | Requires hosted service, but avoids local legacy perception stack. |
| v2 | `Mobile-Agent-v2/run.py` | Edited variables: `adb_path`, `instruction`, `API_url`, `token`, `caption_call_method`, `caption_model`, `qwen_api`, `add_info`, `reflection_switch`, `memory_switch` | No CLI for most settings; requires patching a private runtime copy. |
| v3 Android | `Mobile-Agent-v3/mobile_v3/run_mobileagentv3.py` | `--adb_path`, API/base/model, `--instruction`, `--add_info`, `--coor_type`, `--notetaker` | Coordinate mode confusion and Android typing setup. |
| v3 HarmonyOS | same script | `--hdc_path` instead of `--adb_path` | HDC authorization and HarmonyOS typing/input pitfalls. |

Use `v1-api` when the user has a hosted v1 service and wants to avoid local GroundingDINO/CLIP/TensorFlow/ModelScope dependencies. Use v3 route when the user explicitly names v3 or HarmonyOS/HDC. For new Android tasks, prefer current GUI-Owl v3.5 unless preserving legacy behavior is required.
