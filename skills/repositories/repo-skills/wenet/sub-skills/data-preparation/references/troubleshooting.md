# Data Preparation Troubleshooting

## `wav.scp` and `text` keys mismatch

Symptoms:

- manifest generation fails;
- training silently skips expected utterances;
- dataset length is smaller than expected.

Recovery:

```bash
python sub-skills/data-preparation/scripts/make_wenet_raw_manifest.py \
  --wav-scp wav.scp --text text --output data.list
```

The helper reports keys missing from either side. Fix keys before continuing;
do not let the pipeline guess a transcript for an audio path.

## Invalid raw `data.list`

Symptoms:

- JSON parse errors;
- missing `key`, `wav`, or `txt` fields;
- training loader errors before model construction.

Recovery:

- Validate that every line is one JSON object.
- Check field spelling exactly: `key`, `wav`, `txt`.
- Keep paths readable from the process launching training.
- Recreate the manifest from `wav.scp` and `text` instead of hand-editing many
  JSON lines.

## Audio files cannot be decoded

Symptoms:

- torchaudio/librosa decode errors;
- missing sox extension or unsupported audio format;
- CMVN/feature scripts fail on some utterances.

Recovery:

1. Confirm each `wav` path exists and is readable.
2. Convert unusual formats to WAV/PCM with a trusted audio tool.
3. Install sox/libsox when the audio backend requires it.
4. Start with a tiny subset before scanning the whole corpus.

## Dictionary reserved IDs are wrong

Symptoms:

- model output dimension mismatch;
- CTC blank id errors;
- `<unk>` or `<sos/eos>` behaves incorrectly;
- tokenizer initialization fails.

Recovery:

- Keep `<blank> 0` and `<unk> 1` unless a known config explicitly differs.
- Ensure `<sos/eos>` is present and matches the model/tokenizer config.
- Rebuild simple character dictionaries with:

  ```bash
  python sub-skills/data-preparation/scripts/make_wenet_dict.py \
    --text text --output units.txt
  ```

## Tokenizer files are missing

Symptoms:

- `load_tokenizer` or training initialization cannot open a BPE/model/vocab
  path;
- package loading works in the training directory but fails after moving model
  artifacts.

Recovery:

- Copy tokenizer resources next to exported model artifacts when the config
  references basenames.
- Use absolute paths only for local experiments; use portable relative
  basenames inside model directories.
- Verify tokenizer family matches the model family: character/BPE/Paraformer/
  Whisper/SenseVoice/HuggingFace.

## Dataset filters remove everything

Symptoms:

- training starts with zero batches;
- many warnings about length or output-input ratio;
- custom data works in raw inspection but not in training.

Recovery:

- Inspect filter settings in the training config: min/max input length,
  token length, and output-input ratio.
- Temporarily relax filters on a tiny trusted subset to confirm schema and
  audio decode.
- Check transcript normalization; empty transcripts or unsupported symbols can
  be filtered out.

## Shard packaging is slow or huge

Shard mode writes tar archives and may require substantial disk space. Use raw
mode until schema, tokenization, and data size are confirmed. Convert to shards
only after a small raw training/loader check succeeds.
