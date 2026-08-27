# TTS Model Overview

This reference summarizes NeMo Speech TTS model families and how to choose among them. It distills repository evidence from the TTS docs, example configs/scripts, TTS model source, and TTS tests into self-contained runtime guidance.

## Choose the Model Family

| Task | Prefer | Why | Watch for |
| --- | --- | --- | --- |
| Quick single-speaker waveform from text with released checkpoints | FastPitch + HiFi-GAN | Stable cascaded path: acoustic model generates mel-spectrograms, vocoder converts mels to waveform | Acoustic model and vocoder sample rates/tokenization must match |
| Multi-speaker FastPitch or voice adaptation with mels | FastPitch finetuning | Supports speaker IDs, pitch/energy/align priors, reference specs in configs | Needs manifests, supplementary data, GPU, careful tokenizer/G2P choice |
| Neural LLM-style TTS, voice cloning, multilingual generation, context audio/text | MagpieTTS | Encoder-decoder model over discrete audio codec tokens with attention priors and CFG | Requires codec model, context metadata, checkpoint-specific flags, GPU for practical use |
| Decoder-only Magpie checkpoints | EasyMagpieTTS | Decoder-only inference/training path with phoneme input controls | Use `--model_type easy_magpie` and legacy CAS/text-conditioning flags when needed |
| Pronunciation generation or heteronym/OOV support | G2P T5 or G2P-Conformer | Converts graphemes to phonemes for TTS training/inference control | Requires G2P manifests with grapheme and phoneme fields; ASR collection is a dependency |
| Codec token generation for MagpieTTS training | AudioCodecModel | Trains or restores neural audio codec over waveform/mel features | Heavy training path; sample rate and codebook layout must match TTS checkpoint |
| Mel-to-waveform training or adaptation | HiFi-GAN | Adversarial vocoder trained on waveform/mel pairs | Needs matching mels, sample rate, and GPU; checkpoint mismatch causes distorted audio |
| Heteronym disambiguation with speech/text aligner | AlignerModel | Uses aligner evidence to choose pronunciations | Optional-heavy and language/dictionary dependent |
| Voice conversion from disentangled content/speaker embeddings | SSL FastPitch | Experimental SSL TTS path | Requires SSL supplementary data and configs |

## Cascaded TTS Concepts

NeMo cascaded TTS is a three-stage pipeline:

1. Text analysis converts written text into grapheme or phoneme tokens. It can include text normalization, dictionary lookup, heteronym handling, and G2P.
2. Acoustic modeling converts tokens into acoustic features, normally mel-spectrograms. FastPitch is the main parallel acoustic model and can condition on pitch, speaker, and optional reference features.
3. Vocoding converts mel-spectrograms into waveform audio. HiFi-GAN is the primary vocoder and should be selected to match sample rate and mel feature settings.

Minimal FastPitch/HiFi-GAN API contract:

```python
import soundfile as sf
import torch
import nemo.collections.tts as nemo_tts

spec_generator = nemo_tts.models.FastPitchModel.from_pretrained("tts_en_fastpitch")
vocoder = nemo_tts.models.HifiGanModel.from_pretrained(model_name="tts_en_hifigan")
spec_generator.eval()
vocoder.eval()

with torch.no_grad():
    tokens = spec_generator.parse("This is a NeMo text to speech test.")
    spectrogram = spec_generator.generate_spectrogram(tokens=tokens)
    audio = vocoder.convert_spectrogram_to_audio(spec=spectrogram)

sf.write("speech.wav", audio.squeeze().detach().cpu().numpy(), 22050)
```

Operational checks:

- Use `restore_from("model.nemo")` for local `.nemo` checkpoints and `from_pretrained("model_name")` for registry/cache-backed names.
- `from_pretrained()` may download; confirm network/cache policy before using it.
- Put both models in eval mode and wrap generation in `torch.no_grad()`.
- Set `speaker=0` or another valid integer in `generate_spectrogram()` for multispeaker FastPitch checkpoints.
- Keep FastPitch text tokenizer/G2P style aligned with the checkpoint. ARPABET, IPA, grapheme, and mixed-token checkpoints are not interchangeable.
- Keep HiFi-GAN sample rate and mel preprocessing compatible with the spectrogram generator. Mismatched 22050/44100 Hz or mel parameters can produce noisy or chipmunked output.

## MagpieTTS Concepts

MagpieTTS is an encoder-decoder transformer TTS model over discrete audio codec tokens. It is designed for robust voice-cloning-style synthesis with context audio or context text. It uses CTC loss and attention priors to encourage monotonic text/audio alignment and reduce repeated, skipped, or hallucinated words.

Core ideas:

- The text encoder processes transcript tokens. Phoneme-based checkpoints use an IPA/G2P tokenizer; character/byte checkpoints can operate on raw text.
- The decoder autoregressively predicts audio codec tokens and attends to text and context.
- Context audio provides speaker/voice characteristics. Context text can condition style or provide text-only context depending on checkpoint type.
- Classifier-free guidance is controlled at inference by `use_cfg` plus `cfg_scale`.
- Attention priors can be enabled for more robust alignment on challenging or out-of-distribution text.
- Frame stacking and the Local Transformer can accelerate inference for checkpoints trained with that architecture.
- MaskGit-style local decoding can be used when the checkpoint and config support it.
- Long-form inference chunks sentence-level text and preserves context across chunks; it is best supported for English.

