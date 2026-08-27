# GUI-Owl Configuration Reference

## Required fields by platform

| Platform | Required | Common optional |
|---|---|---|
| mobile | `adb_path`, `api_key`, `base_url`, `model`, `instruction` | `device`, `add_info`, `max_steps`, app resolver API/base/model |
| computer | `api_key`, `base_url`, `model`, `instruction` | `add_info`, `max_steps` |
| browser | `task` or `web`, `model`, `base_url` | `task_id`, `rollout_id`, `output_dir`, `headless`, `image_type`, SoM/eval flags |

Use environment variables for secrets:

```bash
export GUI_OWL_API_KEY=...
export GUI_OWL_BASE_URL=https://your-openai-compatible-endpoint/v1
export GUI_OWL_MODEL=your-model-name
export ADB_PATH=/path/to/adb
export MOBILE_AGENT_REPO=/path/to/prepared/MobileAgent
```

Then build commands with the helper scripts instead of pasting keys.

## Validation examples

Mobile shape check:

```bash
python sub-skills/current-gui-owl/scripts/validate_gui_owl_config.py \
  --platform mobile \
  --adb-path-env ADB_PATH \
  --api-key-env GUI_OWL_API_KEY \
  --base-url-env GUI_OWL_BASE_URL \
  --model-env GUI_OWL_MODEL \
  --instruction "Open Notes and write a reminder" \
  --require-adb-keyboard
```

Browser shape check:

```bash
python sub-skills/current-gui-owl/scripts/validate_gui_owl_config.py \
  --platform browser \
  --task "Search the documentation" \
  --web https://example.com \
  --image-type base64 \
  --headless
```

## Common mistakes

- Supplying both literal `--api-key` and `--api-key-env` to a builder.
- Running desktop control from a headless SSH shell.
- Selecting `image_type=oss` without OSS credentials.
- Expecting text entry on Android before installing/selecting ADB Keyboard.
- Asking the model for verbose explanations around tool calls during automated action parsing.
