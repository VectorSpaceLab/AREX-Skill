# TTS Data Formats

Use this reference before preparing NeMo Speech TTS, MagpieTTS, G2P, vocoder, or audio-codec data. The formats below are distilled from NeMo TTS docs, dataset source, configs, and tests.

## Core JSONL Rules

NeMo TTS manifests are JSON Lines files:

- One JSON object per line.
- No blank lines for regular NeMo manifests.
- Keep training, validation, and test manifests separate.
- Prefer UTF-8 text and avoid control characters.
- Relative audio paths are normally resolved against the dataset `audio_dir` in newer dataset metadata or against the manifest/config convention in older workflows; make the base directory explicit in configs.
- Use WAV for the most tested path. Other audio formats can work through the runtime audio stack but add dependency and codec risk.
- Provide durations in seconds as positive finite numbers. Durations drive filtering, batching, bucketing, progress estimates, and long-tail outlier detection.

Run the bundled checker before long jobs:

```bash
python scripts/check_tts_manifest.py train.jsonl --mode tts --require-audio --min-duration 0.1 --max-duration 30
```

Use `--check-files` when the manifest is local and file existence checks are safe:

```bash
python scripts/check_tts_manifest.py train.jsonl --mode tts --require-audio --check-files --audio-base-dir wavs
```

## Classic TTS Manifest

Classic FastPitch, aligner, vocoder, and many TTS dataset paths use records like:

```json
{"audio_filepath": "wavs/example.wav", "text": "The raw transcript.", "normalized_text": "the normalized transcript", "speaker": 5, "duration": 3.42}
```

Fields:

| Field | Required | Meaning | Notes |
| --- | --- | --- | --- |
| `audio_filepath` | Training/eval yes; inference no | Utterance audio file | Can be absolute or relative to configured base/audio directory |
| `text` | Usually yes | Grapheme, phoneme, or mixed transcript | Empty text is invalid for TTS training and most inference |
| `normalized_text` | Optional | Pre-normalized text that bypasses or supplements normalization | Must not contradict `text` semantically |
| `speaker` or `speaker_id` | Multispeaker yes | Integer or stable speaker label | Keep type consistent across splits |
| `duration` | Strongly recommended; often required | Duration in seconds | Filter out too-short and too-long utterances |
| `mel_filepath` | Optional | Precomputed mel path for vocoder/acoustic workflows | Should match sample rate/hop/mel settings |
| `offset` | Optional | Start offset into audio | Must be non-negative |

Classic config surfaces:

- `model.train_ds.dataset.manifest_filepath` and `model.validation_ds.dataset.manifest_filepath` for `TTSDataset`-style configs.
- `train_dataset` and `validation_dataset` top-level Hydra values in several FastPitch/HiFi-GAN configs.
- `sup_data_path` for supplementary pitch, energy, duration, and alignment-prior material.
- `sup_data_types` commonly includes `align_prior_matrix`, `pitch`, and sometimes `energy`.

## FastPitch Data

FastPitch training and finetuning commonly need:

- Audio waveform paths and transcripts.
- Duration filtering such as `min_duration=0.1` and a task-specific max duration.
- Mel/STFT settings aligned with the checkpoint or intended vocoder.
- Pitch settings (`pitch_fmin`, `pitch_fmax`, `pitch_norm`, `pitch_mean`, `pitch_std`).
- Optional speaker IDs for multispeaker checkpoints.
- Supplementary alignment priors and pitch extracted before training for alignment-enabled recipes.

Tokenizer alignment matters more than manifest shape:

- ARPABET checkpoints expect ARPABET-style phoneme tokens.
- IPA checkpoints expect IPA-style phoneme tokens.
- Grapheme checkpoints expect raw or normalized text tokens.
- Mixed grapheme/phoneme tokenizers may intentionally mix word forms, but the manifest should not randomly switch between incompatible conventions across records.

