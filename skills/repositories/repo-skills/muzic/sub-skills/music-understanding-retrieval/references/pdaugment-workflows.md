# PDAugment Workflows

PDAugment is the Muzic branch for data augmentation by pitch and duration adjustment for automatic lyrics transcription. It reshapes natural speech toward singing-like audio by aligning speech phonemes with MIDI notes, shifting pitch toward the melody, and changing segment duration toward note durations.

## End-to-end pipeline

```text
LibriSpeech FLAC
  -> WAV conversion
  -> phoneme metadata CSV
  -> MFA phoneme-level alignment pickle

FreeMidi pop MIDI files
  -> MIDI preprocessing / lead-track extraction
  -> processed MIDI folder

alignment pickle + frequency JSON + WAV dataset + processed MIDI + metadata CSV
  -> duration-augmented WAV
  -> pitch-augmented WAV
  -> pitch-and-duration PDAugment WAV
```

Treat this as a corpus-scale workflow. The safe bundled helper validates layout only; it does not run ffmpeg, phonemizer, MFA, MIDI preprocessing, WORLD vocoder code, or augmentation.

## Speech data preparation

### 1. Convert FLAC to WAV

Expected LibriSpeech-style input:

```text
data/speech/raw/dev-clean/
  84/
    121123/
      84-121123-0000.flac
      84-121123-0001.flac
      84-121123.trans.txt
```

Command pattern:

```bash
python flac2wav.py data/speech/raw/dev-clean data/speech/wav
```

Expected output shape:

```text
data/speech/wav/dev-clean/
  84/
    121123/
      84-121123-0000.wav
      84-121123-0001.wav
      84-121123.trans.txt
```

Requirements and caveats:

- `ffmpeg` must be installed and on `PATH`.
- The source utility shells out per file and copies transcript files into the matching output directory.
- It assumes LibriSpeech two-level speaker/chapter nesting.

### 2. Convert text to phonemes

Command pattern:

```bash
python text2phone.py data/speech/wav/dev-clean data/speech/phone
```

Expected metadata CSV:

```text
data/speech/phone/dev-clean_metadata.csv
```

Required columns:

| Column | Meaning |
|---|---|
| `wav` | Path to source `.wav` file. |
| `new_wav` | Basename of the WAV file, used as key into the alignment pickle. |
| `txt` | Lower-cased transcript text. |
| `phone` | Word/syllable-separated phoneme string. |
| `new_phone` | `<BOS>`/`<EOS>` phoneme sequence consumed by augmentation. |

Requirements and caveats:

- Requires `phonemizer` and its backend dependencies.
- The source utility assumes the transcript filename is `<speaker>-<chapter>.trans.txt` inside each leaf directory.
- Validate output columns before launching augmentation.

### 3. Generate phoneme-level alignment pickle

The README describes using Montreal Forced Aligner, then post-processing alignment boundaries into a pickle dictionary.

Expected pickle shape:

```python
{
    "174-168635-0000.wav": [0, 12, 18, 20],
    "174-168635-0001.wav": [0, 12, 27, 35]
}
```

The values are split positions between adjacent phonemes for each utterance. The keys must match the `new_wav` values in the metadata CSV.

## MIDI score preparation

The augmentation step needs cleaned melody MIDI files. The README uses FreeMidi pop songs as the source corpus.

Expected raw input:

```text
data/midis/raw/
  *.mid
  *.midi
```

Environment pattern from the README:

```bash
conda create -n midi python=3.6 -y
conda activate midi
pip install -r midi_preprocess/requirements.txt
PYTHONPATH=. python midi_preprocess/preprocess.py --config midi_preprocess/configs/default.yaml
```

Expected processed output:

```text
data/midis/processed/midi_6tracks/
  *.mid
```

The preprocessing entry point reads a YAML config through its `set_hparams()` path, processes raw MIDI files, filters/merges tracks, and generates merged MIDI for training/augmentation. Keep this stage separate from the final PDAugment environment because it may have different dependencies.

## Frequency JSON

The final augmentation code maps MIDI notes to named note/octave frequencies. The bundled validator expects a JSON object shaped like:

```json
{
  "4": {
    "C": 261.63,
    "C#": 277.18,
    "A": 440.0
  }
}
```

The inspected frequency table covers octaves 2 through 6 and chromatic notes C through B.

## Final PDAugment positional arguments

The original README lists a `selected_dir` concept for selecting data for training/validation/testing, but the inspected `pdaugment.py` command-line parser consumes these nine positional arguments exactly:

