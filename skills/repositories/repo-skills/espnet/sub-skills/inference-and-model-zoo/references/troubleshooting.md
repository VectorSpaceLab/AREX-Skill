# Inference and Model-zoo Troubleshooting

## Local model failures

- **Missing config/model path**: run `check_model_files.py` first.
- **Config/checkpoint mismatch**: ensure the model file and config came from the same task family and training run.
- **Wrong class**: ASR, streaming ASR, TTS, enhancement, speaker, diarization, SVS, ST, S2T, and S2ST entrypoints are not interchangeable.
- **Vocoder failure**: TTS/S2ST/SVS may need a compatible `vocoder_config`/`vocoder_file` or a `vocoder_tag`.
- **Device error**: set `device="cpu"` for CPU-safe smoke checks; CUDA requires separate backend verification.

## Model-zoo and pretrained failures

- `from_pretrained(model_tag=...)` may download from model-zoo/Hugging Face or read a local cache.
- If offline, ask for local config/checkpoint files instead of repeatedly trying network calls.
- If a tag is ambiguous, inspect `espnet_model_zoo` metadata or ask the user for the exact model tag and task.
- Do not upload, package for publication, or start a Gradio demo without approval.

## Performance and decoding issues

- High `beam_size`, `nbest`, LM/ngram weights, quantization flags, and batch size affect memory and speed.
- Streaming ASR has different chunk/repetition/length constraints than offline ASR.
- Enhancement/separation may need segment/hop settings for long audio.