## HiFi-GAN/Vocoder Data

Vocoder manifests use waveform files and may include precomputed mel paths:

```json
{"audio_filepath": "wavs/example.wav", "duration": 3.42, "mel_filepath": "mels/example.npy"}
```

Rules:

- If `mel_filepath` is present, it must have been generated with mel parameters compatible with the vocoder config.
- If mels are computed on the fly, sample rate, hop length, FFT/window size, and mel count come from config.
- Training uses waveform segments, so duration outliers and leading/trailing silence affect stability.
- Do not reuse a vocoder trained for one sample rate with mels produced for another sample rate unless the config and checkpoint explicitly support it.

## MagpieTTS Manifest

MagpieTTS uses `TextToSpeechDataset`, `MagpieTTSDataset`, or Lhotse variants with dataset metadata. Minimum manifest fields for supervised finetuning usually look like:

```json
{"audio_filepath": "target.wav", "text": "Transcript to synthesize.", "duration": 5.2, "context_audio_filepath": "context.wav", "context_text": "Reference audio transcript", "target_audio_codes_path": "codes/target.pt", "context_audio_codes_path": "codes/context.pt", "language": "en"}
```

Fields:

| Field | Required | Meaning | Notes |
| --- | --- | --- | --- |
| `audio_filepath` | Training/eval yes | Target utterance audio | Relative to `audio_dir` unless absolute |
| `text` or `normalized_text` | Yes | Target transcript | Lhotse path prioritizes `normalized_text` when present |
| `duration` | Strongly recommended | Target utterance duration | Used for filters and batching |
| `context_audio_filepath` | Voice cloning/context yes | Reference speaker audio | Should match the target speaker for voice adaptation |
| `context_audio_duration` | Optional | Context duration | Useful for sanity checks against min/max context |
| `context_text` | Optional but important | Transcript/style text for context audio | Required for text-conditioning-heavy paths |
| `target_audio_codes_path` | Optional cache | Precomputed codec tokens for target audio | Must match codec checkpoint and segmenting convention |
| `context_audio_codes_path` | Optional cache | Precomputed codec tokens for context audio | Used when `load_cached_codes_if_available=true` |
| `speaker`, `speaker_id`, or Lhotse supervision speaker | Often useful | Speaker identity | Keep target and context speaker consistent |
| `language` | Multilingual yes | Language code, e.g. `en`, `es`, `de`, `ja` | Drives tokenizer selection and long-form thresholds |
| `tokenizer_names` | Dataset-meta/Lhotse optional | Candidate tokenizer keys | Must exist under `model.text_tokenizers` |

Context rules:

- The context audio should usually come from the same speaker as the target audio.
- A context duration of roughly 3–10 seconds is the common range distilled from Magpie evidence; finetuning patterns often pin 5 seconds.
- If context audio is shorter than desired, some loaders repeat/slice it; this is convenient but can hide poor context choices.
- If cached codes are missing or `load_cached_codes_if_available=false`, training/inference computes codes from waveform and requires codec dependencies and extra compute.
- If cached code paths are present, verify they were produced from already-segmented audio. Source comments warn not to double-apply start/duration when loading temporal arrays.

Dataset metadata for Magpie configs:

```yaml
train_ds_meta:
  en_sft:
    manifest_path: train.jsonl
    audio_dir: audio
    feature_dir: features
    sample_weight: 1.0
    tokenizer_names: [english_phoneme]
val_ds_meta:
  en_val:
    manifest_path: val.jsonl
    audio_dir: audio
    feature_dir: features
    sample_weight: 1.0
    tokenizer_names: [english_phoneme]
```

For multilingual finetuning, add one `train_ds_meta` entry per language and adjust `sample_weight` to upsample low-resource languages.

## MagpieTTS Inference Dataset Config

The Magpie inference script reads a dataset JSON config rather than only a raw manifest. A self-contained config shape is:

