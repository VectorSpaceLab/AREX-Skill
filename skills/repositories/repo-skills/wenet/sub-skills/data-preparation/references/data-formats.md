# WeNet Data Formats

Read this before creating or validating training/evaluation data for WeNet.

## `wav.scp`

A Kaldi-style `wav.scp` maps utterance keys to audio paths or audio commands.
For portable WeNet recipes, prefer one whitespace-separated key and an absolute
or stable path per line:

```text
utt001 /data/audio/utt001.wav
utt002 /data/audio/utt002.wav
```

The key must match the key used in `text` and downstream manifests.

## `text`

A `text` file maps utterance keys to normalized transcripts:

```text
utt001 HELLO WORLD
utt002 WE SHARE NET TOGETHER
```

For Mandarin character recipes, recipe stages often remove spaces between
Chinese characters before token extraction. Preserve spaces only when the
chosen tokenizer/config expects word or BPE segmentation.

## Raw `data.list`

A raw WeNet `data.list` is JSON Lines. Each line contains at least:

```json
{"key": "utt001", "wav": "/data/audio/utt001.wav", "txt": "HELLO WORLD"}
```

Required fields:

| Field | Meaning |
|---|---|
| `key` | utterance id |
| `wav` | audio path or audio source understood by the dataset pipeline |
| `txt` | normalized transcript used for training/evaluation |

Use the bundled helper for the common `wav.scp` + `text` conversion:

```bash
python sub-skills/data-preparation/scripts/make_wenet_raw_manifest.py \
  --wav-scp wav.scp --text text --output data.list
```

## Shard `data.list`

Shard mode packages many utterances into tar shards and points the training
pipeline at shard entries. Use shard mode for large datasets where sequential
archive reads improve throughput. It is not the best default for first
custom-data debugging because it adds disk writes, tar packaging, and more
failure points.

When converting a raw custom dataset to shard mode, keep the same normalized
keys and transcripts, then validate a small raw `data.list` first. Only package
shards after the raw manifest is known to load.

## Dictionaries and reserved tokens

A typical character dictionary maps tokens to integer ids:

```text
<blank> 0
<unk> 1
你 2
好 3
<sos/eos> 4
```

Common rules:

- `<blank>` is the CTC blank and should be id `0`.
- `<unk>` should be id `1`.
- `<sos/eos>` marks start/end for attention-decoder workflows. Many recipes add
  it after corpus-derived symbols; some configs place it early. Keep the dict
  and `train.yaml` tokenizer/model assumptions consistent.
- Sort corpus-derived tokens deterministically so repeated preparation gives the
  same ids.

Use the bundled helper for simple character dictionaries:

```bash
python sub-skills/data-preparation/scripts/make_wenet_dict.py \
  --text text --output units.txt
```

## Tokenizer families

WeNet configs can initialize different tokenizer families. Common choices:

- character tokenizer for Mandarin and small character-level recipes;
- BPE/SentencePiece tokenizer for English and multilingual recipes;
- Paraformer, Whisper, SenseVoice, and HuggingFace tokenizers for corresponding
  model families.

Tokenizer config paths in `train.yaml` must point to files that exist in the
training/export/model directory, or to files copied next to the model artifacts
for package loading.

## CMVN and features

Recipes may compute global CMVN statistics before training. The package feature
loader supports configured feature types such as `fbank`, `mfcc`, and
`log_mel_spectrogram`. CMVN and feature extraction scan audio; run them only
after validating paths and estimating runtime.

## Validation checklist

- Every key in `wav.scp` appears exactly once in `text`.
- Every key in `text` appears exactly once in `wav.scp`.
- Audio paths are readable from the process that will train or decode.
- Raw `data.list` is valid JSON Lines and contains `key`, `wav`, and `txt`.
- Dictionary reserved tokens match the training config.
- Tokenizer model/vocab files exist before training/export begins.
- Large datasets are validated in raw mode before shard packaging.