```bash
python pdaugment.py \
  <pickle_path> \
  <frequency_json_file> \
  <dataset_dir> \
  <midi_file_fir> \
  <metadata_dir> \
  <output_duration_dir> \
  <output_pitch_dir> \
  <output_pdaugment_dir> \
  <number_of_threads>
```

Argument contract:

| Position | Name used by source | Example | Must exist before run? |
|---:|---|---|---|
| 1 | `pickle_path` | `data/pickle/mel_splits.pickle` | Yes |
| 2 | `frequency_json_file` | `utils/frequency.json` | Yes |
| 3 | `dataset_dir` | `data/speech/wav/dev-clean` | Yes |
| 4 | `midi_file_fir` | `data/midis/processed/midi_6tracks` | Yes |
| 5 | `metadata_dir` | `data/speech/phone/dev-clean_metadata.csv` | Yes |
| 6 | `output_duration_dir` | `data/duration` | Create or allow script to create descendants |
| 7 | `output_pitch_dir` | `data/pitch` | Create or allow script to create descendants |
| 8 | `output_pdaugment_dir` | `data/pdaugment` | Create or allow script to create descendants |
| 9 | `number_of_threads` | `16` | Positive integer |

Example command:

```bash
python pdaugment.py \
  data/pickle/mel_splits.pickle \
  utils/frequency.json \
  data/speech/wav/dev-clean \
  data/midis/processed/midi_6tracks \
  data/speech/phone/dev-clean_metadata.csv \
  data/duration \
  data/pitch \
  data/pdaugment \
  16
```

Expected output mirrors the source WAV nesting under the three output roots:

```text
data/duration/dev-clean/.../*.wav
data/pitch/dev-clean/.../*.wav
data/pdaugment/dev-clean/.../*.wav
```

## Layout validation helper

Use the bundled helper before running the source augmentation script:

```bash
python scripts/validate_pdaugment_layout.py \
  --pickle-path data/pickle/mel_splits.pickle \
  --frequency-json utils/frequency.json \
  --dataset-dir data/speech/wav/dev-clean \
  --midi-file-dir data/midis/processed/midi_6tracks \
  --metadata-csv data/speech/phone/dev-clean_metadata.csv \
  --output-duration-dir data/duration \
  --output-pitch-dir data/pitch \
  --output-pdaugment-dir data/pdaugment \
  --threads 16
```

What it checks:

- pickle file exists and has a plausible extension;
- frequency JSON is parseable and contains octave/note numeric mappings;
- dataset directory contains WAV files and transcript files when `--require-data` is active;
- metadata CSV has required columns and, optionally, WAV references that exist;
- MIDI directory contains `.mid` or `.midi` files;
- output roots exist or can be planned;
- thread count is positive.

The helper prints the final positional command so a future run can copy it after resolving warnings.

## Known implementation issues to check before running unmodified source

The inspected augmentation source has several portability and CLI hazards. Account for them in run plans:

1. The CLI branch parses the nine arguments but does not load `frequency_json_file`, `pickle_path`, or the MIDI file list after successful parsing. A direct README-style command may therefore fail later with missing globals or an empty MIDI list unless patched.
2. The no-argument branch prints “Need eight command line parameters” even though the command consumes nine positional arguments including thread count.
3. The no-argument branch reads MIDI names from a hard-coded `freemidi` folder rather than the parsed MIDI directory.
4. The worker concatenates `midi_file_fir + s_midi_path`; ensure a separator or patch path joining before corpus runs.
5. Pitch and PDAugment output directory creation calls create the duration directory variable in two branches; pre-create output roots and test on one utterance before a full run.
6. The augmentation worker silently returns on any exception, so missing audio/alignment/MIDI problems can look like skipped output rather than a loud failure.

For production use, run a one-utterance smoke test after patching or wrapping these issues, then scale thread count.

## Minimum preflight checklist

- `ffmpeg` works for one FLAC/WAV conversion.
- `phonemizer` produces metadata for one transcript leaf.
- MFA alignment pickle keys match metadata `new_wav` values.
- Metadata `wav` paths point to readable WAV files.
- Processed MIDI folder contains melody-like `.mid` files with note events in the first instrument.
- Frequency JSON contains note mappings for the expected MIDI octave range.
- Output roots are writable and not shared with raw data.
- The source script is patched or wrapped to load globals and MIDI file names after CLI argument parsing.
