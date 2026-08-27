# MusicBERT Workflows

MusicBERT is the Muzic branch for symbolic music understanding. It uses OctupleMIDI tokenization, Fairseq preprocessing/training, and task-specific Fairseq heads for pretraining, melody/accompaniment ranking, and genre/style classification.

## Environment and execution posture

| Step | Typical backend | Runtime risk | Notes |
|---|---|---|---|
| OctupleMIDI conversion from MIDI zip | CPU | dataset-scale | Interactive prompts, multiprocessing, writes raw text and dictionaries. |
| Fairseq binarization | CPU | version-sensitive | Requires `fairseq-preprocess` and matching dictionary/input files. |
| Masked-LM pretraining | CUDA | expensive | Shell launcher computes update frequency from `nvidia-smi`; zero GPUs will fail. |
| NSP fine-tuning for melody/accompaniment | CUDA | expensive | Requires a MusicBERT checkpoint and `{next,acc}_data_bin`. |
| Genre/style fine-tuning | CUDA | expensive | Requires TOPMAGD/MASD raw labels, fold-specific binarized data, and a checkpoint. |
| Evaluation | CUDA in source scripts | data/checkpoint-dependent | Evaluation scripts call `.cuda()` and load Fairseq Roberta models. |

Use this reference for command planning and data-shape checks. Do not promise that training or evaluation will run unless the user has provided a compatible old Fairseq/Torch stack, datasets, and checkpoints.

## OctupleMIDI representation facts

The inspected preprocessing code encodes each note as eight token fields:

1. Measure/bar index
2. Position inside the bar
3. Program, with percussion represented separately
4. Pitch, with percussion offset separately
5. Duration
6. Velocity
7. Time signature
8. Tempo

Important conversion constants from the source implementation:

| Constant | Value | Meaning |
|---|---:|---|
| `pos_resolution` | 16 | Positions per beat. |
| `bar_max` | 256 | Maximum encoded bar index. |
| `sample_len_max` | 1000 | Maximum window length in notes for raw text samples. |
| `sample_overlap_rate` | 4 | Window overlap divisor for pretraining segments. |
| `pool_num` | 24 | Multiprocessing workers used by default. |
| Train/valid/test split | 98% / 1% / 1% | Pretraining split inside `preprocess.py`. |

The raw text format starts with eight `<s>` tokens, emits eight field tokens per note, and appends seven `</s>` tokens for Fairseq EOS handling.

## Pretraining data workflow

### Inputs

- Lakh MIDI Dataset full archive converted to one MIDI zip, for example `lmd_full.zip`.
- MIDI files inside the zip can be `.mid` or `.midi`.
- Enough local storage for raw OctupleMIDI text and Fairseq binarized data.

### Convert MIDI zip to raw OctupleMIDI

Run the preprocessing script from the MusicBERT source working directory:

```bash
python -u preprocess.py
```

The script prompts interactively:

```text
Dataset zip path: lmd_full.zip
OctupleMIDI output path: lmd_full_data_raw
```

Expected raw outputs:

```text
lmd_full_data_raw/
  dict.txt
  midi_train.txt
  midi_valid.txt
  midi_test.txt
```

Expected terminal signal is a stream of `SUCCESS: ...` lines plus a final success ratio. Errors such as `ERROR(PARSE)`, `ERROR(BLANK)`, `ERROR(DUPLICATED)`, and `ERROR(TSFILT)` are per-MIDI filtering or parsing signals, not always fatal for the whole corpus.

### Binarize pretraining data

```bash
bash binarize_pretrain.sh lmd_full
```

This expects `lmd_full_data_raw/` and creates `lmd_full_data_bin/` using:

```text
--only-source
--srcdict lmd_full_data_raw/dict.txt
--trainpref lmd_full_data_raw/midi_train.txt
--validpref lmd_full_data_raw/midi_valid.txt
--testpref  lmd_full_data_raw/midi_test.txt
--workers 24
```

If the destination directory already exists, the shell script exits rather than overwriting.

### Pretrain MusicBERT masked LM

```bash
bash train_mask.sh lmd_full small
bash train_mask.sh lmd_full base
```

Argument contract:

| Position | Meaning | Example |
|---:|---|---|
| `$1` | Dataset prefix; launcher reads `${prefix}_data_bin` | `lmd_full` |
| `$2` | Architecture suffix after `musicbert_`; default is `small` | `small`, `base` |

Source launcher settings:

| Setting | Value |
|---|---:|
| Total updates | 125000 |
| Warmup updates | 25000 |
| Peak LR | 0.0005 |
| Tokens per sample | 8192 |
| Global batch size target | 256 |
| Max sentences per GPU step | 4 |

The launcher restores from `checkpoints/checkpoint_last_${arch}.pt` and writes a checkpoint suffix for the selected architecture. If no local GPU is visible, `nvidia-smi`-based update-frequency calculation can divide by zero.

## Melody completion and accompaniment suggestion workflow

These tasks use PiRhDy-style paired contexts and binary labels.

### Expected input layout

```text
PiRhDy/
  dataset/
    context_next/
      train
      test
    context_acc/
      train
      test
```

Task names:

| Task | Meaning | Raw output prefix |
|---|---|---|
| `next` | Melody completion / next-context ranking | `next_data_raw` |
| `acc` | Accompaniment suggestion | `acc_data_raw` |

### Generate raw OctupleMIDI-like task files

```bash
python -u gen_nsp.py
```

Prompt:

```text
task = next
```

or:

```text
task = acc
```

