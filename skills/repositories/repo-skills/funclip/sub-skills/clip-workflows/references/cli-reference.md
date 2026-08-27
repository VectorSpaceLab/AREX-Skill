# FunClip CLI reference

This page summarizes the command-line surfaces used by the clip workflow.

## 1) Gradio launcher: `funclip/launch.py`

```bash
python funclip/launch.py [--lang zh|en] [--model paraformer|fun-asr-nano|sensevoice] [--share] [--port PORT] [--listen]
```

Flags:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `-l`, `--lang` | Language mode | Defaults to `zh`. Use `en` for the English Paraformer branch. |
| `-m`, `--model` | ASR model family | Defaults to `paraformer`. Choices are `paraformer`, `fun-asr-nano`, and `sensevoice`. |
| `-s`, `--share` | Public Gradio share link | Only creates a share tunnel when explicitly set. |
| `-p`, `--port` | Listening port | Defaults to `7860`. |
| `--listen` | Bind all interfaces | Sets Gradio to `0.0.0.0` and disables the local frontend/browser probe. |

Model selection rules:

- `-m fun-asr-nano` loads the FunAudioLLM Fun-ASR-Nano checkpoint.
- `-m sensevoice` loads SenseVoice.
- `-m paraformer` uses the Paraformer branch selected by `-l`.
- `-l en` does not override `-m fun-asr-nano` or `-m sensevoice`; it only changes the Paraformer branch and the runtime language setting.

Examples:

```bash
python funclip/launch.py
python funclip/launch.py -m fun-asr-nano
python funclip/launch.py -m sensevoice
python funclip/launch.py -l en
python funclip/launch.py --listen --port 7860
python funclip/launch.py --listen --share --port 7860
```

## 2) CLI runner: `funclip/videoclipper.py`

```bash
python funclip/videoclipper.py --stage 1|2 --file MEDIA [--sd_switch no|yes] [--output_dir DIR] [--dest_text TEXT] [--dest_spk SPK] [--start_ost MS] [--end_ost MS] [--output_file PATH] [--lang zh|en]
```

Supported input suffixes:

- Audio: `.wav`, `.mp3`, `.aac`, `.m4a`, `.flac`
- Video: `.mp4`, `.avi`, `.mkv`, `.flv`, `.mov`, `.webm`, `.ts`, `.mpeg`

Flag details:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--stage` | CLI stage | `1` recognizes, `2` clips using the saved stage-1 state. |
| `--file` | Input media | Must use one of the supported suffixes. |
| `--sd_switch` | Speaker diarization | Use `yes` if you want speaker IDs in stage 1 and later speaker clipping. |
| `--output_dir` | State/output directory | Stage 1 writes recognition artifacts here; stage 2 reads them back. Create parent directories first if needed. |
| `--dest_text` | Target text | Used for text clipping in stage 2. Separate multiple phrases with `#`. |
| `--dest_spk` | Target speaker | Used for speaker clipping in stage 2. Separate multiple speaker ids with `#`. |
| `--start_ost` | Start offset (ms) | Applied after the match is found. Can be negative or positive. |
| `--end_ost` | End offset (ms) | Applied after the match is found. Can be negative or positive. |
| `--output_file` | Final clip path | Audio stage 2 expects a `.wav` path. Video stage 2 uses the base name and appends an internal `_noN` suffix when written. |
| `--lang` | Stage-1 language | Chooses the Chinese or English Paraformer branch for CLI recognition. |

Stage 1 examples:

```bash
python funclip/videoclipper.py --stage 1 \
  --file ./your_video.mp4 \
  --sd_switch no \
  --output_dir ./funclip-output

python funclip/videoclipper.py --stage 1 \
  --file ./your_audio.wav \
  --sd_switch yes \
  --output_dir ./funclip-output
```

Stage 2 examples:

```bash
python funclip/videoclipper.py --stage 2 \
  --file ./your_video.mp4 \
  --output_dir ./funclip-output \
  --dest_text 'hello world' \
  --start_ost 0 \
  --end_ost 100 \
  --output_file ./funclip-output/result.mp4

python funclip/videoclipper.py --stage 2 \
  --file ./your_video.mp4 \
  --output_dir ./funclip-output \
  --dest_spk spk0#spk3 \
  --start_ost -200 \
  --end_ost 300 \
  --output_file ./funclip-output/speaker.mp4
```

Stage behavior:

- Stage 1 stores recognition state for reuse by stage 2.
- Stage 2 loads that state and reuses it for text or speaker matching.
- Stage 2 audio clipping writes a `.wav` file and a matching `.srt` file.
- Stage 2 video clipping writes an `.mp4` file and a matching `.srt` file.
- If no match is found, FunClip returns the original audio or no video output instead of raising a matching error.

## 3) Practical deployment reminders

- Use `--listen` on remote or container hosts when you need all interfaces bound.
- Add `--share` only when you want a public Gradio tunnel.
- Keep `output_dir` writable; the CLI runner uses a simple directory creation path and does not create missing parent directories for nested paths.
- Use the Gradio UI for mixed interactive work, and the CLI runner when you want deterministic stage 1/2 processing with saved state.
