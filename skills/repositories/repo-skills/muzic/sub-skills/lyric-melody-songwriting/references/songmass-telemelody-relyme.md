# SongMASS, TeleMelody, and ReLyMe reference

This reference covers the three lyric-melody families that share fairseq-era expectations, external checkpoints, and strict file layouts.

## 1. Quick decision guide

| Need | Best fit | Why |
|---|---|---|
| Lyric-to-melody or melody-to-lyric translation with pretraining and alignment | SongMASS | It is the paired translation system in this subtree |
| Lyric-to-rhythm plus chord/template-controlled melody generation | TeleMelody | It splits lyric-to-template and template-to-melody stages |
| Constraint-based reranking or objective scoring | ReLyMe | It wraps TeleMelody/SongMASS with lyric-melody relationship rules |

## 2. SongMASS workflow

### Required assets

| Asset | Expected layout | Notes |
|---|---|---|
| Mono data | `data_org/mono/` | Contains lyric and melody monolingual files plus dictionaries |
| Parallel data | `data_org/para/` | Contains train/valid/test lyric-melody pairs and dictionaries |
| Processed data | `data_org/processed/` | Output of `preprocess.sh` for fairseq |
| User dir | `mass/` | Passed to fairseq as `--user-dir mass` |
| Checkpoint | `checkpoint_best.pt` or the model path you pass to inference | Inference path used by `fairseq-generate` |

### Data preparation

1. Parse LMD data into `mono/` and `para/` files.
2. Copy the dictionary files into both `mono/` and `para/`.
3. Mirror the mono files into `mono/train.*` and `mono/valid.*` as needed.
4. Run preprocessing to produce the binarized `processed/` directory.

### Command map

| Stage | Command family | Important arguments | Output |
|---|---|---|---|
| Parse LMD | dataset parser + generator script | LMD root and output directory | `mono/` and `para/` text corpora |
| Preprocess | `fairseq-preprocess` via `preprocess.sh` | `--srcdict`, `--tgtdict`, `--user-dir mass` | Binarized `processed/` data |
| Train | `fairseq-train` via `train.sh` | `--task xmasked_seq2seq`, `--mass_steps`, `--mt_steps`, `--criterion label_smoothed_cross_entropy_with_align` | `checkpoint_best.pt` |
| Infer lyric | `fairseq-generate` via `infer_lyric.sh` | melody->lyric language direction, `--path <model>` | Generated lyric output |
| Infer melody | `fairseq-generate` via `infer_melody.sh` | lyric->melody language direction, `--path <model>` | Generated melody output |
| Evaluate | `evaluate_histo.py`, `evaluate_timeseries.py` | lyric, melody, song-id, and generated hypothesis files | Pitch/duration similarity and melody distance |

### Evaluation inputs
- Pitch and duration similarity use lyric, melody, song-id, and generated melody files.
- Melody distance uses the same inputs as similarity evaluation.
- The evaluation scripts expect the lyric and melody files to remain aligned by song id.

## 3. TeleMelody workflow

### Required assets

| Asset | Expected layout | Notes |
|---|---|---|
| Lyric2Rhythm checkpoints | `checkpoints/<lyric2rhythm_prefix>/checkpoint_best.pt` | Used in the first stage of inference |
| Template2Melody checkpoints | `checkpoints/<template2melody_prefix>/checkpoint_best.pt` | Used in the second stage of inference |
| Dictionaries | `data-bin/<model_prefix>/` | Must match the checkpoint prefix |
| Input lyrics | `data/<lang>/<data_prefix>/lyric.txt` | English uses word-level text; Chinese uses character-level text |
| Input chords | `data/<lang>/<data_prefix>/chord.txt` | Required for both English and Chinese |
| English syllables | `data/en/<data_prefix>/syllable.txt` | Additional lyric-to-rhythm input for English |
| Output dir | `results/<save_prefix>/midi/` | Generated MIDI files are written here |

### Training stages

| Stage | Command family | Notes |
|---|---|---|
| Lyric-to-rhythm | `training/lyric2rhythm/train.sh` | Preprocesses lyric/beat pairs, trains a transformer, and stores checkpoints under `checkpoints/` |
| Template-to-melody | `training/template2melody/gen.py`, `gen_align.py`, `preprocess.sh`, `train.sh` | Builds data, alignment, and the melody model from `lmd_matched` |

### Inference layout