Expected raw outputs:

```text
next_data_raw/
  dict.txt
  train.txt
  train.label
  test.txt
  test.label
```

The generator maps source sequence features into the eight MusicBERT token fields with fixed 4/4 time signature and 120 BPM tempo.

### Binarize NSP data

```bash
bash binarize_nsp.sh next
bash binarize_nsp.sh acc
```

Expected binarized layout:

```text
next_data_bin/
  input0/
  label/
```

The launcher separately binarizes source text and label files.

### Fine-tune NSP head

```bash
bash train_nsp.sh next checkpoints/checkpoint_last_musicbert_base.pt
bash train_nsp.sh acc  checkpoints/checkpoint_last_musicbert_small.pt
```

Argument contract:

| Position | Meaning |
|---:|---|
| `$1` | Task, `next` or `acc`; creates `${task}_head`. |
| `$2` | MusicBERT checkpoint path. |

Source launcher settings:

| Setting | Value |
|---|---:|
| Total updates | 250000 |
| Warmup updates | 50000 |
| Peak LR | 0.00005 |
| Tokens per sample | 8192 |
| Max positions | 8192 |
| Global batch size target | 64 |
| Classes | 2 |
| Best metric | accuracy |

### Evaluate NSP ranking

```bash
python -u eval_nsp.py checkpoints/checkpoint_last_nsp_next_checkpoint_last_musicbert_base.pt next_data_bin
python -u eval_nsp.py checkpoints/checkpoint_last_nsp_acc_checkpoint_last_musicbert_small.pt acc_data_bin
```

The evaluator loads the validation split, uses `next_head` or `acc_head` based on the checkpoint filename, groups candidates in groups of 50, and reports:

- `MAP`
- `HITS@1`, `HITS@5`, `HITS@10`, `HITS@15`, `HITS@20`, `HITS@25`
- a `.npy` file containing `y_true` and `y_pred`

## Genre and style classification workflow

### Inputs

- `lmd_full.zip`
- `midi_genre_map.json` with `topmagd` and/or `masd` entries.
- Desired sequence length, commonly `1000` for raw generation or `8192` maximum positions for model use.

### Generate raw genre/style folds

```bash
python -u gen_genre.py
```

Prompts:

```text
subset: topmagd
LMD dataset zip path: lmd_full.zip
sequence length: 1000
```

or:

```text
subset: masd
LMD dataset zip path: lmd_full.zip
sequence length: 1000
```

The generator:

- filters MIDI zip entries by IDs present in the label map;
- uses five stratified folds;
- samples the longest produced segment per MIDI;
- emits four training samples per input item for train folds;
- writes fold-local dictionaries, text files, labels, and IDs.

Expected raw layout:

```text
topmagd_data_raw/
  0/
    dict.txt
    train.txt
    train.label
    train.id
    test.txt
    test.label
    test.id
  ...
  4/
```

### Binarize genre/style folds

```bash
bash binarize_genre.sh topmagd
bash binarize_genre.sh masd
```

Expected binarized layout:

```text
topmagd_data_bin/
  0/
    input0/
    label/
  ...
  4/
```

The launcher also copies `train.label` and `test.label` into the binarized label folder as `train.label` and `valid.label`.

### Fine-tune genre/style heads

```bash
bash train_genre.sh topmagd 13 0 checkpoints/checkpoint_last_musicbert_base.pt
bash train_genre.sh masd    25 4 checkpoints/checkpoint_last_musicbert_small.pt
```

Argument contract:

| Position | Meaning | Examples |
|---:|---|---|
| `$1` | Subset name | `topmagd`, `masd` |
| `$2` | Number of classes | `13`, `25` |
| `$3` | Fold index | `0` through `4` |
| `$4` | MusicBERT checkpoint path | `checkpoints/checkpoint_last_musicbert_base.pt` |

Source launcher settings:

| Setting | Value |
|---|---:|
| Total updates | 20000 |
| Warmup updates | 4000 |
| Peak LR | 0.00005 |
| Tokens per sample | 8192 |
| Max positions | 8192 |
| Global batch size target | 64 |
| Criterion | `sentence_prediction_multilabel` |
| Best metric | `f1_score_micro` |

### Evaluate genre/style classifiers

The evaluator accepts an `x` placeholder in the checkpoint and data paths, replacing it with fold numbers. In the inspected script, `n_folds` is set to `1`, so only fold `0` is evaluated unless the script is adjusted.

```bash
python -u eval_genre.py checkpoints/checkpoint_last_genre_topmagd_x_checkpoint_last_musicbert_small.pt topmagd_data_bin/x
python -u eval_genre.py checkpoints/checkpoint_last_genre_masd_x_checkpoint_last_musicbert_small.pt masd_data_bin/x
```

Reported metrics:

- `f1_score_macro`, `f1_score_micro`, `f1_score_weighted`, `f1_score_samples`
- `roc_auc_score_macro`, `roc_auc_score_micro`, `roc_auc_score_weighted`, `roc_auc_score_samples`

## Minimum preflight checklist

Before any expensive MusicBERT run, verify:

- The raw output directory does not already exist unless the user intends to resume manually.
- `fairseq-preprocess` and `fairseq-train` resolve to the intended environment.
- The `musicbert` Fairseq user module is importable from the command working directory.
- Checkpoints are placed under the path used in the command.
- CUDA availability matches the selected step; train/eval scripts are not CPU-safe as written.
- Dataset prefixes match exactly: `lmd_full`, `next`, `acc`, `topmagd`, or `masd`.
