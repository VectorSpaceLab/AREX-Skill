# Legacy Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| v2 command ignores flags | v2 settings are source variables, not CLI | Patch a private runtime copy; do not add nonexistent CLI flags. |
| v1 local install is very heavy | GroundingDINO/OCR/CLIP/ModelScope dependencies | Use v1 hosted API if available, or migrate to v3.5 for new tasks. |
| HarmonyOS command includes ADB | Wrong v3 route | Use `--hdc_path` and no `--adb_path` for `v3-harmony`. |
| Coordinates are wrong | `coor_type` mismatch | Use `--coor_type qwen-vl` for models returning normalized 0-1000 relative coordinates; otherwise leave absolute mode. |
| Text entry fails | ADB/HDC input method issue | Install/select ADB Keyboard for Android; handle HarmonyOS typing spaces carefully in a private runtime copy if needed. |
| API token appears in answer/log | Secret was passed literally | Use env vars (`--token-env`, `--api-key-env`) in builders. |
| Migration loses memory behavior | v2 reflection/memory hints not mapped | Preserve `add_info`; use Mobile-Agent-E only when persistent cross-task memory is required. |
