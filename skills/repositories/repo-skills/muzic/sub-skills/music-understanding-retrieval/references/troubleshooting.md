# Troubleshooting: MusicBERT, PDAugment, and CLaMP

Use this guide after selecting the workflow-specific reference. Most Muzic failures in this sub-skill come from missing external data, old dependency stacks, path assumptions, first-run downloads, or source scripts that assume a specific working directory.

## Fast triage table

| Symptom | Likely cause | First checks | Recovery direction |
|---|---|---|---|
| MusicBERT raw output directory already exists and script exits | Source generators refuse to overwrite | Confirm whether partial files are complete | Move/rename incomplete output or resume manually with explicit plan. |
| `fairseq-preprocess` or `fairseq-train` not found | Wrong environment | `which fairseq-preprocess`; Python/Fairseq version | Activate the MusicBERT environment; avoid mixing with CLaMP/PDAugment envs. |
| MusicBERT train launcher fails near `nvidia-smi` or update frequency | No CUDA GPU visible or `nvidia-smi` missing | `nvidia-smi`; GPU count | Use a CUDA environment or patch launcher for a non-training dry run only. |
| MusicBERT eval fails at `.cuda()` | Evaluator is GPU-only as written | CUDA availability; checkpoint/data path | Run on GPU or patch evaluator intentionally for CPU debugging. |
| `RobertaModel.from_pretrained` cannot find user module | Wrong working directory or missing Fairseq user-dir | command cwd; `--user-dir musicbert` path | Run from the MusicBERT source working directory or adjust user-dir path. |
| Genre eval only checks fold 0 | Source evaluator sets `n_folds = 1` | evaluator settings | Loop externally over folds or edit the fold count intentionally. |
| CLaMP starts downloading unexpectedly | First run lacks local HF assets | model directory/cache; network policy | Pre-stage model/tokenizer assets or run with network approval. |
| CLaMP MusicXML conversion fails before inference | MusicXML loader uses a Windows-style shell command | OS, converter invocation, `.mxl` validity | Patch conversion command or pre-convert to acceptable ABC text through equivalent tooling. |
| CLaMP returns stale or surprising key results | Cached key features no longer match key set/model | `inference/cache/*_key_cache_*.pth` | Delete cache for the modal/model length and rerun. |
| CLaMP text keys appear fewer than expected | Blank lines are skipped | Inspect `text_keys.txt` | Remove blank lines or accept skipped lines. |
| PDAugment direct positional command crashes with missing globals | Source CLI branch does not load frequency/pickle/MIDI list after parsing args | Traceback for `fre`, `mel_data`, or empty random choice | Patch/wrap source after argument parsing; validate layout first. |
| PDAugment produces no outputs and no clear error | Worker catches all exceptions and returns | Output dirs; one-utterance trace; logs | Run a one-item debug wrapper with exceptions surfaced. |
| PDAugment cannot find MIDI file | String concatenation without path separator or empty MIDI list | MIDI folder contents; path join | Ensure trailing separator or patch to `os.path.join`; populate MIDI list from configured folder. |
| PDAugment `ffmpeg`/WORLD/librosa fails | Missing system/audio dependencies | `ffmpeg -version`; package imports | Use a dedicated PDAugment environment and test a one-second WAV. |

## MusicBERT-specific checks

### Interactive generators

`preprocess.py`, `gen_nsp.py`, and `gen_genre.py` prompt for inputs and exit when output directories already exist. Capture prompt responses in run logs so a later agent can reproduce exactly which dataset prefix was generated.

Expected prompt map:

| Script | Prompts |
|---|---|
| `preprocess.py` | dataset zip path; OctupleMIDI output path |
| `gen_nsp.py` | task: `next` or `acc` |
| `gen_genre.py` | subset: `topmagd` or `masd`; LMD zip path; sequence length |

### Fairseq binarization

If binarization fails, check the exact raw files expected by each launcher:

