# API reference

This sub-skill wraps the time-structured audio behavior from
`pyAudioAnalysis.audioSegmentation` and the legacy annotation splitter.

## Core segmentation APIs

| API | Purpose | Inputs and units | Returns | Notes |
| --- | --- | --- | --- | --- |
| `train_hmm_from_file(wav_file, gt_file, hmm_model_name, mid_window, mid_step)` | Train one HMM segmentation model from a single annotated recording. | `wav_file` must be readable audio; `gt_file` must be a tab-separated `.segments` file with `<start sec>\t<end sec>\t<label>`; `mid_window` and `mid_step` are seconds. | `(hmm, class_names)` | Saves the HMM, class names, `mid_window`, and `mid_step` into `hmm_model_name`. |
| `train_hmm_from_directory(folder_path, hmm_model_name, mid_window, mid_step)` | Train one HMM from many labeled WAV files in a folder. | `folder_path` should contain paired `.wav` and `.segments` files that share the same stem. | `(hmm, class_names_all)` | Missing `.segments` files are skipped. |
| `hmm_segmentation(audio_file, hmm_model_name, plot_results=False, gt_file='')` | Load an HMM model and predict time-window labels. | `audio_file` is the target WAV; `gt_file` is optional `.segments` sidecar; plotting is off by default. | `(labels, class_names, accuracy, cm)` | If `gt_file` exists, it is used for evaluation and plotting. |
| `mid_term_file_classification(input_file, model_name, model_type, plot_results=False, gt_file='')` | Apply a saved classifier to a file and convert window labels to segments. | `model_type` must match the saved classifier family (`svm`, `svm_rbf`, `knn`, `randomforest`, `gradientboosting`, `extratrees`). | `(labels, class_names, accuracy, cm)` | Not for model training. Models that include long-term beat features are rejected for segmentation. |
| `evaluate_segmentation_classification_dir(dir_name, model_name, method_name)` | Batch-evaluate a folder of WAV + `.segments` pairs. | `method_name` selects the branch; lower-case classifier names use classifier segmentation, anything else routes to HMM. | `None` | Prints aggregate metrics only. |
| `silence_removal(signal, sampling_rate, st_win, st_step, smooth_window=0.5, weight=0.5, plot=False)` | Detect non-silent spans in a signal array. | `signal` is a NumPy audio array; all window arguments are seconds. | `seg_limits` | Returns a list of `[start_sec, end_sec]` intervals; no files are written by the API itself. |
| `speaker_diarization(filename, n_speakers, mid_window=1.0, mid_step=0.1, short_window=0.1, lda_dim=0, plot_res=False)` | Cluster a recording into speaker-like regions. | `filename` is a WAV; `n_speakers <= 0` enables auto-search; `lda_dim=0` disables LDA. | `(cls, purity_cluster_m, purity_speaker_m)` | Returns a label per mid-term window. Purity values are only meaningful when a matching `.segments` file exists. |
| `speaker_diarization_evaluation(folder_name, lda_dimensions)` | Batch diarization evaluation for a folder of recordings. | `folder_name` should contain WAV files with matching `.segments` sidecars; `lda_dimensions` is a list of integers. | `None` | Useful for quick sweeps over LDA settings. |
| `music_thumbnailing(signal, sampling_rate, short_window=1.0, short_step=0.5, thumb_size=10.0, limit_1=0, limit_2=1)` | Find the most self-similar two thumbnail regions in a song. | `signal` is a NumPy audio array; all time-like arguments are seconds. | `(A1, A2, B1, B2, sim_matrix)` | Returns two time spans and the filtered similarity matrix. |

## Annotation splitting helpers

| API | Purpose | Inputs | Returns | Notes |
| --- | --- | --- | --- | --- |
| `annotation2files(wavFile, csvFile)` | Cut one audio file into flat WAV clips from a tab-separated annotation file. | `csvFile` rows must contain `<start sec>\t<end sec>\t<label>`. | `None` | Output filenames are derived from the source audio name, label, and start/end times. |
| `annotation2folders(wavFile, csvFile, folderPath)` | Cut one audio file into class folders. | Same annotation format as above. | `None` | Creates `folderPath/<label>/...` directories as needed. |
| `folderAnnotation2folders(sourceFolder, targetFolder)` | Apply the folder split to every `.segments` file in a folder. | `sourceFolder` should contain paired WAV and `.segments` files. | `None` | A thin batch helper around `annotation2folders`. |

## Internal helpers worth knowing

- `read_segmentation_gt(gt_file)` reads the tab-separated segment format used by
  the HMM and diarization workflows.
- `labels_to_segments(labels, window)` converts frame labels to time spans.
- `segments_to_labels(start_times, end_times, labels, window)` converts segment
  spans back into per-window labels.
- `save_hmm(hmm_model_name, model, classes, mid_window, mid_step)` stores the
  HMM artifact as a sequential pickle stream.
- `calculate_confusion_matrix(...)` and `compute_metrics(...)` are the
  evaluation helpers behind the directory-level workflows.

## Legacy task names

The legacy script entry point `audioAnalysis.py` maps these APIs to task names
such as `trainHMMsegmenter_fromfile`, `trainHMMsegmenter_fromdir`,
`segmentClassifyFileHMM`, `segmentationEvaluation`, `silenceRemoval`,
`speakerDiarization`, and `thumbnail`.

The legacy `audacityAnnotation2WAVs.py` script exposes the annotation splitting
helpers.
