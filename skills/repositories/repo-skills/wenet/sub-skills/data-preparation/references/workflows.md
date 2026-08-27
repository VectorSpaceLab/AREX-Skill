# Data Preparation Workflows

## Custom raw dataset flow

1. Normalize transcripts into a `text` file with one key and transcript per
   line.
2. Create `wav.scp` with matching keys and readable audio paths.
3. Generate a raw manifest:

   ```bash
   python sub-skills/data-preparation/scripts/make_wenet_raw_manifest.py \
     --wav-scp wav.scp --text text --output data.list
   ```

4. Create a dictionary or tokenizer resources. For a simple character dict:

   ```bash
   python sub-skills/data-preparation/scripts/make_wenet_dict.py \
     --text text --output units.txt
   ```

5. Choose a training config whose tokenizer and feature settings match the
   prepared resources.
6. Only after raw data loads, decide whether to compute CMVN and whether to
   package large-scale shard data.

## Recipe-stage pattern

WeNet recipes follow a staged pattern:

| Stage family | Purpose | Typical outputs |
|---|---|---|
| download/acquire | fetch or locate corpus | external data directory |
| data preparation | create `wav.scp` and `text` | `data/<split>/wav.scp`, `data/<split>/text` |
| CMVN/features | compute global normalization or feature metadata | `global_cmvn` |
| dictionary/tokenizer | build units or BPE resources | `units.txt` or tokenizer model/vocab |
| manifest | create raw or shard `data.list` | `data/<split>/data.list` |
| training | train a model from config and manifests | checkpoints, `train.yaml` |
| decoding/scoring | recognize eval manifests and compute WER/CER | result text and score files |
| export | create deployment artifacts | JIT/ONNX/runtime model files |

For a new dataset, run stages one at a time and validate each output before
starting training.

## Raw versus shard

Use raw mode when:

- the dataset is small or medium;
- you are debugging a new corpus;
- paths are simple and local;
- you want easy inspection of individual JSON Lines.

Use shard mode when:

- the dataset is very large;
- training input throughput matters;
- you can budget time and disk for tar packaging;
- the team already has a stable raw manifest and wants faster streaming reads.

Do not convert directly to shards before verifying `wav.scp`, `text`, raw
`data.list`, dictionary, and tokenizer assumptions.

## CMVN and feature notes

Some recipes compute global CMVN using audio lists and the selected training
config. CMVN is useful for reproducible acoustic normalization, but it scans
many audio files. Validate the manifest and estimate data size before running
CMVN on a large corpus.

Feature type and dimensions come from the config's dataset section. The package
feature loader supports configured `fbank`, `mfcc`, or `log_mel_spectrogram`
paths. Keep feature settings consistent between training, package loading, and
export.

## Reference-only source utilities

The original repository contains many shell and Python utilities for shard
packaging, CMVN, Kaldi-style data directory cleanup, speed perturbation,
filtering, and validation. They are not bundled wholesale because they assume a
recipe checkout layout, may mutate data directories, can scan large audio
collections, or require extra binaries. The generated skill instead provides
safe raw-manifest and dictionary helpers plus the schemas and checks needed to
recreate the workflows in a user environment.