```text
pretrain:  {prefix}_data_raw/dict.txt, midi_train.txt, midi_valid.txt, midi_test.txt
NSP:       {task}_data_raw/dict.txt, train.txt, train.label, test.txt, test.label
genre:     {subset}_data_raw/{fold}/dict.txt, train.txt, train.label, test.txt, test.label
```

The shell scripts exit if `{prefix}_data_bin` already exists.

### Checkpoint naming

Training launchers derive checkpoint suffixes from task, fold, and source checkpoint basename. When evaluation cannot locate a checkpoint, reconstruct the expected suffix from the training command rather than guessing.

Examples:

```text
nsp_next_checkpoint_last_musicbert_base
genre_topmagd_0_checkpoint_last_musicbert_base
```

### GPU and batch math

The shell launchers compute:

```text
UPDATE_FREQ = BATCH_SIZE / MAX_SENTENCES / N_GPU_LOCAL
```

A missing GPU count leads to invalid shell arithmetic. A small GPU count changes effective update frequency; record visible GPU count with training logs.

## CLaMP-specific checks

### Layout before model load

Use the validator first:

```bash
python scripts/validate_clamp_inputs.py --inference-dir inference --query-modal text --key-modal music --top-n 5
```

For music keys, validate that `.mxl` files are readable zip files. For text keys, count non-empty lines and ensure `top_n` is not accidentally larger than the candidate set.

### Model and tokenizer downloads

The source `from_pretrained` method downloads CLaMP model files manually if the named local directory does not exist. Transformers may separately download `distilroberta-base` assets. If network is disallowed, pre-stage these caches or restrict the task to input validation and command planning.

### MusicXML conversion portability

The loader invokes `inference/xml2abc.py` through a Windows-style command wrapper. If running outside Windows, test conversion independently before model inference. A failure here is not a model-quality issue.

### Cache reset

Delete the relevant cache if:

- key files changed but results look unchanged;
- switching between 512 and 1024 model lengths caused tensor mismatch;
- a previous run was interrupted while writing cache;
- text key order changed and you need clean ranking provenance.

## PDAugment-specific checks

### Validate all data joins

The final augmentation joins five data sources:

1. metadata CSV row;
2. `wav` path from that row;
3. `new_wav` key in alignment pickle;
4. randomly selected processed MIDI file;
5. frequency JSON mapping for note/octave conversion.

Any mismatch can silently skip work because the worker catches broad exceptions.

### One-utterance debug before full corpus

Before scaling to many threads:

- run or wrap one metadata row;
- force one known MIDI file rather than random selection;
- surface exceptions instead of swallowing them;
- confirm duration, pitch, and combined outputs all appear;
- inspect output length and clipping/no-speech artifacts.

### Source CLI hazards

The inspected source defaults and CLI parser are not equivalent. With positional arguments supplied, important globals may not be loaded. With no arguments, defaults are loaded but MIDI names are read from a hard-coded folder name. Prefer a small wrapper or source patch that:

- loads frequency JSON after parsing args;
- loads alignment pickle after parsing args;
- populates MIDI paths from the configured processed MIDI folder;
- uses `os.path.join` for MIDI paths;
- creates pitch and PDAugment output directories explicitly;
- logs exceptions with metadata row identifiers.

### Audio/system dependencies

PDAugment combines Python audio libraries and system tools:

- FLAC-to-WAV conversion uses `ffmpeg`.
- Duration change uses `ffmpeg` `atempo` filters on temporary WAV cuts.
- Pitch shifting uses WORLD vocoder routines through `pyworld`.
- WAV I/O uses `librosa` and `soundfile`.

Version mismatches can affect audio duration and sample-rate behavior. Keep the PDAugment environment isolated from MusicBERT and CLaMP.

## Reporting unresolved blockers

When a run cannot proceed, report blockers in this order:

1. Missing or inaccessible dataset/checkpoint/model asset.
2. Missing system tool or Python package.
3. Backend mismatch such as no CUDA for GPU-only script.
4. Source portability issue requiring patch/wrapper.
5. Budget or runtime limit.

Include the exact command attempted, the validated input layout, and the earliest failing signal. Avoid claiming model failure when the problem is data layout, dependency setup, or source portability.
