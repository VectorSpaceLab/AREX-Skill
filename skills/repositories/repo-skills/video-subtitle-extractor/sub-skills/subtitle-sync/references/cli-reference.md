# Sushi CLI Reference

Required flags:

- `--src <filename>`: source audio/video.
- `--dst <filename>`: destination audio/video.
- `--script <filename>`: subtitle file to shift.

Common output/control flags:

- `-o, --output <filename>`: output subtitle path.
- `--temp-dir <dir>`: temporary demux folder.
- `--no-cleanup`: keep demuxed streams.
- `-v, --verbose`: verbose logging.

Alignment options:

- `--window`, `--max-window`, `--rewind-thresh` tune search/recovery.
- `--no-grouping` disables event grouping and error recovery.
- `--max-kf-distance`, `--kf-mode {shift,snap,all}` control keyframe snapping.
- `--smooth-radius` controls median smoothing.
- `--max-ts-duration`, `--max-ts-distance` tune typesetting grouping.

Media stream/metadata options:

- `--src-audio`, `--dst-audio`, `--src-script` select streams.
- `--chapters`, `--dst-keyframes`, `--src-keyframes` provide external metadata.
- `--dst-fps`, `--src-fps`, `--dst-timecodes`, `--src-timecodes` handle frame
  rate/timecode cases.
