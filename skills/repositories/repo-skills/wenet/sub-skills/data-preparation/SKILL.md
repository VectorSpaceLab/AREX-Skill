---
name: data-preparation
description: "Prepare and validate WeNet data manifests, dictionaries,
  tokenizers, CMVN inputs, and raw-versus-shard dataset layouts before training
  or decoding."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WeNet Data Preparation

Use this sub-skill when the task is to convert speech data into WeNet training
or evaluation inputs, validate `wav.scp`/`text`, create `data.list`, build a
character dictionary, choose raw versus shard data, or debug tokenizer/CMVN
setup.

## Start here

1. Read [references/data-formats.md](references/data-formats.md) to confirm the
   expected `wav.scp`, `text`, `data.list`, dictionary, and tokenizer shapes.
2. Use the bundled raw-manifest helper for small or medium custom datasets:

   ```bash
   python sub-skills/data-preparation/scripts/make_wenet_raw_manifest.py \
     --wav-scp wav.scp --text text --output data.list
   ```

3. Use the bundled dictionary helper for character-token recipes:

   ```bash
   python sub-skills/data-preparation/scripts/make_wenet_dict.py \
     --text text --output units.txt
   ```

4. Read [references/workflows.md](references/workflows.md) before planning
   CMVN, shard data, tokenizer selection, or recipe-stage conversion.
5. Read [references/troubleshooting.md](references/troubleshooting.md) when
   dataset loading filters everything, keys mismatch, audio cannot be decoded,
   dictionaries have wrong reserved IDs, or tokenizer files cannot be found.

## Route by task

- Single-audio package transcription belongs in
  [../package-transcription/SKILL.md](../package-transcription/SKILL.md).
- Training, checkpoint averaging, recognition, and WER/CER scoring belong in
  [../training-and-decoding/SKILL.md](../training-and-decoding/SKILL.md).
- Exporting a trained checkpoint belongs in
  [../model-export/SKILL.md](../model-export/SKILL.md).

## Key decisions

- Choose `raw` data for ordinary small/medium datasets and custom debugging.
  Choose `shard` only when the dataset is large enough that tar shards improve
  throughput and the user can tolerate extra packaging steps.
- Use absolute or stable audio paths in `wav.scp` and `data.list`. Relative
  paths often fail when training is launched from a different directory.
- For Mandarin character recipes, dictionary files reserve `<blank> 0`,
  `<unk> 1`, and `<sos/eos>` as the final or recipe-defined special token.
  Keep the active training config and tokenizer initialization consistent.
- Treat CMVN computation and feature extraction as data-prep stages, but do not
  run large audio scans unless the user has approved the data path, runtime,
  and storage cost.
