# Workflows

## 1. Train and reuse an HMM from one labeled file

1. Prepare `clip.wav` and a matching `clip.segments` file.
2. Ensure the segment file is tab-separated and uses seconds.
3. Train the model with `train_hmm_from_file(...)`.
4. Reuse the saved model with `hmm_segmentation(...)`.
5. If you need scoring, pass the same `clip.segments` file as `gt_file`.

```python
from pyAudioAnalysis import audioSegmentation as aS

hmm, class_names = aS.train_hmm_from_file(
    "clip.wav", "clip.segments", "clip_hmm.model", 1.0, 0.1
)
labels, class_names, accuracy, cm = aS.hmm_segmentation(
    "clip.wav", "clip_hmm.model", plot_results=False, gt_file="clip.segments"
)
```

Notes:
- `mid_window` and `mid_step` are seconds.
- `hmm_model_name` is a single artifact file that stores the model and its
  timing metadata together.
- Keep `plot_results=False` in batch or headless runs.

## 2. Train an HMM from a folder

1. Organize a folder so that every WAV has a same-stem `.segments` file.
2. Call `train_hmm_from_directory(folder_path, model_name, mid_window, mid_step)`.
3. Reuse the model with `hmm_segmentation(...)` or batch-score the folder with
   `evaluate_segmentation_classification_dir(..., method_name="hmm")`.

```python
from pyAudioAnalysis import audioSegmentation as aS

aS.train_hmm_from_directory("labeled_folder", "folder_hmm.model", 1.0, 0.1)
aS.evaluate_segmentation_classification_dir("labeled_folder", "folder_hmm.model", "hmm")
```

Notes:
- Missing sidecars are skipped during training.
- Batch evaluation only prints metrics when the matching GT files exist.

## 3. Use a saved classifier for mid-term segmentation

1. Train the classifier in the sibling classification workflow.
2. Reuse the saved model path here with `mid_term_file_classification(...)`.
3. Pass the same kind of `model_type` string that was used when training.
4. Inspect the returned per-window labels and aggregate metrics.

```python
from pyAudioAnalysis import audioSegmentation as aS

labels, class_names, accuracy, cm = aS.mid_term_file_classification(
    "clip.wav", "saved_classifier", "svm_rbf", False, "clip.segments"
)
```

Notes:
- This workflow is for inference and evaluation only.
- Models that include long-term beat features are rejected for segmentation.

## 4. Remove silence from a recording

1. Read the file with `audioBasicIO.read_audio_file(...)`.
2. Pass the returned signal array and sample rate to `silence_removal(...)`.
3. Treat the return value as time spans in seconds.
4. Cut audio only if you explicitly want files.

```python
from pyAudioAnalysis import audioBasicIO as aIO
from pyAudioAnalysis import audioSegmentation as aS

fs, signal = aIO.read_audio_file("speech.wav")
segments = aS.silence_removal(signal, fs, 0.05, 0.05,
                              smooth_window=0.5, weight=0.5, plot=False)
```

Notes:
- `weight` near `1` is stricter; near `0` is looser.
- The API returns intervals; the file-writing behavior lives in the legacy CLI
  wrapper.

## 5. Run speaker diarization

1. Provide a WAV file and a speaker-count guess.
2. Use `n_speakers > 0` when you know the count.
3. Use `n_speakers <= 0` to let the function search 2..9 clusters.
4. Leave `plot_res=False` in batch or CI runs.

```python
from pyAudioAnalysis import audioSegmentation as aS

cls, cluster_purity, speaker_purity = aS.speaker_diarization(
    "conversation.wav", 4,
    mid_window=1.0, mid_step=0.1,
    short_window=0.1, lda_dim=0,
    plot_res=False,
)
```

Notes:
- `cls` is a per-window cluster label sequence.
- If the audio has a matching `.segments` file, purity values are computed
  against it.
- If your environment hits the known purity-evaluation crash on same-stem
  `.segments` files, run the function on a temporary copy of the WAV that has
  no matching sidecar.
- `speaker_diarization_evaluation(...)` is the batch helper when you already
  have a folder of annotated recordings.

## 6. Find music thumbnails

1. Read or synthesize a signal array.
2. Call `music_thumbnailing(...)` with seconds-based windows.
3. Use the returned spans to cut two representative excerpts.
4. Inspect the similarity matrix only if you need a visual explanation.

```python
from pyAudioAnalysis import audioBasicIO as aIO
from pyAudioAnalysis import audioSegmentation as aS

fs, signal = aIO.read_audio_file("track.wav")
A1, A2, B1, B2, sim_matrix = aS.music_thumbnailing(signal, fs)
```

Notes:
- Increase `thumb_size` for longer thumbnails; reduce it for short clips.
- Very short or highly repetitive clips can produce degenerate thumbnails.

## 7. Split Audacity annotations into WAV clips

1. Prepare a tab-separated annotation file with `<start sec>\t<end sec>\t<label>`.
2. Use `annotation2files(...)` for flat output or `annotation2folders(...)` for
   class folders.
3. Keep the output root separate from the source audio tree.
4. If you need batch processing, use `folderAnnotation2folders(...)`.

Notes:
- This workflow slices by human annotations rather than classifying time windows.
- Output filenames should stay sanitized and under a controlled destination
  directory.

## 8. Smoke check the sub-skill

The bundled smoke script exercises a safe default path without needing a model:

```bash
python scripts/segmentation_smoke.py
```

Optional checks become active only when you supply the relevant paths:

```bash
python scripts/segmentation_smoke.py \
  --sample-wav demo.wav \
  --hmm-model demo_hmm.model \
  --n-speakers 4
```