| Language | Required input files | Notes |
|---|---|---|
| English | `lyric.txt`, `chord.txt`, `syllable.txt` | `infer_en.py` consumes lyric, chord, and syllable text |
| Chinese | `lyric.txt`, `chord.txt` | `infer_zh.py` consumes lyric and chord text |

### miditoolkit caveat
- TeleMelody's README requires a patched `miditoolkit` parser for Chinese lyric dumping.
- The patch adds a `charset` argument to `midi/parser.py` and passes that argument into `mido.MidiFile`.
- The asset checker can confirm file layout, but it cannot verify that the installed `miditoolkit` package was patched.

### Evaluation metrics

| Script | Metric family | Required files |
|---|---|---|
| `cal_similarity.py` | Pitch and duration similarity | Generated MIDI and ground-truth MIDI |
| `cal_dtw.py` | Melody distance | Generated MIDI and ground-truth MIDI |
| `cal_acc.py` | TA, CA, RA, AA | `test.hyp.txt` and `test.src.txt` |

The `test/` fixtures show the expected score/input shape. The helper scripts and references should treat those files as format examples, not as mandatory runtime assets.

## 4. ReLyMe workflow

### TeleMelody integration path

| Step | What changes | Why |
|---|---|---|
| Copy patched TeleMelody files | Copy the `telemelody_en` or `telemelody_zh` helper tree into the TeleMelody inference area | Adds ReLyMe-specific constraint logic |
| Replace fairseq internals | Swap in the provided `sequence_generator.py` and `fairseq_task.py` | Enables the custom decoding path |
| Set generation mode | Toggle `GEN_MODE` in `config.py` between `BASE` and `ReLyMe` | Chooses baseline or constrained generation |
| Run the main pipeline | Execute the patched `main.py` | Produces baseline or ReLyMe-enhanced MIDI |

### SongMASS integration path

The SongMASS branch exists in the repository's ReLyMe code, but the top-level README marks this section as under-documented. Treat it as code evidence rather than a polished user guide.

| Component | Role |
|---|---|
| `songmass_en` / `songmass_zh` helper trees | Constraint-aware SongMASS reranking and generation helpers |
| `generate_melody_songmass.py` | Converts generated SongMASS pieces into MIDI |
| `ranking.py` | Selects the best candidate MIDI with the objective score module |
| `gen_at/` helpers | Build alignments and merge candidate pieces |
| `get_l2m_result_base.sh` / `get_l2m_result_relyme.sh` | Staged wrappers for baseline and ReLyMe-style SongMASS flows |

### Score module

| Item | Inputs | Output |
|---|---|---|
| `score_en.py` | `.mid`, `.strct`, and `.syl` files | English objective score |
| `score_zh.py` | `.mid` and `.strct` files | Chinese objective score |
| `score/` helpers | MIDI split, pitch/duration distance, contour, pause, and structure rules | Component scores and total score |

The score code uses temporary `strct_temp/a` and `strct_temp/b` subdirectories while computing structure metrics. Make sure the workspace is writable.

## 5. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `fairseq-preprocess` fails with a user-dir error | `mass/` is missing or the wrong path was passed | Point `--user-dir` at the SongMASS fairseq extension directory |
| `fairseq-generate` cannot find dictionaries | The checkpoint prefix and `data-bin` prefix do not match | Use the same model prefix for both the checkpoint and the binarized data |
| TeleMelody inference fails on Chinese MIDI output | The local `miditoolkit` package was not patched | Apply the parser patch before running the Chinese inference path |
| English TeleMelody inference complains about missing syllables | `syllable.txt` was not created | Add the syllable file under `data/en/<data_prefix>/` |
| ReLyMe TeleMelody results look unchanged | `GEN_MODE` is still set to `BASE` | Switch to `ReLyMe` in the copied config before running the patched main pipeline |
| ReLyMe score fails with missing temp directories | The workspace is read-only or path creation is blocked | Run in a writable workspace so `strct_temp/` can be created |
| SongMASS reranking fails to choose a result | The candidate folders are empty or ranking inputs were not generated | Confirm the generation stages produced candidate MIDI files before ranking |
| Evaluation numbers look suspiciously perfect or zero | Ground-truth and generated files were mixed up | Recheck the lyric/melody pairing and hypothesis file format |

## Notes for future agents
- SongMASS and TeleMelody are fairseq-era workflows; the exact dependency stack matters.
- ReLyMe's SongMASS branch is present but under-documented, so preserve the distinction between code evidence and fully documented runtime recipe.
- The bundled asset checker only validates layout and presence; it does not train or decode models.
