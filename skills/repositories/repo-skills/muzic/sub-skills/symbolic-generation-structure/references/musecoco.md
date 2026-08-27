# MuseCoco

MuseCoco is a two-stage symbolic music-from-text pipeline:

1. text-to-attribute understanding
2. attribute-to-music generation

The first stage predicts musical attributes from text. The second stage converts the attribute bundle into symbolic music.

## Attribute map

The public attribute set used by the repo centers on these top-level groups:

| Group | Meaning |
|---|---|
| `I1s2` | instrument |
| `R1` / `R3` | rhythm attributes |
| `S2s1` | artist |
| `S4` | genre |
| `B1s1` | bar |
| `TS1s1` | time signature |
| `K1` | key |
| `T1s1` | tempo |
| `P4` | pitch range |
| `EM1` | emotion |
| `TM1` | time |

The stage-1 attribute list in the code uses the same family names and the shipped `att_key.json` expands them into concrete labels.

## Stage 1: text-to-attribute understanding

### Data preparation

The repo provides a small text-formation workflow under `1-text2attribute_dataprepare`.

Typical steps:

```bash
cd 1-text2attribute_dataprepare
bash run.sh
```

This creates the paired attribute-text files used by the classifier stage, including:

- `att_key.json`
- `test.json`

The code also provides the public `predict.json` shape for inference: a list of objects with at least a `text` field.

### Training

```bash
cd 1-text2attribute_model
bash train.sh
```

The stage-1 trainer is Hugging Face Transformers based and expects a BERT-style encoder.

### Prediction

```bash
cd 1-text2attribute_model
bash predict.sh
```

Outputs from prediction:

- `tmp/predict_attributes.json`
- `tmp/softmax_probs.json`

### Stage-1 postprocessing

`stage2_pre.py` merges the attribute predictions into the inference bundle expected by stage 2.
It also regroups the `I1s2` and `S4` label families back into grouped vectors.

```bash
python stage2_pre.py
```

Output:

- `infer_test.bin`

## Stage 2: attribute-to-music generation

### Data extraction

The second stage starts from MIDI data and extracts symbolic token/attribute pairs.

```bash
python extract_data.py /path/to/midi_folder /path/to/save_dataset
```

Outputs:

- `TOKEN.bin`
- `TOKEN_index.json`
- `RID.bin`
- `RID_index.json`
- `file_list.txt`

Notes:

- the tool automatically extracts objective attributes from MIDI
- subjective fields such as artist, genre, and emotion may need manual fill-in in the source script

### Split and binarize

After extraction, move the packed files into the stage-2 model data folder and run:

```bash
cd 2-attribute2music_model/data_process
python split_data.py
python util.py
```

This creates Fairseq-ready text and binary data. The split script writes `train`, `valid`, and `test` text files plus command arrays.

### Training

The published large model recipe uses the stage-2 training shell:

```bash
cd 2-attribute2music_model
bash train-xl.sh
```

The repo also contains the `linear_mask` implementation directory used by the interactive generator.

## Stage 2 inference

The shipped inference path expects:

- a prepared `infer_test.bin` from stage 1
- the `linear_mask-1billion` checkpoint
- the binary input copied to `data/infer_input/infer_test.bin`

Run generation with:

```bash
bash interactive_1billion.sh 0 200
```

The start/end arguments choose the slice of the inference bundle.

Typical outputs:

- generated symbolic results under `generation/`
- per-run logs under `log/`

## Evaluation

The evaluation script compares generated music against extracted objective attributes.

```bash
python evaluation/eval_acc_v3.py --root PATH_OF_GENERATED_MUSIC
```

Reported outputs include:

- average sample-wise accuracy (ASA)
- per-attribute accuracy data
- per-file inspection data

The code writes `acc_result.json` and `midiinfo.json`; the README text also mentions `acc_results.json`, so treat the script output name as the authoritative one.

## Safe stage planning

The stage-1 and stage-2 boundary matters more than the exact command order:

1. predict attributes from text
2. run `stage2_pre.py`
3. copy `infer_test.bin` into the stage-2 input folder
4. run the interactive stage-2 generator
5. evaluate the generated music if objective-attribute coverage matters

## Common artifact table

| Stage | Artifact | Purpose |
|---|---|---|
| 1 | `predict_attributes.json` | predicted discrete labels |
| 1 | `softmax_probs.json` | stage-1 confidence values |
| 1 | `infer_test.bin` | stage-2 inference bundle |
| 2 | `TOKEN.bin` / `RID.bin` | packed symbolic music and metadata |
| 2 | `train.txt` / `valid.txt` / `test.txt` | Fairseq text data |
| 2 | `data-bin/` | binary training data |
| 2 | `generation/` | generated MIDI / token outputs |

## Safe validation helper

Use [scripts/plan_musecoco_pipeline.py](../scripts/plan_musecoco_pipeline.py) to check a MuseCoco file set and print the stage-by-stage artifact plan before running the heavyweight commands.
