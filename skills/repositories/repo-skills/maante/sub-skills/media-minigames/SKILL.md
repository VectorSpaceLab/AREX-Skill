---
name: media-minigames
description: "Guides MaaNTE audio, rhythm, MIDI, Tetris, BagelSpam, and
  AutoFScroll automation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Media and Minigames

## Use This When

Use this sub-skill for MaaNTE features where audio, music, rhythm, or lightweight minigame automation is the core task:

- `SoundDodge` audio dodge/counter.
- `Rhythm` / auto rhythm play and select-song logic.
- `AutoPiano` MIDI playback.
- `Tetris` AI and vitality handling.
- `BagelSpam` photo/text/LLM post generation.
- `AutoFScroll` quick pickup.

For general gameplay menus or task options, return to [../gameplay-tasks/SKILL.md](../gameplay-tasks/SKILL.md). For underlying Python action mechanics, return to [../custom-actions/SKILL.md](../custom-actions/SKILL.md).

## Read First

1. [references/media-workflows.md](references/media-workflows.md) for task behavior, options, and key implementation facts.
2. [references/troubleshooting.md](references/troubleshooting.md) for audio, MIDI, Windows-key, and minigame-specific failures.
3. [../../references/task-catalog.md](../../references/task-catalog.md) for the task table and option names.
4. Use the bundled helper scripts when you need safe file/input checks:
   - `scripts/check_midi_file.py`
   - `../../scripts/check_maante_environment.py --summary`

## General Notes

- Audio workflows are sensitive to host services and devices. A Linux import check does not prove PulseAudio/PipeWire capture or Windows loopback behavior.
- Rhythm and Tetris live loops should respect `context.tasker.stopping` and avoid unbounded sleep loops without stop checks.
- AutoPiano uses Windows keyboard message injection in the bridge layer; it is not a pure cross-platform library workflow.
- BagelSpam may run in preset mode or LLM mode. LLM mode depends on an OpenAI-compatible HTTP endpoint and API key; keep that dependency explicit.
- AutoFScroll is a simple holding/scrolling helper, but its usefulness depends on the user already holding F to activate the action in-game.

## Validation

Safe checks:

```bash
python scripts/check_midi_file.py path/to/file.mid
python ../../scripts/check_maante_environment.py --summary
```

Live verification requires the appropriate game mode/window and should be short, bounded, and user-approved. Use a tiny song, one rhythm round, one Tetris round, one BagelSpam post generation, or one audio threshold check rather than a long farm loop.
