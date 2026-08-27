# AppAgent setup

Use this reference before either workflow. It covers host prerequisites, Python installation, and the minimum readiness check.

## What AppAgent needs
- Python 3.11+ with the repo requirements installed.
- `adb` on `PATH`.
- A connected Android device or an Android Studio emulator with USB debugging enabled.
- An LLM backend configured in `config.yaml`:
  - `MODEL: "OpenAI"` with OpenAI vision credentials, or
  - `MODEL: "Qwen"` with a DashScope key.

## Recommended setup order
1. Create or reuse a private Python environment.
2. Install the repo requirements.
3. Edit `config.yaml` with the chosen model backend and API key.
4. Verify `adb` can see the device or emulator.
5. Choose a writable `root_dir` outside the repo if you do not want generated `apps/` and `tasks/` folders in the checkout.
6. Run `scripts/check_setup.py` from the generated skill to catch missing config, imports, or adb before starting a workflow.

## Installation
```bash
python -m pip install -r requirements.txt
```

The repo has no packaging metadata, so installation is requirements-driven rather than editable-package driven.

## Device setup
- Real device: enable USB debugging, connect by cable, and confirm `adb devices` shows the device.
- Emulator: Android Studio's emulator also works if it exposes an adb target.
- If `adb` is missing, install Android platform-tools or Android Studio first.

## Config source of truth
`config.load_config()` reads `config.yaml` and then overlays that YAML onto the environment map. In practice, the YAML file is the effective source of truth for AppAgent runs, so edit it directly instead of relying on shell environment variables to override the same keys.

## Ready check
Use the bundled checker when you want a quick preflight:
- `scripts/check_setup.py` for a full readiness check.
- `scripts/check_setup.py --skip-adb` if you only need Python imports and config validation.

A healthy preflight should confirm:
- config file is readable,
- required keys are present,
- helper modules import,
- `adb` is on `PATH` for real device use.
