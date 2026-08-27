# TTS API Reference

## Verified Entry Points

- `mlx_audio.tts.utils.load_model(model_path, lazy=False, strict=True, **kwargs)`
- `mlx_audio.tts.generate.generate_audio(text, model=None, max_tokens=1200, voice='af_heart', prompt=None, instruct=None, speed=1.0, lang_code='en', cfg_scale=None, ddpm_steps=None, sigma=None, ref_audio=None, ref_text=None, stt_model='mlx-community/whisper-large-v3-turbo-asr-fp16', output_path=None, file_prefix='audio', audio_format='wav', join_audio=False, play=False, verbose=True, temperature=0.7, stream=False, streaming_interval=2.0, save=False, use_zero_spk_emb=False, **kwargs)`

## Common Input Fields

- `text`: source text to synthesize
- `voice`: voice preset or speaker label
- `prompt` / `instruct`: model-specific conditioning
- `ref_audio`: path or list of paths to a reference clip
- `ref_text`: transcript or list of transcripts
- `stt_model`: fallback transcription model for reference audio
- `stream` / `streaming_interval`: low-latency output control
- `save` / `join_audio` / `output_path` / `file_prefix`: output routing and file layout

## Important Behavior

- `--stream` implies playback.
- `--save` is only valid when streaming is enabled.
- Repeated `ref_audio` and `ref_text` values must align in length.
- Some models preserve reference audio paths and perform their own preprocessing.
- Some model families accept additional kwargs such as `gen_duration`, `steps`, `stg_scale`, `sigma`, or `use_zero_spk_emb`.

## Model-Family Notes

- Qwen3-TTS can require both `ref_audio` and `ref_text`.
- OmniVoice is sensitive to reference preprocessing; transcribe the preprocessed clip, not the raw file.
- CSM / MisoTTS, Spark, OuteTTS, Chatterbox, and Ming Omni support voice cloning through their own reference inputs.
