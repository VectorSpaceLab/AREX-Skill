# Separation troubleshooting

Use this file for workflow-specific failures from `spleeter separate`, `Separator`, `AudioAdapter`, ffmpeg load/save, filename templates, MWF, and pretrained model first-run downloads. For install-wide issues, see the [root troubleshooting reference](../../../references/troubleshooting.md) and [installation/runtime reference](../../../references/installation-and-runtime.md).

## Quick triage order

1. Run `python -m spleeter --version` and `python -m spleeter separate --help`.
2. Confirm `ffmpeg -version` and `ffprobe -version` work in the same shell.
3. Run a short WAV smoke command with `--duration 10`, default codec `wav`, and default filename format.
4. If failure occurs before separation starts, check model descriptor/cache/network issues.
5. If failure occurs while loading or saving audio, check path, stream, codec, and permissions issues.

## Symptoms and recoveries

| Symptom or message | Likely cause | Recovery |
| --- | --- | --- |
| `ffmpeg binary not found` or `ffprobe binary not found` | Default `FFMPEGProcessAudioAdapter` cannot find system ffmpeg tools | Install ffmpeg/ffprobe for the platform and ensure both commands are on `PATH` in the same shell or service environment that runs Spleeter. Re-run `python -m spleeter separate --help` and a short smoke command. |
| `An error occurs with ffprobe` | Path is wrong, file is unreadable, file is not an audio container, or ffprobe cannot decode it | Verify the exact path, permissions, and container with `ffprobe input_file`. If needed, transcode to a known-good WAV/FLAC file with ffmpeg and retry. |
| `No stream was found with ffprobe` or failure after probing | The file has no audio stream, has an unsupported stream layout, or the selected object is not an audio file | Check `ffprobe -show_streams input_file`; use a file with an audio stream or convert/extract audio first. |
| CLI rejects input before running | Positional input path does not exist or is not a readable file | Pass files as positional arguments after options. Use shell quoting for spaces. Avoid directories unless a wrapper expands them into files first. |
| Command exits with code 20 and logs that `-i` is not supported | Deprecated `-i`/`--inputs` option was used | Replace `python -m spleeter separate -i song.wav -o out` with `python -m spleeter separate -o out song.wav`. |
| `Separated source path conflict` | `filename_format` maps more than one stem from the same input to the same path, commonly because `{instrument}` is missing | Include `{instrument}` in the template, for example `{filename}/{instrument}.{codec}` or `{filename}_{instrument}.{codec}`. |
| Later files overwrite earlier batch outputs | Multi-file template does not distinguish input files, for example it uses `{instrument}.{codec}` only | Include `{filename}` or `{foldername}` for multi-file jobs, or use a unique output directory per input. The bundled helper warns about this before execution. |
| `output directory does not exists` from direct adapter use | `FFMPEGProcessAudioAdapter.save` was called directly and the parent directory was not created | Create the parent directory before `adapter.save(...)`, or use `Separator.save_to_file(...)`, which creates output directories for each formatted stem path. |
| Permission denied or no output files | Output path is not writable, parent filesystem is full, process ended before asynchronous saves completed, or the filename template points outside the intended writable tree | Choose a writable output directory, keep templates relative, check free space, and call `separator.join()` when using asynchronous Python saves. Use `synchronous=True` for simpler scripts. |
| First run hangs or fails before writing stems | Pretrained model download is in progress or failed because of network, proxy, release host, or cache permissions | Expect first-run latency. Retry once after network/proxy is fixed. For repeated failures, inspect model descriptor spelling and cache configuration in the [root models/configuration reference](../../../references/models-and-configuration.md). |
| `Downloaded file is corrupted, please retry` | Downloaded model archive checksum did not match the release checksum | Delete the incomplete model directory for that descriptor, verify network stability, and rerun. Do not reuse a cache that failed checksum validation. |
| `No checksum for model ...` | Descriptor/model name is not present in the configured release checksum index | Use a supported descriptor such as `spleeter:2stems`, `spleeter:4stems`, `spleeter:5stems`, or a valid local JSON config/model directory. Check custom model-provider variables in the root models/configuration reference. |
| TensorFlow logs warn about missing CUDA, cuDNN, TensorRT, or GPU libraries | TensorFlow sees no usable GPU acceleration; CPU execution is still the verified baseline | Treat GPU as optional acceleration only. Continue on CPU if the command otherwise works. Do not claim GPU verification unless the active TensorFlow runtime actually lists and uses a GPU. |
| Process is killed or runs out of memory | Long duration, 4/5-stem model, MWF, large batch, or TensorFlow memory pressure | Retry with a short `--duration` smoke segment, disable `--mwf`, process one file at a time, choose 2-stem if suitable, and ensure sufficient RAM/swap. |
| `spleeter` command is not found or behaves differently on Windows | Console entry-point wrapper can be unavailable or broken | Use `python -m spleeter ...` instead of the `spleeter` shortcut. Keep paths quoted. |
| Apple Silicon import/runtime failures | TensorFlow compatibility can be the limiting factor on Apple Silicon | Use a Python/TensorFlow combination supported by the installed Spleeter version, or use a CPU/x86_64/remote runtime known to import TensorFlow 2.12.x successfully. Treat local GPU acceleration as optional and unverified. |
| Custom adapter import fails | Dotted path is not importable, class name is wrong, or class does not subclass `AudioAdapter` | Import the class in a Python shell, confirm `issubclass(CustomAdapter, AudioAdapter)`, and ensure its `load` and `save` methods match the base signatures. |
| Non-WAV codec fails during save | System ffmpeg build lacks the requested encoder or rejects the selected bitrate/container combination | Retry with `--codec wav` to separate the Spleeter path from encoder issues. Then install/enable the required ffmpeg encoder or choose a different codec/bitrate. |

## Collision-safe filename checklist

Before executing a batch, inspect the `--filename_format` value:

- Includes `{instrument}`: prevents stems from the same input colliding.
- Includes `{filename}` or `{foldername}` for more than one input: prevents different songs from overwriting each other.
- Includes `{codec}` or a literal extension matching `--codec`: keeps output names clear.
- Does not start with an absolute path and does not contain parent-directory escapes unless the user intentionally wants outputs outside `--output_path`.

Recommended templates:

```text
{filename}/{instrument}.{codec}
{filename}_{instrument}.{codec}
{foldername}/{filename}_{instrument}.{codec}
```

## Minimal recovery smoke command

When a complex command fails, reduce it to this form:

```bash
python -m spleeter separate \
  --params_filename spleeter:2stems \
  --output_path separated_smoke \
  --duration 10 \
  --codec wav \
  input_audio_file
```

If this succeeds, add back custom filename templates, non-WAV codecs, MWF, custom adapters, longer durations, and multiple files one at a time.
