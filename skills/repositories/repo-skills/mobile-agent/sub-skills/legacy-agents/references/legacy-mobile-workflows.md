# Legacy Mobile Workflows

## v1 hosted API

Use when the user has a hosted Mobile-Agent v1 service URL/token:

```bash
python sub-skills/legacy-agents/scripts/build_legacy_mobile_command.py \
  --version v1-api \
  --instruction "Open an app" \
  --adb-path-env ADB_PATH \
  --url-env MOBILE_AGENT_V1_URL \
  --token-env MOBILE_AGENT_V1_TOKEN
```

This route avoids local GroundingDINO/OCR/CLIP downloads.

## v1 local

Use only for exact local reproduction. It requires the old local perception stack and model downloads:

```bash
python sub-skills/legacy-agents/scripts/build_legacy_mobile_command.py \
  --version v1-local \
  --instruction "Open an app" \
  --adb-path-env ADB_PATH \
  --api-env MOBILE_AGENT_V1_API
```

## v2 edited settings

v2 settings live in source variables, not CLI flags. Prepare a private runtime copy and edit:

- `adb_path`
- `instruction`
- `API_url`
- `token`
- `caption_call_method`
- `caption_model`
- `qwen_api`
- `add_info`
- `reflection_switch`
- `memory_switch`

The command is simply `python run.py` from the v2 directory after edits. Do not emit nonexistent v2 CLI flags for these settings.

## v3 Android/HarmonyOS

v3 uses CLI flags. Android uses `--adb_path`; HarmonyOS uses `--hdc_path`. Optional `--coor_type qwen-vl` maps 0-1000 relative coordinates to device resolution; `--notetaker True` is for tasks requiring remembered content.
