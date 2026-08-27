# Preprocessing JSONL into trainable codec codes

Use this reference when a task needs to turn raw MOSS-TTS training manifests into prepared JSONL rows with discrete audio-code fields. The generated skill bundles a safe validator, but it does **not** bundle the repository's full GPU/model-download preprocessing programs; use the option contracts below with the matching preprocessing entry point in the user's active MOSS-TTS checkout or an equivalent training implementation.

## Pick the preprocessing family

| Family / task | Entry point to choose in the user's training checkout | Default model | Default codec | Notes |
|---|---|---|---|---|
| Delay / MOSS-TTS v1.5, TTSD, SoundEffect v1, VoiceGenerator | Delay-family preprocessing program | `OpenMOSS-Team/MOSS-TTS-v1.5` unless task-specific | `OpenMOSS-Team/MOSS-Audio-Tokenizer` | Shared Delay-family pipeline. For TTSD v1.0, keep prompt templates/code compatible with the TTSD checkpoint and pass `--n-vq 16`. |
| Local Transformer legacy | Local-family preprocessing program | `OpenMOSS-Team/MOSS-TTS-Local-Transformer` | `OpenMOSS-Team/MOSS-Audio-Tokenizer` | Same JSONL family as Delay. |
| Local Transformer v1.5 | Local v1.5 preprocessing program | `OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5` | `OpenMOSS-Team/MOSS-Audio-Tokenizer-v2` | Codec weight dtype is `fp32`; compute dtype can be `bf16`/`fp16`/`fp32`; fixed RVQ depth is normally 12. |
| Realtime | Realtime preprocessing program | not used in preprocessing | `OpenMOSS-Team/MOSS-Audio-Tokenizer` | Encodes every assistant-audio turn and optional prompt/reference audio; records without assistant turns are skipped. |

## Validate before preprocessing

Run the bundled validator from this sub-skill before launching codec/model work. It imports only the Python standard library.

```bash
# From this sub-skill directory, or replace <this sub-skill> with its installed path.
python scripts/validate_training_jsonl.py train_raw.jsonl \
  --task moss-tts \
  --mode raw \
  --base-dir .
```

Useful variants:

```bash
# Validate a prepared Local v1.5 JSONL and enforce the default 12-codebook depth.
python scripts/validate_training_jsonl.py train_with_codes.jsonl \
  --task local-v15 --mode prepared --format json

# Validate TTSD prepared data; defaults to checking n_vq=16 for coded fields.
python scripts/validate_training_jsonl.py prepared/dialog.rank00000-of-00008.jsonl \
  --task ttsd --mode prepared

# Validate URI-heavy manifests without local file existence checks.
python scripts/validate_training_jsonl.py manifest.jsonl \
  --task realtime --mode raw --no-exists-check
```

## Single-process preprocessing option contracts

The exact script/program path depends on the user's checkout or training package. Keep these option contracts together when constructing the command.

### Delay / MOSS-TTS / TTSD / SoundEffect v1 / VoiceGenerator

```bash
python <delay-family-preprocess-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-v1.5 \
  --codec-path OpenMOSS-Team/MOSS-Audio-Tokenizer \
  --device auto \
  --input-jsonl train_raw.jsonl \
  --output-jsonl train_with_codes.jsonl
```

For TTSD v1.0-style rows, add `--n-vq 16` and carry the same value into SFT:

```bash
python <delay-family-preprocess-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTSD-v1.0 \
  --codec-path OpenMOSS-Team/MOSS-Audio-Tokenizer \
  --device auto \
  --n-vq 16 \
  --input-jsonl train_raw.jsonl \
  --output-jsonl train_with_codes.jsonl
```

### Local Transformer legacy

```bash
python <local-family-preprocess-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-Local-Transformer \
  --codec-path OpenMOSS-Team/MOSS-Audio-Tokenizer \
  --device auto \
  --input-jsonl train_raw.jsonl \
  --output-jsonl train_with_codes.jsonl
```

### Local Transformer v1.5

```bash
python <local-v15-preprocess-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5 \
  --codec-path OpenMOSS-Team/MOSS-Audio-Tokenizer-v2 \
  --codec-weight-dtype fp32 \
  --codec-compute-dtype bf16 \
  --device auto \
  --input-jsonl train_raw.jsonl \
  --output-jsonl train_with_codes.jsonl
```

The public v1.5 path allows only `--codec-weight-dtype fp32`. `--codec-compute-dtype` affects codec inference only; it does not alter saved integer codes.

