# GETMusic

GETMusic covers any-track symbolic generation with two interactive modes:
track generation and position generation / infilling.
It also exposes a preprocessing chain that builds the OctupleMIDI training data and vocabulary.

## What the model expects

GETMusic works with a fixed six-track layout plus chord guidance:

| Index | Track |
|---|---|
| 0 | lead |
| 1 | bass |
| 2 | drum |
| 3 | guitar |
| 4 | piano |
| 5 | string |
| 6 | chord guidance |

Instrument program IDs used by the shipped examples:

| Program | Meaning |
|---|---|
| 0 | piano |
| 25 | guitar |
| 32 | bass |
| 48 | string |
| 80 | lead melody |
| 128 | drums |

Chord guidance is inferred from the input MIDI. The shipped track-generation prompt mentions `c` as a possible selection, but the code keeps chord handling separate from the user-controlled content track list.

## Mode 1: track generation

Use this when you want to keep some tracks and generate new content tracks.

```bash
python track_generation.py --load_path /path/to/checkpoint --file_path example_data/inference
```

The script iterates over each MIDI file in the input folder and prompts for two selections:

1. condition tracks
2. content tracks

### Condition prompt grammar

The prompt accepts any combination of these letters:

| Letter | Meaning |
|---|---|
| `l` | lead |
| `b` | bass |
| `d` | drum |
| `g` | guitar |
| `p` | piano |
| `s` | string |
| `c` | chord guidance |

The shipped code treats `c` as a chord-guidance concept, but the actual conditioning map is built from the musical track letters and the chord guidance is inferred from the input MIDI.

### Content prompt grammar

The content prompt accepts:

| Letter | Meaning |
|---|---|
| `l` | lead |
| `b` | bass |
| `d` | drum |
| `g` | guitar |
| `p` | piano |
| `s` | string |

### Workflow notes

- Do not select all tracks as condition; the code falls back to an unconditional branch.
- If no content track is selected, the script skips the file.
- The output name follows the selected condition/content pattern.
- Chord guidance is inferred automatically from the input MIDI content.

## Mode 2: position generation / infilling

Use this when you want to condition on spans of specific tracks and empty out other spans.

```bash
python position_generation.py --load_path /path/to/checkpoint --file_path example_data/inference
```

The script shows a track/position layout and then asks for two commands:

- positions to condition on
- positions to empty

### Position command grammar

Each command is a semicolon-separated list of `track_id,start,end` segments.

| Field | Meaning |
|---|---|
| `track_id` | 0 lead, 1 bass, 2 drum, 3 guitar, 4 piano, 5 string, 6 chord |
| `start` | inclusive start position |
| `end` | exclusive end position; leave blank to run until the end |

Examples:

```text
0,0,200;6,0,
1,0,;4,0,;5,0,
```

A single `-` means “no command” and leaves the positions unchanged.

### Reading the prompt correctly

- Positions are time positions, not bars.
- The command is track-index based, not program-ID based.
- `empty` wins over `condition` when the same region is declared both ways.

## Preprocessing and vocabulary build

The bundled example data shows the order of the preprocessing chain.
Use the small example folders to confirm the file layout before touching a larger corpus.

### Step 1: OctupleMIDI conversion

```bash
python preprocess/to_oct.py example_data/train example_data/processed_train
```

This writes the processed octuple text file:

- `example_data/processed_train/oct.txt`

### Step 2: Build the token dictionary

```bash
python preprocess/make_dict.py example_data/processed_train 3
```

Important side effect:

- the resulting dictionary is written as `pitch_dict.txt`
- the `tracks_start` and `tracks_end` values in the MIDI config must match the output token layout

### Step 3: Binarize train and valid splits

```bash
python preprocess/binarize.py example_data/processed_train/pitch_dict.txt example_data/processed_train/oct.txt example_data/processed_train
```

Expected outputs in the processed folder include:

- `train.data`, `train.idx`, `train_length.npy`
- `valid.data`, `valid.idx`, `valid_length.npy`

## Training configuration

Before training, update the config to point at your processed data:

| Field | What to set |
|---|---|
| `solver.vocab_size` | token count in `pitch_dict.txt` plus 1 for `[EMPTY]` |
| `solver.vocab_path` | path to `pitch_dict.txt` |
| `dataloader.*.path` / `data_folder` fields | your processed data directory |

Then run:

```bash
python train.py
```

## Practical notes

- The model is designed around a six-track pop-style layout.
- Incremental generation works well: generate a core track first, then fill the accompaniment.
- The code normalizes to C major / A minor when building the representation.
- Domain gaps matter; style mismatch often hurts generation quality.
- A copied chord progression in the input MIDI is the safest way to steer harmony.

## Safe validation helper

Use [scripts/validate_getmusic_request.py](../scripts/validate_getmusic_request.py) to catch invalid track letters or malformed position commands before a GPU run.
