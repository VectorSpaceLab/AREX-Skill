# Media and Minigame Workflows

## SoundDodge

Task: `SoundDodge`, entry `SoundDodgeMain`, controller `Win32-Front`.

Behavior:

- Reads enabled config values from attach nodes and/or task parameters.
- Creates an audio listener and dodger, starts monitoring, and reacts to dodge or counter events.
- Optionally runs in dodge-only or dodge+counter mode.

Task options:

- `SoundDodgeEnable`: global on/off.
- `SoundDodgeAllAttacks`: use dodge for both attack and counter sounds.
- `SoundDodgeThreshold`: attack threshold.
- `SoundCounterThreshold`: counter threshold.

Important implementation facts:

- The audio listener depends on `soundcard` and a host audio backend.
- The task is foreground-oriented.
- Use precise threshold explanations in troubleshooting; lower thresholds are more sensitive.

## Rhythm

Task: `Rhythm`, entry `RhythmEntrance`.

Behavior:

- Auto song selection can choose a target song or a predefined default.
- Auto repeat can use a fixed count or repeat until vitality is exhausted.
- The play loop analyzes drum templates and schedules key presses in sync with lane timing.

Task options:

- `自动选曲`: auto-select on/off.
- `演奏目标歌曲选择`: manual target song.
- `自动连打`: enable repeat logic.
- `连打模式`: max vs fixed repeat.
- `连打次数`: fixed repeat count.
- `目标帧率`: playback loop FPS.

Important implementation facts:

- Rhythm config is read from a runtime JSON when present; otherwise built-in defaults apply.
- Drum detection uses OpenCV template matching and candidate scheduling, not OCR.
- The `SceneGate` and `DrumDetector` components are separate from the task JSON option plumbing.

## AutoPiano

Task: `AutoPiano`, entry `AutoPiano`, custom action `auto_play_piano`.

Task options:

- The visible task JSON wires the default song/speed/transpose values through `custom_action_param`.
- The action itself also supports `key_mode`, `tracks`, and `out_of_range_mode` settings.

Implementation facts:

- The keyboard bridge uses Windows message APIs and a direct window title lookup.
- MIDI parsing and note scheduling happen in the AutoPiano module tree.
- A Linux import check can validate module presence but cannot prove keyboard injection works.

## Tetris

Task: `Tetris`, entry `TetrisEntrance`.

Behavior:

- Uses a custom AI player with scene detection, board evaluation, and input scheduling.
- Supports single-round or repeat behavior, optional speed drop, and vitality detection.
- Ends the task when vitality is exhausted or the requested round count is reached.

Task options:

- `TetrisAutoRepeat_Single`
- `TetrisAllowSpeedDrop`

## BagelSpam

Task: `BagelSpam`, entry `BagelSpamEntrance`, controller `Win32-Front`.

Behavior:

- Optionally takes a photo before posting.
- Can use preset title/body mode or LLM generation mode.
- Uses an OpenAI-compatible endpoint and API key in LLM mode.
- Limits publish count via `BagelSpamPublishCount`.

Implementation facts:

- `BagelSpamLLMGenerate` is a CustomRecognition that converts the screenshot to base64 and calls a multimodal chat/completions API.
- `BagelSpamOutputText` chooses the output title/body pair or falls back to task-provided text lists.
- The LLM path is not safe for offline verification unless a mock endpoint is explicitly supplied.

## AutoFScroll

Task: `AutoFScroll`, entry `AutoFScroll`.

Behavior:

- Pure custom-action helper for holding F and scrolling to pick items faster.
- No extra task options in the current catalog.
- Simple behavior, but still depends on the user's current in-game context because it assumes the action should remain active while held.
