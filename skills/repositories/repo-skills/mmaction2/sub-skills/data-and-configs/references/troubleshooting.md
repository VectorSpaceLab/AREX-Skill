# MMAction2 data/config troubleshooting

Use this table to diagnose data and config problems before routing to training, testing, or inference execution.

## Annotation and prefix errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'video'` while building a video dataset | `VideoDataset` or `VideoTextDataset` expects `data_prefix=dict(video=...)`. | Change the prefix key to `video`, or use `dict(video=None)` only if filenames are complete. |
| `KeyError: 'img'` with raw frames or AVA | `RawframeDataset` and frame-based `AVADataset` expect `data_prefix=dict(img=...)`. | Change `data_prefix` from `video` to `img`, then verify the loader is `RawFrameDecode`. |
| `KeyError: 'audio'` with `AudioDataset` | Audio configs expect `data_prefix=dict(audio=...)`. | Use `dict(audio=FEATURE_ROOT)` and keep annotation filenames relative to that root. |
| Media path is doubled or points to the wrong directory | Both `data_root` and `data_prefix`/annotation values include the same root segment. | Decide whether paths are rooted by `data_root` or by complete annotation entries; do not include the same component twice. |
| Dataset length is zero after filtering | Wrong split name, `valid_ratio` too strict, AVA exclude file removes all timestamps, or annotation identifiers do not match split keys. | Print split names/first identifiers from the annotation file; relax `valid_ratio`; inspect exclude rows; verify `frame_dir` vs `filename` identifiers. |

## Classification annotation errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError` converting label to int | Label column is missing, a class name string was used, or a path contains unescaped whitespace. | Use integer labels; avoid spaces in file paths or use a supported delimiter consistently for `VideoDataset`. |
| `AssertionError` about label length in `RawframeDataset` or `AudioDataset` | `multi_class=False` but a line has multiple labels. | Set `multi_class=True` and `num_classes`, or reduce each line to one label. |
| One-hot conversion fails or labels out of range | Multi-label labels exceed `num_classes - 1`. | Recompute `num_classes` and remap labels to contiguous integer ids. |
| Supervised training sees label `-1` | A `VideoDataset` or `RawframeDataset` line omitted the label. | Add labels to supervised annotations; unlabeled lines are only safe for inference-like use. |

## Rawframe decoding errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| File-not-found for `img_00001.jpg` | `filename_tmpl` or `start_index` does not match extracted frame names. | Inspect one frame directory; set `filename_tmpl` and `start_index` to match actual names. |
| Sampled frame index exceeds available files | `total_frames` in the annotation is larger than actual frame count, or offset/clip length is wrong. | Correct `total_frames`; if using clips, set `with_offset=True` and verify `offset total_frames`. |
| Flow pipeline cannot find x/y frames | `modality='Flow'` but frame templates/prefixes are RGB-only or missing paired flow files. | Use a flow-specific template/prefix convention and verify both x and y components exist. |
| Rawframe config still uses `DecordInit`/`OpenCVInit` | Pipeline was not changed when dataset type changed. | Replace video init/decode transforms with `SampleFrames` + `RawFrameDecode`. |

## Encoded video decode errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Decoder import error (`decord`, `av`, or OpenCV backend) | Optional video decoding dependency is absent. | Switch to an installed decoder in the config or install the optional dependency in the user's environment. |
| Decoder reports zero frames or cannot open video | Bad codec, corrupt file, unsupported container, or wrong path. | Test a tiny sample with a non-destructive video check; consider re-encoding only after user confirmation. |
| Test results differ unexpectedly from validation | Test pipeline uses more clips/crops or `test_mode` differs. | Compare `val_pipeline` and `test_pipeline`; ensure intended `num_clips`, crop strategy, and `test_mode=True`. |

## Pose/skeleton errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Assertion that pose annotation must end with `.pkl` | `PoseDataset` expects a pickle annotation file. | Convert skeleton annotations into a pickle layout with `split`/`annotations` or a list of annotation dicts. |
| Shape mismatch in pose transforms | `keypoint` is not `[M, T, V, C]` or `keypoint_score` is not `[M, T, V]`. | Rebuild or transpose the annotation arrays; verify `T == total_frames`. |
| Graph layout error or wrong number of keypoints | Pipeline/backbone layout does not match keypoint format. | Keep `coco`, `nturgb+d`, `openpose`, or custom layout consistent in both graph config and transforms. |
| `valid_ratio` filtering assertion | Kinetics-pose filtering requested but `box_score`/`valid` fields are absent or `box_thr` is not allowed. | Remove `valid_ratio`, add required fields, or choose `box_thr` from `0.5` to `0.9` in increments of `0.1`. |

