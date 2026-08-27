# VAD and Realtime

## Verified VAD Surface

- `mlx_audio.realtime_vad.parse_turn_detection(turn_detection)`
- `mlx_audio.realtime_vad.ServerVadConfig`
- `mlx_audio.realtime_vad.StreamingVad`
- `mlx_audio.realtime_vad.TurnDetector`
- `mlx_audio.realtime_vad.TurnEventKind`

## Default Server VAD

`server_vad` defaults match the OpenAI-style values used by the package:

- threshold: `0.5`
- prefix padding: `300` ms
- silence duration: `500` ms

`semantic_vad` is rejected; the package only implements `server_vad` style turn detection.

## Practical Behavior

- `TurnDetector` is the pure state machine.
- `StreamingVad` buffers raw samples until a full VAD frame is available.
- The server route uses this logic for realtime turn detection and auto-commit.
- A bad sample rate will usually show up as garbled realtime transcription rather than a clean parser error.

## Model Families

- Silero VAD is the default server-side turn detector.
- Sortformer families belong to diarization-style workflows.
- Enhancement and separation models live in the STS family, not in the VAD state machine itself.
