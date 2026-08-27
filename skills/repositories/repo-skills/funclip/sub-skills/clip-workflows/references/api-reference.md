# FunClip API reference

This page records the signatures and state assumptions used by the clip workflow.

## Launcher helpers

### `create_asr_model(model_name, lang, auto_model_cls=AutoModel)`

Returns an ASR model instance configured for one of the supported launch-time model families.

Behavior:

- `model_name == "fun-asr-nano"` loads `FunAudioLLM/Fun-ASR-Nano-2512` with remote-code support, `fsmn-vad`, `cam++`, and `hub="hf"`.
- `model_name == "sensevoice"` loads `iic/SenseVoiceSmall` with `fsmn-vad` and `cam++`.
- Any other value falls back to the Paraformer branch.
- Paraformer uses the Chinese SeACo checkpoint when `lang == "zh"` and the English Paraformer checkpoint otherwise.
- `lang` does not override the `fun-asr-nano` or `sensevoice` model family choice.

### `build_launch_kwargs(*, share, port, listen)`

Returns the exact Gradio launch keyword arguments.

- Default result: `{"share": share, "server_port": port, "server_name": "127.0.0.1"}`.
- When `listen` is true, it changes the host to `0.0.0.0` and adds `inbrowser=False` and `_frontend=False`.
- It preserves the caller's `share` choice; it does not auto-enable public sharing.

## `VideoClipper`

### `VideoClipper(funasr_model)`

Stores a FunASR-compatible model object. The model must expose `generate(...)` with the arguments used by the recognition path.

### `recog(self, audio_input, sd_switch='no', state=None, hotwords='', output_dir=None)`

Recognizes raw audio and builds a clipping state.

Expected input:

- `audio_input` is a `(sample_rate, ndarray)` pair.
- The audio may be float or integer PCM; the helper normalizes it to float64.
- Non-16000 Hz audio is resampled to 16 kHz.
- Multi-channel audio uses the first channel only.

Returned value:

- `(res_text, res_srt, state)`

State keys:

- `audio_input`
- `recog_res_raw`
- `timestamp`
- `sentences`
- `sd_sentences` when speaker diarization is enabled

Recognition compatibility notes:

- When `sd_switch == 'Yes'`, FunClip asks FunASR for speaker results and uses them to populate `sd_sentences`.
- When token-level timestamps are missing but a top-level timestamp is present, FunClip synthesizes a usable sentence list so clipping and subtitles still work.
- SenseVoice and Fun-ASR-Nano paths depend on the compatibility behavior added in `funasr>=1.3.29`.

### `clip(self, dest_text, start_ost, end_ost, state, dest_spk=None, output_dir=None, timestamp_list=None)`

Clips audio using the saved recognition state.

Expected state keys:

- `audio_input`
- `recog_res_raw`
- `timestamp`
- `sentences`
- `sd_sentences` when speaker clipping is requested

Parameters:

- `dest_text` may contain multiple phrases separated by `#`.
- An individual phrase may include bracket offsets such as `text[0, 100]`.
- `dest_spk` may contain multiple speaker ids separated by `#`.
- `timestamp_list` bypasses text and speaker matching entirely and is used by AI clip flows.

Important semantics:

- ASCII matching is case-insensitive because the matcher lowercases ASCII before comparing.
- Chinese matching still depends on the normalized text produced by `pre_proc`.
- If no match is found, the original audio is returned unchanged.
- Speaker matches require `sd_sentences`; each speaker segment must be longer than 999 ms to be kept.

Returned value:

- `((sr, res_audio), message, clip_srt)`

### `video_recog(self, video_filename, sd_switch='no', hotwords='', output_dir=None)`

Recognizes the audio track from a video file and returns the same `(text, srt, state)` shape as `recog`.

State keys also include:

- `video_filename`
- `clip_video_file`
- `video`

Notes:

- The video must have an audio stream.
- The helper extracts audio to a temporary WAV file, loads it at 16 kHz, and removes the temporary file afterward.

### `video_clip(self, dest_text, start_ost, end_ost, state, font_size=32, font_color='white', add_sub=False, dest_spk=None, output_dir=None, timestamp_list=None)`

Clips video using the recognition state.

Expected state keys:

- `recog_res_raw`
- `timestamp`
- `sentences`
- `video`
- `clip_video_file`
- `video_filename`
- `sd_sentences` when speaker clipping is used

Behavior notes:

- `add_sub=True` overlays subtitles with the bundled font and MoviePy subtitle objects.
- `output_dir` controls where the clip is written.
- The implementation appends an internal `_noN` suffix when it writes video clips.
- When `sentences` is a string in English mode, it is split before subtitle generation.
- `timestamp_list` bypasses text and speaker matching and is interpreted as explicit boundaries.

Returned value:

- `(clip_video_file, message, clip_srt)`

## CLI convenience runner

### `runner(stage, file, sd_switch, output_dir, dest_text, dest_spk, start_ost, end_ost, output_file, config=None, lang='zh')`

This is the CLI convenience wrapper used by `funclip/videoclipper.py`.

Behavior:

- `stage == 1` performs recognition and writes the saved state to `output_dir`.
- `stage == 2` loads that state and performs clipping.
- `lang` selects the CLI recognition branch for stage 1.
- `config` is accepted by the signature but is not used in the current implementation.
- Input files are classified by suffix into audio or video categories.

## Subtitle and matching helpers

### `pre_proc(text)`

Normalizes text for matching by removing punctuation and spacing Chinese characters more explicitly.

### `proc(raw_text, timestamp, dest_text, lang='zh')`

Finds text matches in the recognition transcript and returns sample-based timestamp ranges.

- ASCII matching is case-insensitive.
- Return value is a list of `[start_sample, end_sample]` pairs.

### `proc_spk(dest_spk, sd_sentences)`

Finds speaker segments for a target speaker id such as `spk0`.

- Returns sample-based timestamp ranges.
- Ignores very short segments shorter than about one second.

### `convert_pcm_to_float(data)`

Converts integer PCM or float arrays to float64.

### `generate_srt(sentence_list)`

Builds a full transcript SRT string from a sentence list.

### `generate_srt_clip(sentence_list, start, end, begin_index=0, time_acc_ost=0.0)`

Builds the clipped SRT string and subtitle overlay cues for the current clip.

- Returns `(srt_total, subs, next_index)`.
- Long subtitle sentences are split when they exceed internal duration or token limits.

### `time_convert(ms)`

Formats milliseconds into SRT-style timestamps.

### `str2list(text)`

Tokenizes Chinese characters and word-like ASCII chunks for subtitle rendering.

### `extract_timestamps(text)`

Parses bracketed `[start-end]` timestamps used by AI clip outputs and returns millisecond pairs.
