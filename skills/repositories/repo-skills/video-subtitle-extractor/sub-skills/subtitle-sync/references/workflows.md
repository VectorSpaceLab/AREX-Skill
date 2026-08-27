# Subtitle Synchronization Workflows

## GUI Sync Timeline

The GUI Sync Timeline page asks for:

- Source video: the video that currently matches the subtitle file.
- Source subtitle: `.srt` or `.ass` file to shift.
- Destination video: the video to align to.

The GUI builds an output path beside the destination video with the destination
stem and source subtitle extension, then starts the Sushi runner.

## CLI workflow

From a VSE source environment:

```bash
python -m backend.sushi --src source.mkv --dst destination.mkv --script source.srt -o synced.srt
```

Use the command builder before running:

```bash
python sub-skills/subtitle-sync/scripts/sushi_command_builder.py \
  --src source.mkv --dst destination.mkv --script source.srt --output synced.srt
```

## High-level helper behavior

The `subtitle_sync` helper identifies the subtitle argument, chooses the larger
of two videos as BD and smaller as HD, uses ffmpeg to create temporary WAV files,
runs Sushi, then deletes temporary WAV files. Because it uses shell ffmpeg calls
and deletes temp files, prefer explicit CLI planning and validate paths before
running.

## When to use keyframes/timecodes/chapters

Use keyframe, timecode, FPS, or chapter options when source/destination timing
is complex, variable frame rate, or chapter-offset related. Keep ordinary sync
runs minimal first.
