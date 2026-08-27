# ASR, ST, SSL, and Whisper Workflows

## ASR Model Families

- **Conformer / Transformer**: main modern ASR path. Supports attention and CTC-style decoding choices. Online variants accept `--num_decoding_left_chunks` for streaming-like chunk context.
- **DeepSpeech2 online/offline**: legacy CTC/RNN family. Some variants use external language model resources for beam search.
- **TALCS code-switch**: use `--lang zh_en --codeswitch True` with matching TALCS tags.
- **Whisper**: separate command family for multilingual transcription, translation, and language detection.
- **SSL models**: Wav2Vec2, Hubert, and WavLM can be used for ASR or representation extraction depending on `--task`.

## Recipe Structure

Most ASR/ST examples follow a staged shell recipe pattern:

1. Set environment with `path.sh`, `cmd.sh`, and parse-options helpers.
2. Stage 0 prepares data, manifests, CMVN, vocabularies, or tokenizer files.
3. Stage 1 trains or fine-tunes the model.
4. Stage 2 averages checkpoints.
5. Stage 3 evaluates or decodes.

Treat these recipes as planning evidence unless the user explicitly asks to run them. They can download datasets, require Kaldi-style tools, use GPUs, and take a long time.

## Decoding Decisions

- Use `attention_rescoring` for strong conformer/transformer ASR defaults when supported.
- Use `ctc_greedy_search` for fast CTC-only smoke checks.
- Use `ctc_prefix_beam_search` when beam search behavior matters.
- For online conformer variants, tune `num_decoding_left_chunks`; lower values reduce context and can reduce accuracy.

## Audio Input Expectations

- Prefer mono WAV.
- Most commands expect 16 kHz audio.
- Use the bundled `validate_audio_inputs.py` helper to detect obvious duration/sample-rate mismatches before downloads.
- `--yes` can accept automatic sample-rate transformation, but a reproducible workflow should record whether resampling changed the input.

## ST and Kaldi Dependencies

Speech translation uses Kaldi-style fbank/pitch feature extraction. Default ST execution can download `kaldi_bins` into the model cache and then modify process `PATH` / `LD_LIBRARY_PATH` for the current run. Do not run ST in a restricted environment without acknowledging that side effect.

## Whisper Resource Notes

Whisper can download model checkpoints and auxiliary resource data. Use smaller sizes (`tiny`, `base`) for initial smoke runs. Use `--language` only when the user wants to force a decode language; otherwise let the model detect language.
