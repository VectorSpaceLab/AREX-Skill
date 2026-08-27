# Fine-tuning JSONL data formats

This reference is self-contained for selecting and validating MOSS-TTS fine-tuning JSONL rows. Use `scripts/validate_training_jsonl.py` before codec preprocessing and again on prepared JSONL when data is assembled from multiple shards.

## Task ids handled by this sub-skill

Use these ids with the bundled validator:

- `moss-tts`: standard Delay/Local text-to-speech and single-reference voice cloning rows.
- `local-v15`: MOSS-TTS Local Transformer v1.5 rows with codec-v2, full language names, and a fixed 12-RVQ layout.
- `ttsd`: multi-speaker dialogue/continuation rows for MOSS-TTSD; when using the public TTSD v1.0 base, keep `n_vq=16` consistently.
- `soundeffect-v1`: autoregressive SoundEffect v1 rows using `ambient_sound` prompts.
- `voice-generator`: rows using `text` plus `instruction` to describe the target voice.
- `realtime`: MOSS-TTS-Realtime conversation records with user/assistant turns.

SoundEffect v2 DiT fine-tuning is intentionally out of scope; route it to `../soundeffect-v2/SKILL.md`.

## Common row concepts

### Raw rows

Raw rows point to audio files and are input to `prepare_data.py`.

- Non-Realtime tasks use top-level `audio` as the target training audio path.
- Realtime uses `conversations[*].wav` for every turn and optional top-level `ref_wav` for the assistant voice reference.
- Relative paths are safest when they are relative to the JSONL file for Local v1.5. For Delay, Local, and Realtime helpers, launch from the same directory assumed by the manifest or use unambiguous paths.

### Prepared rows

Prepared rows contain codec output and can be passed directly to `sft.py`.

- Non-Realtime tasks require `audio_codes` with shape `[time][n_vq]`.
- Single-reference voice cloning usually has `ref_audio_codes` with shape `[time][n_vq]`.
- Multi-reference TTSD rows use `reference_audio_codes`, a list whose elements are either `[time][n_vq]` code matrices or `null` placeholders.
- Realtime rows require `conversations[*].audio_codes`; `ref_audio_codes` is required if `ref_wav` was provided and training will not keep a codec loaded.

Do not mix code depths across target and reference fields. `audio_codes`, `ref_audio_codes`, and every non-null element of `reference_audio_codes` must have the same `n_vq` in a row.

## Schemas by task

### `moss-tts`: standard TTS and single-reference voice cloning

Required raw fields:

```jsonl
{"audio":"data/utt0001.wav","text":"Actually, I noticed that I am very sensitive to other people's emotions.","language":"English"}
{"audio":"data/utt0002.wav","text":"Speak this line in the reference voice.","ref_audio":"data/ref.wav","language":"English"}
```

Required meaning:

- `audio`: target speech path unless `audio_codes` is already present for direct training.
- `text`: transcript or synthesis text.
- `ref_audio`: optional single reference path for voice cloning.
- `reference_audio`: accepted as a reference-audio alias when needed.
- `reference`: accepted by the shared dataset path, but reserve list-valued `reference` and `null` placeholders for TTSD unless the selected model family explicitly expects them.
- `language`: optional; full names such as `English`, `Chinese`, or `French` are preferred for newer v1.5-family checkpoints. Legacy Local examples may use short tags such as `en`.
- `tokens`, `quality`, `sound_event`, `ambient_sound`, and `instruction` are forwarded if present, but for ordinary TTS they should be intentional rather than accidental leftovers from another task.

Prepared fields:

```jsonl
{"audio":"data/utt0002.wav","text":"Speak this line in the reference voice.","ref_audio":"data/ref.wav","audio_codes":[[11,12]],"ref_audio_codes":[[21,22]],"language":"English"}
```

The real code matrices are much longer; the miniature values above show only shape.

### `local-v15`: Local Transformer v1.5

Raw examples:

```jsonl
{"audio":"data/en.wav","text":"This is a clean English training line.","language":"English"}
{"audio":"data/zh.wav","text":"请用同一个声音说出这句话。","ref_audio":"data/ref.wav","language":"Chinese"}
```

Rules:

- Use model family Local Transformer v1.5 and codec-v2.
- `audio` is required for preprocessing unless a prepared row already contains `audio_codes`.
- `text` is the public required text-like field.
- `language` is optional but strongly recommended; use full language names.
- `ref_audio` is the documented single-reference field. It should be a single string, not a list.
- `reference_audio` is accepted as a preprocessing alias.
- `reference` is a compatibility field, not the public v1.5 multi-speaker workflow; do not use multi-reference or `null` lists here unless you have separate model evidence.
- Prepared `audio_codes` must match the checkpoint's fixed RVQ count, normally 12.
- The codec internally targets 48 kHz stereo. Input files may be mono or another sample rate; the processor handles loading and normalization.

### `ttsd`: MOSS-TTSD multi-speaker/dialog continuation

