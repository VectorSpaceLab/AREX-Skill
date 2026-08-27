# Training data formats

FunASR training commonly consumes newline-delimited JSON. The public conversion entry points are `scp2jsonl`, `jsonl2scp`, and `sensevoice2jsonl`. This sub-skill bundles stricter helpers so a future agent can test tiny fixtures without relying on long training scripts.

## Standard audio JSONL schema

One utterance per line:

```json
{"key":"utt001","source":"audio/utt001.wav","source_len":320,"target":"hello world","target_len":2,"prompt":"<ASR>"}
```

Field assumptions:

| Field | Required for robust training? | Meaning |
|---|---:|---|
| `key` | Yes | Unique utterance id. It should match the ids in `wav.scp` and text files. |
| `source` | Yes | Audio path or URI that FunASR can load at training time. Local paths should exist before training starts. |
| `source_len` | Strongly recommended | Audio length used for filtering/sorting, in roughly 10 ms frames. For a 16 kHz WAV this is `num_samples / 160`, rounded down. |
| `target` | Yes | Transcript or task target text. |
| `target_len` | Strongly recommended | `len(target.split())` when spaces are present, otherwise character length. |
| `prompt` | Optional | Defaults to `<ASR>` in the standard audio index dataset when absent. |
| `text_language`, `emo_target`, `event_target`, `with_or_wo_itn` | Optional | SenseVoice-style training metadata. Keep these fields only when the selected dataset/model config expects them. |

The standard audio index dataset filters by `min_source_length`, `max_source_length`, `min_target_length`, `max_target_length`, and `max_token_length`. Bad length values can silently drop useful samples or keep pathological ones, so validate lengths before training.

## `wav.scp` plus text input

The public converters expect two aligned text files:

```text
# train_wav.scp
utt001 audio/utt001.wav
utt002 audio/utt002.wav

# train_text.txt
utt001 hello world
utt002 你好世界
```

Rules:

- The id is the first whitespace-separated token.
- The value is everything after the first whitespace.
- Ids should be unique within each file.
- The key sets should match unless the user deliberately asks to use only the intersection.
- Local source paths should exist. URIs can be kept, but duration cannot be verified by the bundled pure-Python helper.

Recommended conversion from this sub-skill directory:

```shell
python scripts/make_jsonl_from_scp.py \
  --wav-scp train_wav.scp \
  --text train_text.txt \
  --output train.jsonl

python scripts/validate_manifest.py train.jsonl --check-sources --check-source-len
```

For URI-heavy manifests, use `--no-check-sources` while converting, then validate with a loader-specific smoke before training. Do not treat a placeholder `source_len=1` as suitable for final large-scale training.

## Reverse conversion

`jsonl2scp` writes `wav.scp` and text files from `source` and `target`. The bundled validator can do the same after validation:

```shell
python scripts/validate_manifest.py train.jsonl \
  --write-wav-scp train_wav.scp \
  --write-text train_text.txt
```

If an older AISHELL-style recipe expects spaces stripped from Chinese targets when the audio path contains `aishell`, pass `--aishell-strip-spaces` explicitly. The default preserves the manifest target text exactly.

## SenseVoice-style manifests

`sensevoice2jsonl` extends the standard audio schema with language/emotion/event/ITN tags. If these fields are missing, the public converter can infer tags by running a SenseVoice model; that may download/load a model and is not a safe default preflight step.

Useful optional fields:

```json
{
  "key":"utt003",
  "source":"audio/utt003.wav",
  "source_len":410,
  "target":"早上好。",
  "target_len":4,
  "text_language":"<|zh|>",
  "emo_target":"<|NEUTRAL|>",
  "event_target":"<|Speech|>",
  "with_or_wo_itn":"<|withitn|>"
}
```

When a user only needs ordinary ASR fine-tuning, keep the standard `source`/`target` schema. Add SenseVoice metadata only when the selected config or model family requires it.

## Conversational audio manifests

Some LLM-ASR training data uses a `messages` schema instead of `source`/`target`:

```json
{
  "messages": [
    {"role":"system","content":"You are a helpful assistant."},
    {"role":"user","content":"Speech transcription:<|startofspeech|>!audio/utt.wav<|endofspeech|>"},
    {"role":"assistant","content":"hello world"}
  ],
  "speech_length": 320,
  "text_length": 2
}
```

This sub-skill can validate the basic JSON shape with `validate_manifest.py --schema messages`, but model-family routing, vLLM acceleration, and Nano-specific freezing/adapter decisions belong to `../llm-asr-and-vllm/`.

## Large-data list files

If `train_data_set_list` or `valid_data_set_list` points to a file whose name does not end in `.jsonl` or `.json`, the audio index loader treats it as a list of JSONL files, one path per line:

```text
shards/train.000.jsonl
shards/train.001.jsonl
shards/train.002.jsonl
```

With `++dataset_conf.data_split_num=256`, the list is divided sequentially into 256 groups. For heterogeneous data, balance shards before writing the list so each group has similar language, duration, and model-family distribution.

## Tiny difficult fixture pattern

To test validation without training:

1. Create a one-second WAV and a two-line text file.
2. Convert with `make_jsonl_from_scp.py`.
3. Deliberately corrupt one JSONL line by removing `source` or changing `target_len`.
4. Confirm `validate_manifest.py` exits non-zero and reports line numbers.

This catches the most common silent data issues before a long training run starts.