```json
{
  "eval_set": {
    "manifest_path": "eval_manifest.jsonl",
    "audio_dir": "audio",
    "feature_dir": "features",
    "sample_weight": 1.0,
    "tokenizer_names": ["english_phoneme"],
    "whisper_language": "en"
  }
}
```

Operational notes:

- `--datasets_json_path` points to this JSON.
- `--datasets_base_path` can make paths inside the JSON relative to a known base.
- `--datasets eval_set,other_set` filters the JSON keys.
- Evaluation fields such as `whisper_language` and `load_cached_codes_if_available` are stripped before dataset construction by the inference runner.
- If `--run_evaluation` is enabled, the manifest must contain target/context data needed by CER, WER, speaker-similarity, and quality metrics.

## G2P Manifest

G2P training, evaluation, and inference use JSONL records with grapheme and phoneme fields:

```json
{"text_graphemes": "Swifts, flushed from chimneys.", "text": "ˈswɪfts, ˈfɫəʃt ˈfɹəm ˈtʃɪmniz."}
```

Defaults:

- `text_graphemes`: grapheme input field.
- `text`: ground-truth phoneme field for training/evaluation.
- `pred_text`: common prediction output field for inference.

Rules:

- For inference-only G2P, phoneme labels may be absent; use `--mode g2p --allow-missing-phonemes` in the bundled checker.
- For training/evaluation, require both grapheme and phoneme fields.
- Keep punctuation policy consistent with the config (`add_punctuation`, lowercase settings, tokenizer choices).
- Sentence-level G2P can include OOV and heteronym contexts; do not strip punctuation blindly if the model was trained with punctuation.

## Audio Codec Dataset Metadata

Codec training configs use dataset metadata rather than only `manifest_filepath` fields:

```yaml
train_ds_meta:
  my_codec_data:
    manifest_path: train.jsonl
    audio_dir: audio
    sample_weight: 1.0
```

Rules:

- Audio codec data is waveform-heavy. Validate durations before training.
- Match config sample rate to the target codec/checkpoint: common configs include 16 kHz, 22.05 kHz, 24 kHz, and 44.1 kHz.
- Segment duration and min-duration filters must be compatible. Tests assert that too-short cuts are rejected for fixed segment training.
- If using Lhotse or tarred/webdataset-style paths, verify shard strategy and DDP behavior before large training.

## Text, Phoneme, and Normalization Pitfalls

- `text` and `normalized_text` should not encode different utterances. If both exist, `normalized_text` may take precedence in some loaders.
- Grapheme and phoneme fields should not silently mix. If a manifest has `phonemes` plus raw grapheme `text`, document which field the model config uses.
- Phoneme tokenizers often use language-specific inventories. IPA and ARPABET are not interchangeable.
- Heteronyms should be resolved through a dictionary/G2P/aligner path, not by random per-record edits.
- Keep punctuation policy aligned with training. Removing all punctuation can hurt long-form sentence splitting and G2P context.
- Speaker fields should use one type and naming convention across train/validation/test.
- Language codes should match tokenizer keys and long-form thresholds.
- Context audio/text must match the intended speaker/style. A mismatched context can sound like the wrong speaker even when target text is correct.

## Validation Checklist

Before training or inference:

1. Run `python scripts/check_tts_manifest.py ...` in the appropriate mode.
2. Confirm split separation: training and validation manifests are not the same file and do not duplicate most audio paths.
3. Check duration outliers and remove or route extreme long-form examples intentionally.
4. Check empty text, whitespace-only text, repeated spaces, digits, and punctuation policy.
5. Check path base semantics: `audio_dir`, `feature_dir`, absolute paths, and relative paths are intentional.
6. Check tokenizer/G2P style against the checkpoint/config.
7. For MagpieTTS, check context audio/text, cached-code compatibility, codec path, language, and tokenizer names.
8. For evaluation, check that target/context references required by metrics are present and local model/cache policy is acceptable.
