# Subtitle Sync API Reference

## Parser entry points

`backend.sushi.__main__.create_arg_parser()` defines the Sushi command-line
interface. `parse_args_and_run(cmd_keys)` parses a list of CLI tokens, installs
logging, and calls `run(args)`.

## High-level helper

`backend.sushi.sushi_main.subtitle_sync(argv, opts=None)` accepts two videos and
a subtitle path, creates temporary WAV files with ffmpeg, chooses output beside
the larger destination video, calls the parser, and deletes the temporary WAVs.
Use it carefully because it shells out and mutates temp files.

## Core algorithm surfaces

The bundled Sushi package parses SRT/ASS scripts, demuxes audio, computes audio
alignment shifts, optionally uses chapters/keyframes/timecodes, smooths shifts,
and writes shifted subtitle events. Algorithm details live in the bundled source
package; this skill exposes the operational flags and failure modes needed for
agent use.