Common Magpie inference defaults from the source:

| Parameter | Typical default | Meaning |
| --- | ---: | --- |
| `max_decoder_steps` | `500` | Max autoregressive steps before forced termination |
| `temperature` | `0.7` | Sampling temperature; `0.0` selects deterministic argmax paths where supported |
| `topk` | `80` | Top-k token sampling cutoff |
| `cfg_scale` | `2.5` | Strength of classifier-free guidance when `--use_cfg` is enabled |
| `apply_attention_prior` | true in model parameters, explicit in runner config | Biases cross-attention toward monotonic alignment |
| `longform_mode` | `auto` in long-form docs | Auto, always, or never use chunked long-form generation |

Use MagpieTTS when the task mentions voice cloning, context audio, long-form synthesis, multilingual LLM-based TTS, old Magpie checkpoints, codec tokens, preference optimization, or evaluation with CER/speaker similarity.

## EasyMagpieTTS Concepts

EasyMagpieTTS is the decoder-only Magpie path. Use it when the checkpoint or user explicitly says EasyMagpie, decoder-only, phoneme input type, or old EasyMagpie text-conditioning/CAS behavior.

Important inference choices:

- Select `--model_type easy_magpie` in the inference script contract.
- Use `--phoneme_input_type gt` when the dataset already contains ground-truth phoneme inputs, or `predicted` when the model should predict phonemes.
- Use `--phoneme_sampling_method argmax` for deterministic phoneme selection or `multinomial` for sampled phoneme predictions.
- Use `--disable_cas_for_context_text` for legacy EasyMagpie checkpoints whose context text path predates CAS embedding behavior.
- Use `--phoneme_tokenizer_path` only when overriding a broken or moved tokenizer path stored in the checkpoint config.

## Audio Codec Models

NeMo Audio Codec models encode audio or mel features into discrete token sequences used by MagpieTTS. They use convolutional encoder/quantizer/decoder components and RVQ or FSQ quantization. Training configs include 16 kHz, 22.05 kHz, 24 kHz, and 44.1 kHz variants.

Treat audio codec work as heavy and checkpoint-sensitive:

- Training requires GPU/CUDA and enough audio coverage for the target sample rate.
- The codec model path must match MagpieTTS checkpoint expectations for codebook size, number of codebooks, downsampling/frame rate, and special-token layout.
- Cached `target_audio_codes_path` and `context_audio_codes_path` in Magpie manifests avoid on-the-fly encoding but must have been produced by a compatible codec.
- Codec training examples are reference-only for future agents unless the user explicitly wants a long training run.

## G2P Models

NeMo TTS G2P covers:

- ByT5 G2P: text-to-text model suited to flexible grapheme-to-phoneme conversion.
- G2P-Conformer CTC: smaller non-autoregressive model that is faster for inference.
- Sentence-level G2P training to handle OOV words and heteronyms in context.
- Dictionary/IPA/ARPABET helper modules used by TTS tokenizers.

Use G2P when the user needs pronunciations, phoneme manifests, heteronym handling, IPA/ARPABET conversion, or when TTS quality problems trace to grapheme-vs-phoneme mismatch.

## Checkpoint Loading and Compatibility

General loading patterns:

```python
import nemo.collections.tts as nemo_tts

fastpitch = nemo_tts.models.FastPitchModel.restore_from("fastpitch.nemo")
hifigan = nemo_tts.models.HifiGanModel.from_pretrained("tts_en_hifigan")
available = nemo_tts.models.FastPitchModel.list_available_models()
```

For unknown local `.nemo` files, restore with the concrete class expected by that checkpoint. If only the file is known, inspect its config in a caller-owned environment to find the `target` class rather than guessing.

Magpie legacy codebook layouts:

- New checkpoints read codec codebook size, number of codebooks, and downsampling from the codec checkpoint and size special-token embeddings automatically.
- Old checkpoints from before the April 2025 layout change may need `--legacy_codebooks` in Magpie inference or forced Hydra overrides.
- Decoder-context legacy layout with 2048 tokens uses audio BOS/EOS at 2046/2047 and context audio BOS/EOS at 2044/2045.
- Multi-encoder/single-encoder legacy layout with 2048 tokens uses audio and context audio BOS/EOS at 2046/2047.
- A short-lived invalid 2018-token layout overwrote codec tokens and should usually be rejected rather than forced.
- Legacy EasyMagpie text conditioning may require `--legacy_text_conditioning` or `--disable_cas_for_context_text` depending on the checkpoint path.

## Evaluation Surfaces

TTS evaluation can include:

- CER/WER from an ASR model over generated audio.
- Speaker similarity against target or context audio through TitaNet or WavLM-style speaker verification.
- UTMOSv2, Frechet Codec Distance, end-of-utterance metrics, PESQ, and related audio quality metrics.
- Real-time factor and FLOP summaries for Magpie inference.

These metrics may require optional ASR, speaker verification, Hugging Face, audio, or CUDA dependencies and sometimes model downloads. For offline or restricted environments, prefer local model paths and explicitly document skipped metrics.
