# Media and Minigame Troubleshooting

## SoundDodge

Symptoms:

- `soundcard` import fails.
- Monitoring starts but no dodge/counter events fire.
- The task triggers too often or not enough.

Likely causes:

- No audio service/device on the host.
- Default microphone or loopback capture device is unavailable.
- Threshold values are too low or too high.
- The task is not running in the foreground controller mode required by the game/audio path.

Actions:

- Treat Linux headless `soundcard` failures as environment warnings, not proof of a source bug.
- Adjust `SoundDodgeThreshold` and `SoundCounterThreshold` in small steps.
- Check whether `SoundDodgeEnableConfig` and `SoundDodgeModeConfig` attach nodes are actually enabled/disabled as expected.

## Rhythm

Symptoms:

- The song selector never finds the target song.
- The play loop does not press keys in time.
- The task exits from results or song-select unexpectedly.

Likely causes:

- Song title mismatch or wrong OCR/recognition text.
- Rhythm config values differ from the built-in defaults.
- Drum templates are missing or only partially available.
- FPS/latency assumptions are too aggressive for the host.

Actions:

- Confirm the target song and the selected auto/manual mode.
- Check `rhythm_config.json` if present.
- Keep the requested FPS realistic; raising it too far can make event scheduling unstable.
- Inspect the scene gate state transitions before changing detector thresholds.

## AutoPiano

Symptoms:

- Import fails on Linux.
- Notes are not sent to the game window.
- MIDI file path or speed/transpose parsing fails.

Likely causes:

- Windows-only `ctypes.windll` bridge.
- Window title not found.
- Invalid MIDI path or unsupported note mapping.
- Bad custom parameters passed through `custom_action_param`.

Actions:

- Validate the MIDI file path first.
- Keep the target song path relative to the repo or explicitly absolute.
- If you only need to verify parsing, use static import/help checks, not live keystroke simulation.

## Tetris

Symptoms:

- The AI never finds a valid move.
- Piece detection keeps repeating the same signature.
- Vitality detection stops the task too early.

Likely causes:

- Scene/detector templates are stale.
- Board or queue detection is out of sync.
- The chosen mode or speed-drop setting conflicts with the current board state.

Actions:

- Use the Tetris play logic's debug output and check template availability.
- Do not remove `tasker.stopping` checks or widen every threshold at once.

## BagelSpam

Symptoms:

- LLM generation returns empty title/body.
- API request fails.
- Text mode cannot find preset titles/bodies.

Likely causes:

- Missing API key or wrong endpoint.
- Network/API incompatibility.
- The screenshot is too empty or the prompt is too strict.
- Title/body lists are not split into usable pairs.

Actions:

- Validate the API endpoint and key before debugging the Pipeline branch.
- Use preset mode for offline validation.
- When changing the LLM prompt, keep the output JSON contract stable.

## AutoFScroll

Symptoms:

- The helper does nothing obvious.
- It keeps running after the user wants to stop.

Actions:

- Remember this helper assumes the user already started the relevant interaction.
- Check task stop behavior and make sure the surrounding task releases the key/scroll state on exit.
