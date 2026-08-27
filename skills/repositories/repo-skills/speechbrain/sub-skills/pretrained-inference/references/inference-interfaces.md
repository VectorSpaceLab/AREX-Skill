# SpeechBrain inference interface reference

Use this reference to pick the right `speechbrain.inference` class and call shape. Signatures below were verified from the installed package snapshot used for this skill.

## Loading API shared by inference classes

Most inference classes inherit `speechbrain.inference.interfaces.Pretrained`.

```python
Class.from_hparams(source, hparams_file="hyperparams.yaml", **kwargs)
```

Important forwarded keyword arguments include:

- `savedir`: local directory for fetched hparams/checkpoints/code.
- `run_opts`: runtime options such as `{"device": "cpu"}` or `{"device": "cuda"}`.
- `overrides`: HyperPyYAML overrides for the model config.
- `download_only`: fetch files without constructing/loading the interface.
- `local_strategy`: `LocalStrategy.SYMLINK`, `COPY`, `COPY_SKIP_CACHE`, or `NO_LINK`.
- `fetch_config`: `FetchConfig(overwrite=False, allow_updates=False, allow_network=True, token=False, revision=None, huggingface_cache_dir=None)`.

`Pretrained.load_audio(path, savedir=None)` accepts a local path, URL, or Hugging Face-style reference, loads audio through SpeechBrain audio I/O, and applies the model's `audio_normalizer`.

## Interface matrix

| Workflow | Class | Common methods | Notes |
| --- | --- | --- | --- |
| Encoder-decoder ASR | `speechbrain.inference.ASR.EncoderDecoderASR` | `transcribe_file(path, **kwargs)`, `transcribe_batch(wavs, wav_lens)`, `encode_batch(wavs, wav_lens)` | Returns words and token ids for batches; file API returns one transcription string. |
| Encoder/CTC ASR | `speechbrain.inference.ASR.EncoderASR` | `transcribe_file(path, **kwargs)`, `transcribe_batch(wavs, wav_lens)` | Uses a tokenizer and decoding function from hparams. |
| Whisper ASR | `speechbrain.inference.ASR.WhisperASR` | `transcribe_file(path, task=None, initial_prompt=None, ...)` | Returns segment objects; supports chunking and optional streaming path. |
| Streaming ASR | `speechbrain.inference.ASR.StreamingASR` | `transcribe_file(path, dynchunktrain_config, use_torchaudio_streaming=True)` | Requires a dynamic chunk training config. |
| Speech LLM ASR | `speechbrain.inference.ASR.SpeechLLMASR` | class-specific generation/transcription methods | Check hparams/model requirements carefully. |
| Classification | `speechbrain.inference.classifiers.EncoderClassifier` | `classify_file(path, **kwargs)`, `classify_batch(wavs, wav_lens=None)`, `encode_batch(wavs, wav_lens=None, normalize=False)` | Speaker-id, language-id, emotion, keyword spotting. |
| Audio classification | `speechbrain.inference.classifiers.AudioClassifier` | `classify_batch(wavs, wav_lens=None)` | Audio-tag/classifier interface. |
| Speaker verification | `speechbrain.inference.speaker.SpeakerRecognition` | `verify_files(path_x, path_y, **kwargs)`, `verify_batch(wavs1, wavs2, wav1_lens=None, wav2_lens=None, threshold=0.25)` | Returns similarity/decision-style outputs depending on model. |
| Spectral enhancement | `speechbrain.inference.enhancement.SpectralMaskEnhancement` | `enhance_file(filename, output_filename=None, **kwargs)`, `enhance_batch(noisy, lengths=None)` | Can write output audio when `output_filename` is provided. |
| Waveform enhancement | `speechbrain.inference.enhancement.WaveformEnhancement` | `enhance_file(filename, output_filename=None, **kwargs)`, `enhance_batch(noisy, lengths=None)` | Direct waveform model path. |
| Separation | `speechbrain.inference.separation.SepformerSeparation` | `separate_file(path, savedir=None)`, `separate_batch(mix)` | Produces separated sources. |
| VAD | `speechbrain.inference.VAD.VAD` | `get_speech_segments(audio_file, large_chunk_size=30, small_chunk_size=10, ...)` | Boundary post-processing has many thresholds. |
| TTS | `speechbrain.inference.TTS.Tacotron2`, `MSTacotron2`, `FastSpeech2`, `FastSpeech2InternalAlignment` | class-specific synthesis methods | Usually paired with a vocoder. |
| Vocoders | `speechbrain.inference.vocoders.HIFIGAN`, `DiffWaveVocoder`, `UnitHIFIGAN` | waveform synthesis methods | Match to acoustic model output representation. |
| G2P | `speechbrain.inference.text.GraphemeToPhoneme` | `g2p(text)`, callable wrapper | Accepts a string or list of strings. |
| SLU/ST/S2UT | `EndToEndSLU`, `EncoderDecoderS2UT` | class-specific decode/translate methods | Confirm task-specific hparams. |
| Custom pretrained code | `foreign_class(...)` | returns requested custom class instance | Executes fetched Python; trusted sources only. |

## Method selection tips

- Use file-level methods (`transcribe_file`, `classify_file`, `enhance_file`, `verify_files`, `separate_file`) for one-off audio paths.
- Use batch methods when you already have tensors and relative lengths. The typical `wav_lens` shape is `[batch]` with `1.0` for the longest item and shorter items as `len / max_len`.
- Use `load_audio` to normalize sample rate/channels to the model's training convention before batch methods.
- For text-only G2P, use `GraphemeToPhoneme.g2p(text)` or call the object directly.
- For profiling or memory measurements, do not run full pretrained downloads until the model source, device, batch sizes, and duration grid are approved.