### Realtime

```bash
python <realtime-preprocess-entrypoint> \
  --codec-path OpenMOSS-Team/MOSS-Audio-Tokenizer \
  --device auto \
  --input-jsonl train_raw.jsonl \
  --output-jsonl train_with_codes.jsonl
```

Realtime preprocessing does not need a text-model `--model-path`; it loads only the audio tokenizer codec and writes `audio_codes` inside conversation turns.

## Reference audio encoding

For Delay, Local, Local v1.5, and Realtime preprocessing, reference audio is encoded by default when present.

Non-Realtime reference fields:

- `ref_audio`: single reference path; prepared field is `ref_audio_codes`.
- `reference_audio`: string or list alias; prepared field is `reference_audio_codes`.
- `reference`: string or list; for TTSD, list elements may be `null`, and prepared `reference_audio_codes` preserves `null` placeholders.

Skip reference-code preprocessing only when the training runtime will keep the codec available or when reference code fields are already present:

```bash
python <preprocess-entrypoint> \
  --input-jsonl train_raw.jsonl \
  --output-jsonl train_with_codes.jsonl \
  --skip-reference-audio-codes
```

If `ref_audio` or `reference` paths remain in the prepared JSONL without corresponding code fields, the dataset packer may try to encode them during training. That requires a loaded audio tokenizer and can be slower or fail in a training-only environment.

## Pre-encoded `audio_codes` versus raw `audio`

- SFT expects prepared code fields. Direct training from raw audio paths is not the normal path.
- Delay and Local legacy preprocessing normally re-encodes top-level `audio`; do not run it on a prepared manifest if the goal is to preserve existing `audio_codes`.
- Local v1.5 preprocessing can skip target encoding for rows that already contain `audio_codes`, but it can still encode missing reference codes unless `--skip-reference-audio-codes` is set.
- If every row already has valid `audio_codes` and needed reference code fields, skip preprocessing and launch SFT with the equivalent of `SKIP_PREPARE=1`.

Validate prepared manifests with `--mode prepared` before skipping preprocessing.

## Distributed preprocessing and sharded outputs

Preprocessing can be launched under Accelerate. The helpers infer `world_size` and `rank` from Accelerate unless the user overrides `--num-shards` and `--shard-rank`.

```bash
accelerate launch --num_processes 16 <preprocess-entrypoint> \
  --model-path OpenMOSS-Team/MOSS-TTS-v1.5 \
  --codec-path OpenMOSS-Team/MOSS-Audio-Tokenizer \
  --device auto \
  --input-jsonl train_raw.jsonl \
  --output-jsonl prepared/train_with_codes.jsonl
```

With `world_size > 1`, output names are rewritten per rank:

- `prepared/train_with_codes.rank00000-of-00016.jsonl`
- `prepared/train_with_codes.rank00001-of-00016.jsonl`
- ...
- `prepared/train_with_codes.rank00015-of-00016.jsonl`

The sharding rule is record index modulo world size. Every rank writes only its local records. Use the glob form when training:

```bash
--train-jsonl 'prepared/train_with_codes.rank*.jsonl'
```

Manual sharding without Accelerate is possible with `--num-shards`, `--shard-rank`, and `--save-shard-suffix`, but prefer Accelerate for multi-GPU codec encoding because device placement follows rank-local devices.

## Path handling and base directories

- Local v1.5 preprocessing resolves non-URI audio paths relative to the input JSONL file's parent directory.
- Delay, Local legacy, and Realtime helpers read paths as written. Use a consistent launch directory or paths that are unambiguous from the training host.
- The bundled validator defaults `--base-dir` to the JSONL parent. If the helper you plan to run interprets paths differently, pass the actual base directory explicitly.
- URI-like paths may be syntactically valid but should be validated against the runtime loader separately; use `--no-exists-check` for the local-file validator in that case.

## Preprocessing checklist

Before launching a long training run:

1. Validate raw JSONL with the correct task id.
2. Confirm target audio paths and reference paths resolve from the intended base directory.
3. For TTSD, decide and record `n_vq=16` when using the TTSD v1.0 base.
4. Run preprocessing single-process on a tiny subset or one shard before scaling out.
5. Validate prepared JSONL or one representative shard with `--mode prepared`.
6. Use `--train-jsonl` as a single file, directory, glob, or comma-separated list; quote globs so the training script can resolve the intended files consistently.