Raw example:

```jsonl
{"audio":"data/dialog_target.wav","text":"[S1] This is speaker one. [S2] This is speaker two. [S1] Continue with speaker one.","reference":["data/s1_ref.wav",null],"language":"English"}
```

Rules:

- `audio` is the target continuation/dialogue audio.
- `text` should preserve the speaker tags expected by the prompt template, such as `[S1]` and `[S2]`, when the dataset uses them.
- `reference` may be a list. Each element is either a reference audio path string or `null`; `null` means that speaker has no cloning reference and must remain a placeholder.
- `prepare_data.py` preserves `null` entries as `None` while encoding the non-null reference paths.
- `ref_audio` remains a single-reference field. Do not put a TTSD speaker list in `ref_audio`.
- When using the public TTSD v1.0 base, pass `--n-vq 16` to both preprocessing and training, and keep the support code/prompt template, prepared JSONL, checkpoint, and inference path on the same TTSD-compatible implementation. Mixing them can make the training loss look normal while inference becomes gibberish.

Prepared TTSD rows use `audio_codes` plus `reference_audio_codes`:

```jsonl
{"audio":"data/dialog_target.wav","text":"[S1] ...","reference":["data/s1_ref.wav",null],"audio_codes":[[1,2]],"reference_audio_codes":[[[3,4]],null],"language":"English"}
```

### `soundeffect-v1`: autoregressive SoundEffect v1

Raw examples:

```jsonl
{"audio":"data/rain.wav","ambient_sound":"Rolling thunder with steady rainfall."}
{"audio":"data/footsteps.wav","ambient_sound":"Clear footsteps echoing on concrete at a steady rhythm.","tokens":160}
```

Rules:

- `audio`: target sound-effect audio.
- `ambient_sound`: required text-like condition for v1.
- `tokens`: optional positive integer duration/length control.
- `sound_event` and `quality` may be forwarded if the task design uses them.
- Do not use this schema for SoundEffect v2 DiT fine-tuning.

### `voice-generator`: text plus voice instruction

Raw examples:

```jsonl
{"audio":"data/old_man.wav","text":"My old back is really giving me trouble these days.","instruction":"A tired, hoarse elderly voice complaining slowly with a faint groan."}
{"audio":"data/tavern.wav","text":"Hey there, stranger!","instruction":"Hearty, jovial tavern owner's voice, loud and welcoming with a slightly gruff tone."}
```

Rules:

- `audio`: target speech audio.
- `text`: words to speak.
- `instruction`: required voice/style condition.
- `language` and `tokens` are optional when useful.
- Reference audio fields are not the primary interface for this task; use them only if the selected model prompt explicitly combines instruction and reference conditioning.

### `realtime`: conversation rows

Raw single-turn example:

```jsonl
{"id":"000001","ref_wav":"data/ref0.wav","conversations":[{"role":"assistant","text":"Actually, I noticed that I am very sensitive to other people's emotions.","wav":"data/utt0001.wav"}]}
```

Raw multi-turn example:

```jsonl
{"id":"000003","ref_wav":"data/ref0.wav","conversations":[{"role":"user","text":"Hey, I just landed in Paris. Any ideas?","wav":"data/user_utt0001.wav"},{"role":"assistant","text":"Nice, welcome to Paris! Six hours is perfect for a short city walk.","wav":"data/assistant_utt0001.wav"},{"role":"user","text":"Just a backpack.","wav":"data/user_utt0002.wav"},{"role":"assistant","text":"Then start near the Seine and keep the walk relaxed.","wav":"data/assistant_utt0002.wav"}]}
```

Rules:

- Top-level `conversations` is required and must be a non-empty list.
- Each turn has `role` (`user` or `assistant`), `text`, and raw `wav` before preprocessing.
- At least one assistant turn is required. Records with no assistant turn are skipped by preprocessing and unusable for supervised training.
- Assistant turns are the labeled targets. User turns provide context; a final user-only turn has no response target.
- Optional top-level `ref_wav` is the assistant voice reference. All assistant turns should be the same speaker as `ref_wav`; user turns may be different speakers.
- Prepared rows place `audio_codes` inside each conversation turn and top-level `ref_audio_codes` when `ref_wav` was encoded.
- Realtime uses 16 audio channels/codebooks internally. Prefer prepared turn codes shaped `[time][16]`.

## Optional field validation rules

- `language`: string when present; prefer full names for v1.5-family checkpoints.
- `tokens`: integer greater than zero when present.
- `audio_codes`, `ref_audio_codes`: 2-D integer lists. Avoid transposed non-Realtime codes; use `[time][n_vq]`.
- `reference_audio_codes`: either a single 2-D code matrix, a list of 2-D matrices, or for TTSD a list containing 2-D matrices and `null` placeholders.
- URI-like audio references are acceptable only if your runtime loader can read them; local-file existence checks should be skipped or replaced with dataset acquisition checks for URI manifests.
