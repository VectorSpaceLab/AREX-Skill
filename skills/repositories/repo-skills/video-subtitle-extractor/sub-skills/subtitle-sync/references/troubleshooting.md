# Subtitle Sync Troubleshooting

## Missing files

The CLI validates source, destination, subtitle, keyframe, timecode, and chapter
paths. Check all paths before running; the command builder can show the exact
command without mutating files.

## ffmpeg or demux tools missing

Full synchronization needs media demuxing/audio extraction. Install ffmpeg and,
for some containers/features, mkvtoolnix or scxvid-compatible keyframe tools as
needed. `--help` does not prove those tools exist.

## Wrong output path

The GUI output path is destination-video stem plus subtitle extension in the
destination directory. CLI `-o/--output` overrides it. Avoid overwriting the
source subtitle unless explicitly requested.

## Bad sync or broken segments

- Increase `--max-window` or adjust `--rewind-thresh` for difficult drift.
- Use chapter/keyframe/timecode inputs for variable frame rate or chaptered
  sources.
- Use `--verbose` to inspect shift decisions.
- Preserve temp files with `--no-cleanup` only for debugging.
