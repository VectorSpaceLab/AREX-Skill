# Python Workflows

## Purpose

Read this when you need to turn the Python API into a runnable wake-word file check, a safe device preflight, or a microphone recipe.

## 1) File workflow

This is the main workflow for this sub-skill.

### Recommended sequence

1. Install the package:

   ```bash
   pip install pvporcupine
   ```

2. Get a valid Picovoice AccessKey.

3. Choose one of these input modes:
   - built-in keywords through `--keyword`
   - explicit `.ppn` files through `--keyword-path`

4. If you need a custom `.pv` file, pass `--model-path` as well.

5. Run the bundled checker:

   ```bash
   python scripts/porcupine_file_check.py \
     --access-key "$ACCESS_KEY" \
     --input-wav sample.wav \
     --keyword picovoice
   ```

6. Read detections and clean up with `delete()` in the helper or in your own code.

### What the helper validates

`scripts/porcupine_file_check.py` is the safe, checkout-free file recipe for this skill. It is adapted from the packaged Python file demo, but it adds path-safe arguments and the `--help` / `--list-devices` preflight modes. It:

- accepts `--help` without an AccessKey
- can list devices with `--list-devices`
- loads the native Porcupine library through `pvporcupine`
- checks that the WAV file is 16-bit PCM
- checks that the WAV sample rate matches `porcupine.sample_rate`
- uses the engine’s `frame_length` to slice frames exactly
- warns when stereo input is encountered and processes the left channel
- prints detections with timestamps when an AccessKey is supplied

### Built-in keyword example

```bash
python scripts/porcupine_file_check.py \
  --access-key "$ACCESS_KEY" \
  --input-wav sample.wav \
  --keyword picovoice porcupine
```

### Custom keyword path example

```bash
python scripts/porcupine_file_check.py \
  --access-key "$ACCESS_KEY" \
  --input-wav sample.wav \
  --keyword-path /abs/path/to/custom.ppn \
  --model-path /abs/path/to/porcupine_params.pv
```

### Direct API shape

If you need to write your own script instead of using the bundled helper, keep the flow in this order:

```python
porcupine = pvporcupine.create(...)
try:
    print(porcupine.version)
    print(porcupine.frame_length)
    print(porcupine.sample_rate)
    # read wav
    # slice into frame_length chunks
    # call porcupine.process(frame)
finally:
    porcupine.delete()
```

### Asset routing note

If you do not already know which `.ppn` and `.pv` pair belong together, stop here and use `../custom-keywords-and-assets/SKILL.md`. This sub-skill only passes the files through.

## 2) Microphone workflow, reference-only

The live microphone flow is documented here for completeness, but it is hardware-required and therefore not bundled as a runnable helper.

### Packaged CLI

If you install the optional demo package, the console scripts are:

- `porcupine_demo_mic`
- `porcupine_demo_file`

The microphone CLI mirrors the Python API flow and requires a live audio device.

### Typical microphone flow

```bash
pip install pvporcupinedemo
porcupine_demo_mic --access_key "$ACCESS_KEY" --keywords picovoice
```

Useful demo flags:

- `--show_audio_devices` to inspect recorder devices
- `--audio_device_index` to choose a specific microphone
- `--output_path` to save recorded audio for debugging
- `--show_inference_devices` to print the Porcupine inference devices

### Why this stays reference-only

- It depends on live microphone hardware.
- It depends on the optional recorder package.
- It is a long-running stream loop rather than a safe one-shot check.

## 3) Safe preflight and device enumeration

Use these checks before you run file detection or when you want to confirm the native library can see inference backends.

### Safe command

```bash
python scripts/porcupine_file_check.py --list-devices
```

### Programmatic form

```python
import pvporcupine
print("\n".join(pvporcupine.available_devices()))
```

### Device strings to know

The factory accepts these canonical selectors:

- `best`
- `cpu`
- `cpu:N`
- `gpu`
- `gpu:N`

The device list returned by `available_devices()` is the best way to see what the native library currently advertises on the host.

## 4) Optional demo CLI notes

The packaged demo commands are useful when you want a quick compare point with the public Python package, but they are not required for this skill.

- `porcupine_demo_file` is the package’s file demo.
- `porcupine_demo_mic` is the package’s microphone demo.

Prefer the bundled `scripts/porcupine_file_check.py` when you want a self-contained checker that does not depend on the original repository checkout.
