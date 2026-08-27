# Structure and emotion generation

This reference covers the remaining symbolic generation families in the scope:
Museformer, MeloForm, and EmoGen.

## At a glance

| System | Main idea | Main inputs | Main outputs |
|---|---|---|---|
| Museformer | long-sequence music LM with fine/coarse attention | MIDI corpus tokenized with REMIGEN2 / MidiProcessor | Fairseq checkpoint, generated token logs, decoded MIDI |
| MeloForm | melody generation with musical form and phrase refinement | monophonic LMD-style melody data or expert-system phrases | paired template/melody data, Fairseq checkpoints, refined phrase MIDI |
| EmoGen | emotion control through emotion-to-attribute mapping and attribute-to-music generation | jSymbolic features, REMIGEN2 MIDI tokens, emotion quadrants | Linear Transformer checkpoints and emotion-conditioned MIDI |

## Museformer

Museformer uses a long-context symbolic representation and Fairseq-style training.
The public workflow assumes a 4/4, six-track normalization for the standard recipe.

### Data and tokenization

The repo expects a MIDI file list under `data/meta` and a tokenized corpus under `data/token`.

Key steps:

```bash
mp-batch-encoding data/midi data/token --encoding-method REMIGEN2 --normalize-pitch-value --remove-empty-bars --ignore-ts --sort-insts 6tracks_cst1
python tools/generate_token_data_by_file_list.py data/meta/train.txt data/token data/split
python tools/generate_token_data_by_file_list.py data/meta/valid.txt data/token data/split
python tools/generate_token_data_by_file_list.py data/meta/test.txt data/token data/split
fairseq-preprocess --only-source --trainpref data/split/train.data --validpref data/split/valid.data --testpref data/split/test.data --destdir data-bin/lmd6remi --srcdict data/meta/dict.txt
```

For a more general dataset, use `REMIGEN`, do not ignore time signatures, and switch to `data/meta/general_use_dict.txt`.

### Training

```bash
bash ttrain/mf-lmd6remi-1.sh
```

Important constraints:

- the published recipe uses batch size 1 per GPU
- Triton is required by the code path
- `--beat-mask-ts True` is needed for the general-use variant
- the `con2con` and `con2sum` settings control fine-grained and coarse-grained attention ranges

### Validation and generation

Validation:

```bash
bash tval/val__mf-lmd6remi-x.sh 1 checkpoint_best.pt 10240
```

Generation:

```bash
printf '\n\n\n\n\n' | bash tgen/generation__mf-lmd6remi-x.sh 1 checkpoint_best.pt 1
```

Then decode the generated text log back into MIDI:

```bash
python tools/batch_extract_log.py output_log/generation.log output/generation --start_idx 1
python tools/batch_generate_midis.py --encoding-method REMIGEN2 --input-dir output/generation --output-dir output/generation
```

### Museformer artifact flow

| Step | Artifact |
|---|---|
| tokenization | `data/token/*.txt` |
| split assembly | `data/split/*.data` |
| binary preprocessing | `data-bin/lmd6remi` |
| training | `checkpoints/mf-lmd6remi-1` |
| generation log | `output_log/generation.log` |
| decoded tokens and MIDI | `output/generation/` |

## MeloForm

MeloForm is a melody-form system that combines an expert-system stage with a neural phrase refinement stage.

### Data preparation

The public workflow starts from monophonic LMD-style data:

```bash
python preprocess_lmd.py ./data/train/raw ./data/train/processed/para
bash binarize.sh ./data/train/processed/ meloform
```

The preprocessing path produces paired template/melody files and dictionary files for Fairseq binarization.

### Training

```bash
bash train.sh ./data/train/processed/processed_para/ meloform
```

The training shell launches a Fairseq transformer with MeloForm's custom criterion and user directory.

### Refinement workflow

The refinement path is phrase based.

1. Prepare expert-system output and a `template.json` file.
2. Convert the expert-system phrase into neural-network training material.
3. Refine phrase-by-phrase with the iterative shell.

Core commands:

```bash
python process_es.py ./data/refine/expert_system 0 ./data/refine/data_nn
bash meloform_refine_melody.sh ./data/refine/data_nn 0 checkpoints/ results/
```

The refinement shell first generates one phrase, replaces it into the template, then generates the next phrase with the updated context.

### MeloForm artifacts

| Step | Artifact |
|---|---|
| preprocessing | `para/`, paired template and melody files |
| binarization | `processed_para/` |
| training | `checkpoints/` |
| expert-system conversion | `data_nn/<song_id>/template/` |
| refinement output | `results/out_midi/<song_id>/b1/src_res.mid` |

## EmoGen

EmoGen uses emotion quadrants mapped to attribute vectors, then generates music from those attributes.
It needs Python plus Java + jSymbolic for feature extraction.

### Environment

Required external pieces:

- Python 3.8
- Java
- the `jSymbolic_2_2_user` package inside `jSymbolic_lib`

### Data flow

For a dataset such as `data/Piano`:

```bash
cd data_process
python midi_encoding.py
cd ../jSymbolic_lib
python jSymbolic_feature.py
cd ../data_process
python gen_data.py
```

This produces:

- REMIGEN2 token files in `data/<set>/remi`
- jSymbolic XML features in `data/<set>/feature`
- train / valid / test text files
- command arrays for control learning
- Fairseq data bins under `data/<set>/data-bin`

### Training

Piano recipe:

```bash
bash Piano_train.sh
```

TopMAGD recipe:

```bash
bash TopMAGD_train.sh
```

### Inference

Piano generation:

```bash
bash Piano_gen.sh 3
```

TopMAGD generation:

```bash
bash TopMAGD_gen.sh 1
```

The integer selects the target emotion quadrant:

| Value | Emotion |
|---|---|
| 1 | Q1 |
| 2 | Q2 |
| 3 | Q3 |
| 4 | Q4 |

### EmoGen artifacts

| Step | Artifact |
|---|---|
| MIDI encoding | `data/<set>/remi/` |
| jSymbolic extraction | `data/<set>/feature/` |
| split / commands | `train.txt`, `valid.txt`, `test.txt`, `*_command.npy` |
| Fairseq bins | `data/<set>/data-bin/` |
| inference commands | `data/infer_input/inference_command.npy` |
| generated music | `generation/` |

## Cross-system guidance

- Museformer is the long-structure route when the question is about tokenized symbolic modeling over long spans.
- MeloForm is the route when the task is about form-aware melody generation or phrase refinement from expert-system output.
- EmoGen is the route when the task is about emotion control via quadrant mappings and jSymbolic features.
