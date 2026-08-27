# Mobile and Desktop GUI-Owl Workflows

## Mobile-Agent-v3.5 mobile

The mobile launcher surface is:

```text
python run_gui_owl_1_5_for_mobile.py \
  --adb_path <adb-binary> \
  [--device <adb-serial>] \
  --api_key <model-api-key> \
  --base_url <openai-compatible-base-url> \
  --model <model-name> \
  --instruction <task> \
  [--add_info <hints>] \
  [--max_steps 50] \
  [--app_resolver_api_key <key>] \
  [--app_resolver_base_url <url>] \
  [--app_resolver_model qwen-plus]
```

Use `scripts/build_mobile_command.py` to print this safely with environment-variable substitutions.

### Mobile preflight

- `adb_path` points to a platform-tools `adb` binary.
- The device/emulator appears in `adb devices` as `device`, not unauthorized/offline.
- USB debugging is enabled.
- ADB Keyboard (or equivalent input method) is installed and selected for text-entry tasks.
- The OpenAI-compatible endpoint can serve the model and accepts images/tool-call prompts.
- The instruction is concrete; put persistent hints in `--add_info`.

### Mobile execution behavior

The launcher captures screenshots, asks GUI-Owl for a tool-call action, rescales normalized coordinates to screenshot pixels, and executes actions through ADB helpers. The `open` action may resolve app names through `NAME_PACKAGE_DICT` and, if necessary, a separate app-resolver LLM configured by the resolver flags.

## Desktop GUI-Owl computer-use

The desktop launcher surface is:

```text
python run_gui_owl_1_5_for_pc.py \
  --api_key <model-api-key> \
  --base_url <openai-compatible-base-url> \
  --model <model-name> \
  --instruction <task> \
  [--add_info <hints>] \
  [--max_steps 50]
```

Use `scripts/build_computer_command.py` to print this safely.

### Desktop preflight

- The runtime host has an unlocked interactive GUI session.
- Screenshot capture works in that session.
- Accessibility/input automation permissions are granted by the OS.
- The model endpoint can process screenshots and return one valid GUI-Owl action at a time.
- If the host is Linux, `DISPLAY` or `WAYLAND_DISPLAY` should refer to the live desktop session.

## Shared action format

The mobile and desktop launchers expect GUI-Owl-style JSON inside a `<tool_call>` block. Coordinates are normalized `0..1000` and rescaled to the screenshot size before action execution. Typical actions include click/tap, text input, swipes/drags, app open, back/home/finish, and desktop mouse/keyboard operations.

When parsing fails, ask the model to output exactly one complete `<tool_call>` JSON object with nested `arguments`. Avoid extra prose around the tool call during automated execution.
