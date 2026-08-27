# Classification and Regression Workflows

Use these workflows from an installed pyAudioAnalysis environment. Keep outputs in a deliberate work directory because the training APIs write pickle artifacts as side effects.

## 1. Train and use a folder-based classifier

### Prepare data

Create one folder per class:

```text
training-data/
  speech/
    s01.wav
    s02.wav
  music/
    m01.wav
    m02.wav
heldout/
  speech/
  music/
models/
```

Operating requirements:

- At least two class folders.
- Enough files per class for internal train/validation splits; use more than one or two clips per class for real training.
- Audio clips should be longer than the mid-term window and not near-silent.
- Use WAV for the most predictable path; other supported formats may need optional decoders.

### Train

```python
from pathlib import Path
from pyAudioAnalysis import audioTrainTest as aT

work = Path("models")
work.mkdir(parents=True, exist_ok=True)

class_dirs = ["training-data/speech", "training-data/music"]
model_prefix = str(work / "speech_music_svm")

aT.extract_features_and_train(
    class_dirs,
    mid_window=1.0,
    mid_step=1.0,
    short_window=aT.shortTermWindow,
    short_step=aT.shortTermStep,
    classifier_type="svm",
    model_name=model_prefix,
    compute_beat=False,
    train_percentage=0.9,
    dict_of_ids=None,
    use_smote=False,
)
```

For short synthetic clips, reduce `mid_window` and `mid_step` (for example `0.5, 0.5`) rather than using clips shorter than the model window.

### Classify one file

```python
class_id, probs, classes = aT.file_classification(
    "unknown.wav",
    model_prefix,
    "svm",
)

if class_id == -1:
    raise RuntimeError("classification failed; check audio path, model path, and model type")

winner = classes[int(class_id)]
score = float(probs[int(class_id)])
print({"winner": winner, "score": score, "classes": list(classes)})
```

### Evaluate held-out folders

```python
cm, thr_prre, pre, rec, thr_roc, fpr, tpr = aT.evaluate_model_for_folders(
    ["heldout/speech", "heldout/music"],
    model_prefix,
    "svm",
    positive_class="speech",
    plot=False,
)
print(cm)
```

Set `plot=False` unless an interactive HTML plot in the current working directory is desired.

## 2. Batch classify a folder through the API

This mirrors the folder-classification behavior without relying on CLI parsing.

```python
from collections import Counter
from glob import glob
from pathlib import Path
from pyAudioAnalysis import audioTrainTest as aT

model_prefix = "models/speech_music_svm"
model_type = "svm"
files = sorted(glob("incoming/*.wav"))
counts = Counter()
rows = []

for audio_path in files:
    class_id, probs, classes = aT.file_classification(audio_path, model_prefix, model_type)
    if class_id == -1:
        rows.append({"file": audio_path, "error": "classification_failed"})
        continue
    label = classes[int(class_id)]
    counts[label] += 1
    rows.append({
        "file": audio_path,
        "label": label,
        "probability": float(probs[int(class_id)]),
    })

print({"counts": dict(counts), "rows": rows})
```

For command-line syntax, route to the `cli-and-io` sub-skill rather than duplicating CLI catalogs here.

## 3. Use grouped evaluation to avoid leakage

If files from the same speaker/session/recording family appear in multiple class folders, provide `dict_of_ids` so internal evaluation can split by group instead of by file.

```python
from pathlib import Path
from pyAudioAnalysis import audioTrainTest as aT

class_dirs = ["train/cough", "train/non_cough"]
groups = {}
for path in Path("train").glob("*/*.wav"):
    # Example: speaker id is the text before the first underscore.
    groups[str(path)] = path.name.split("_")[0]

aT.extract_features_and_train(
    class_dirs,
    1.0, 1.0,
    aT.shortTermWindow, aT.shortTermStep,
    "svm_rbf",
    "models/cough_svm_rbf",
    dict_of_ids=groups,
)
```

The keys must match the full filename strings discovered by the package. If paths are relative in `class_dirs`, build `dict_of_ids` with the same relative form.

## 4. Train and use audio regression

### Prepare data

```text
emotion-regression/
  001.wav
  002.wav
  valence.csv
  arousal.csv
```

Example `valence.csv`:

```csv
001.wav,0.12
002.wav,0.87
```

Each CSV file creates one regression target.

### Train

```python
from pyAudioAnalysis import audioTrainTest as aT

errors, baselines, params = aT.feature_extraction_train_regression(
    "emotion-regression",
    mid_window=1.0,
    mid_step=1.0,
    short_window=aT.shortTermWindow,
    short_step=aT.shortTermStep,
    model_type="svm_rbf",
    model_name="models/emotion",
    compute_beat=False,
)
print({"errors": errors, "baselines": baselines, "params": params})
```

### Predict

```python
values, names = aT.file_regression("emotion-regression/001.wav", "models/emotion", "svm_rbf")
print(dict(zip(names, [float(v) for v in values])))
```

Use `svm`, `svm_rbf`, or `randomforest` for regression training and file inference. Avoid `knn` regression in this package version even if a legacy folder parser exposes it.

## 5. Run the bundled smoke script

From this sub-skill directory, inspect options first:

```bash
python scripts/classification_smoke.py --help
```

Then run a bounded synthetic smoke test:

```bash
python scripts/classification_smoke.py --classifier svm
```

By default the script writes two temporary tone class folders under an auto-created temporary work directory and removes them after the run. Add `--keep-work-dir` or pass a project scratch directory with `--work-dir` if you need to inspect generated WAVs and model files; do not place smoke outputs inside the skill tree. The script patches the package's expensive hyperparameter evaluation to a fixed bounded selector, trains a classifier through `extract_features_and_train(...)`, classifies a held-out tone, and prints a JSON result. It is a functionality smoke test, not a model-quality benchmark.

## 6. Boundary reminders

- Need raw feature matrices, short-term features, or feature names? Route to `feature-extraction`.
- Need segment-by-segment classification, HMM segmentation, or diarization? Route to `segmentation-diarization`.
- Need all `audioAnalysis.py` command forms and top-level-import execution notes? Route to `cli-and-io`.
