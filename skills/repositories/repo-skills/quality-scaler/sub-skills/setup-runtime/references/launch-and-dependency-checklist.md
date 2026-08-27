# Launch and dependency checklist

## Purpose

Read this when the app will not start yet and you need the smallest safe sequence that gets QualityScaler ready on a Windows machine.

## Launch order

1. Confirm the platform is Windows 10/11.
2. Use Python 3.12 or newer for the source module.
3. Install the public runtime set described in the root shared runtime reference.
4. Place the model files under `AI-onnx/` with the exact `_fp16.onnx` names.
5. Place `ffmpeg.exe` and `exiftool.exe` under `Assets/`.
6. Confirm the DirectML provider is visible to the ONNX runtime before trying image or video work.
7. Start the GUI only after the layout check passes.

## What to verify before launch

- The app entry file exists.
- The asset folders exist.
- The model filenames match the source expectations exactly.
- The runtime dependency set imports cleanly.
- The preference JSON either exists and parses or does not exist yet.

## Suggested safe checks

- Run the bundled layout helper to confirm file presence.
- Confirm the package imports in the target environment.
- Check the available ONNX providers before launching the GUI.
- Launch the app only after the above checks are green.

## Notes for future agents

- The source is not a cross-platform desktop app; the launch path is Windows-specific.
- An environment that can import the module for inspection may still be missing the intended DirectML runtime.
- Layout checks are more useful than raw file existence guesses because the app depends on exact filenames.
