# FunClip workflows

This page gives concrete, copyable workflows for the common FunClip paths covered by this sub-skill.

## 1) Launch FunClip in Gradio

Use the default Paraformer path for Chinese clipping:

```bash
python funclip/launch.py
```

Choose the ASR backend when needed:

```bash
python funclip/launch.py -m fun-asr-nano
python funclip/launch.py -m sensevoice
python funclip/launch.py -l en
```

Deployment flags:

```bash
python funclip/launch.py --listen --port 7860
python funclip/launch.py --listen --share --port 7860
```

Notes:

- `-m` selects the model family. It overrides the default Paraformer choice.
- `-l en` selects the English Paraformer branch when `-m` stays at its default.
- `--listen` binds the server to `0.0.0.0` and disables the local browser/frontend probe.
- `--listen` does **not** create a public Gradio link. Add `--share` only when you explicitly want one.
- In the UI, blank `output_dir` behaves like no output directory. Nonblank values are resolved to an absolute path and created when needed.

## 2) Gradio ASR then clip

Typical interactive flow:

1. Upload a video or audio file.
2. Optionally add hotwords.
3. Choose whether to run ASR only or ASR plus speaker diarization.
4. Copy the text segment you want, or enter a speaker id such as `spk0`.
5. Set start/end offsets in milliseconds.
6. Click **Clip** or **Clip+Subtitles**.

Useful patterns:

- Repeated text: separate multiple target phrases with `#`.
- Speaker clipping: use `spk0`, `spk1`, or `spk0#spk3` after diarized recognition.
- Offsets are applied in milliseconds after the text or speaker match is found.
- ASCII matching is case-insensitive; Chinese text still needs normalized spacing and punctuation handling.

## 3) CLI stage 1/2 workflow

Create an output directory first if you want a nested path:

```bash
mkdir -p ./funclip-output
```

Stage 1 recognition:

```bash
python funclip/videoclipper.py --stage 1 \
  --file ./your_media.mp4 \
  --sd_switch yes \
  --output_dir ./funclip-output
```

Stage 2 clipping by text:

```bash
python funclip/videoclipper.py --stage 2 \
  --file ./your_media.mp4 \
  --output_dir ./funclip-output \
  --dest_text 'hello world' \
  --start_ost 0 \
  --end_ost 100 \
  --output_file ./funclip-output/result.mp4
```

Stage 2 clipping by speaker:

```bash
python funclip/videoclipper.py --stage 2 \
  --file ./your_media.mp4 \
  --output_dir ./funclip-output \
  --dest_spk spk0#spk3 \
  --start_ost -200 \
  --end_ost 300 \
  --output_file ./funclip-output/speaker.mp4
```

What stage 1 writes into `output_dir`:

- `total.srt`
- `recog_res_raw`
- `timestamp`
- `sentences`
- `sd_sentences` when speaker diarization is enabled

What stage 2 writes:

- Audio clips: a `.wav` file plus a `.srt` companion.
- Video clips: an `.mp4` file plus a `.srt` companion.
- Video clips are renamed with an internal `_noN` suffix when written.

## 4) Programmatic clipping

A direct Python flow from a FunClip checkout usually looks like this. The source files use top-level imports, so add the checkout's `funclip/` directory to `sys.path` before importing helpers:

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path("funclip").resolve()))

from launch import create_asr_model
from videoclipper import VideoClipper

model = create_asr_model("paraformer", "zh")
clipper = VideoClipper(model)
clipper.lang = "zh"

text, srt, state = clipper.video_recog("./your_video.mp4", sd_switch="yes")
clip_path, message, clip_srt = clipper.video_clip(
    "your target text",
    0,
    100,
    state,
    add_sub=True,
    output_dir="./funclip-output",
)
```

Use `timestamp_list` when you already have explicit clip boundaries, such as from LLM output. In that path, FunClip skips text matching and speaker matching and uses the supplied timestamps directly.

## 5) Subtitle generation workflow

- `Clip+Subtitles` overlays subtitles with the bundled font and MoviePy's `TextClip`/`SubtitlesClip` path.
- Subtitle overlay depends on the local ffmpeg/ImageMagick/font setup.
- `generate_srt` writes the full transcript SRT.
- `generate_srt_clip` writes the clipped SRT and the subtitle overlay cues for the current clip.
- Long sentences may be split into smaller subtitle chunks when they exceed the internal duration or token limits.

## 6) Sentence-info compatibility

Fun-ASR-Nano and SenseVoice paths should keep working even when token-level timestamps are missing, as long as `funasr>=1.3.29` is installed.

- If `sentence_info` is present, FunClip uses it for subtitles and clipping.
- If `sentence_info` is empty but a top-level `timestamp` exists, FunClip synthesizes a usable sentence list from that timestamp.
- This is the compatibility path that keeps speaker and subtitle workflows usable for recent FunASR outputs.