## Audio errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing label assertion | `AudioDataset` requires at least one label per annotation line. | Add integer labels or use an inference-specific path outside supervised data loading. |
| Audio feature selector index error | Feature length, `total_frames`, and `SampleFrames` settings are inconsistent. | Verify feature frame count and original-video `total_frames`; reduce clip length/interval for a tiny check. |
| Import error for audio feature generation dependencies | Optional audio preprocessing dependencies are absent. | Do not run feature generation automatically; ask user to confirm environment and output plan. |

## AVA and spatio-temporal detection errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CSV parse error or wrong number of columns | AVA annotation rows are not exactly `video_id,timestamp,x1,y1,x2,y2,label,entity_id`. | Normalize to eight comma-separated fields with numeric timestamp, coordinates, label, and entity id. |
| Assertion about proposal coordinates | Proposal boxes are pixel coordinates, not normalized `[0, 1]`. | Convert proposals to normalized coordinates or use a config/evaluator expecting pixel coordinates. |
| No proposals above threshold | `person_det_score_thr` too high or proposal scores are poorly calibrated. | Lower the threshold; the dataset keeps at least the top-scoring proposal when scores exist. |
| Custom class assertion | `custom_classes` includes `0`, is not in the label map, or `num_classes` is not `len(custom_classes)+1`. | Remove `0`, validate ids against the label file, and update model/dataset/evaluator class counts together. |
| Missing boxes after spatial transforms | A recognition-only crop/format step dropped or failed to update box fields. | Use AVA-compatible sampling, resize/crop/flip, `FormatShape(..., collapse=True)`, and `PackActionInputs`. |
| Timestamp mismatch between GT and proposals | Proposal keys use a different timestamp format or FPS convention. | Use keys like `video_id,0902`; set `fps=1` only for frame-counted datasets and verify `timestamp_start/end`. |

## Localization errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Feature CSV not found | `ActivityNetDataset` constructs `feature_path` as `data_prefix.video / (video_name + '.csv')`. | Rename feature files or update `data_prefix.video`; keep JSON keys equal to feature basenames without `.csv`. |
| Localization labels are empty or invalid | Annotation `segment` values are outside `duration_second` or reversed. | Validate segment start/end seconds and video duration metadata. |
| Pipeline tries to decode frames | A recognition pipeline was copied into a localization config. | Use `LoadLocalizationFeature`, `GenerateLocalizationLabels`, and `PackLocalizationInputs`. |

## Video-text errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| JSON loads but dataset size is larger than video count | Expected behavior: each text caption becomes a separate sample. | Account for one sample per `(video, text)` pair in batch sizing and evaluation. |
| Missing `text` key downstream | Annotation JSON maps to a string instead of a list of strings, or a custom pipeline removed text. | Use `{"video.mp4": ["caption one", "caption two"]}` and keep tokenizer/pack steps after decode. |
| Tokenizer dependency missing | Text pipeline requires an optional tokenizer/model package. | Route dependency/model issues to models-and-extension or inference/training owner depending on the requested action. |

## Config and override errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `_base_` file cannot be found | Relative inheritance path is wrong for the config's location. | Move the config next to its expected bases or rewrite `_base_` to valid paths. |
| Override is ignored | Wrong dotted key path or overriding a top-level variable that is no longer used after dataloader expansion. | Inspect resolved config with the bundled script; override the actual nested field, such as `train_dataloader.dataset.ann_file`. |
| Override list becomes a string | Missing shell quotes around list/tuple values. | Use `key="[1,2,3]"` or edit the config file directly for complex structures. |
| `train_pipeline.0.type=...` fails | Pipeline is inherited under a different name or is embedded only inside dataloader dataset. | Inspect both top-level pipeline variables and dataset pipeline lists; override the path that exists. |
| Registry error for a transform/dataset/model type | Custom class is not registered or default scope/imports are wrong. | If the task is to implement/register custom classes, route to models-and-extension; otherwise use built-in type names. |
| Config parse executes unexpected code | Config files are Python. | Only inspect trusted user-provided configs. For untrusted configs, request a sanitized config excerpt instead of loading it. |

## Final triage rule

If the failure occurs before a dataset/model is built, stay in this sub-skill. If the failure occurs while launching training/testing or evaluating metrics, route to training-and-evaluation. If it occurs during prediction or demo visualization, route to inference-and-demos. If it requires adding or registering code, route to models-and-extension.
