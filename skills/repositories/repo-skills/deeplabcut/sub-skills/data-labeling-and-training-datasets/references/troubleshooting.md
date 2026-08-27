# Troubleshooting Data Labeling And Training Dataset Creation

Use this guide for failures before training starts: frame extraction, labels, CSV/HDF conversion, shuffles, trainset metadata, and multi-animal table shape.

## Frame extraction problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `extract_frames` extracts no images. | Video path in `config.yaml` is wrong, video cannot be opened, or `start`/`stop` select an empty interval. | Check each `video_sets` key, verify the file opens outside DeepLabCut, set `0 <= start < stop <= 1`, and try `algo="uniform"` with a tiny `numframes2pick` first. |
| Extracted images are black or constant. | Video decoder issue, bad video segment, or moviepy/opencv backend mismatch. | Try `opencv=True` if not already, inspect the source video around the selected interval, and regenerate/convert the video if needed. |
| `Erroneous start or stop values`. | `start` or `stop` in `config.yaml` is outside `[0, 1]` or `start >= stop`. | Edit `config.yaml` and rerun extraction. |
| Prompt blocks automation. | `userfeedback=True`, `mode="manual"`, or `crop="GUI"`. | For non-interactive runs, use `userfeedback=False`, `mode="automatic"`, and pre-filled crop coordinates or `crop=False`. |
| Existing label folder causes an add/delete prompt. | `labeled-data/<video-stem>/` already contains frames. | If keeping old labels, use `userfeedback=True` and answer carefully. If output is disposable, use a fresh project/folder or delete the label folder before extraction. |
| K-means frame selection is slow or memory-heavy. | Long/high-resolution videos and small `cluster_step`. | Increase `cluster_step`, lower `cluster_resizewidth`, use `uniform`, crop frames, or extract from shorter `start`/`stop` windows. |
| Multi-camera matched extraction overwrote labels. | `mode="match"` can delete matching-camera PNGs to replace them. | Restore from backup if needed. Use matched extraction only before labeling the target camera or after explicitly deciding to regenerate its labels. |

## Label and `check_labels` problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Attention: <folder> does not appear to have labeled data!` | Missing `CollectedData_<scorer>.h5`, wrong scorer filename, or video stem mismatch. | Check `config.yaml` `scorer` and `video_sets`; ensure `labeled-data/<video-stem>/CollectedData_<scorer>.h5` exists. Convert CSV to HDF if only CSV exists. |
| Rendered labels are shifted, flipped, or on wrong frames. | Row image paths do not match the images, external coordinate origin differs, crop conversion was not applied, or images were replaced after labeling. | Compare row index values with actual image filenames. Re-export external labels in pixel coordinates for the stored images. Do not train until rendered checks are correct. |
| Some labels appear missing. | Occluded points were intentionally left `NaN`, bodypart names do not match config, or columns were dropped during reindexing. | Distinguish intentional occlusions from schema errors. Verify spelling/case of every bodypart in columns and `config.yaml`. |
| Skeleton drawing fails or looks wrong. | `skeleton` has bodypart names not present in the project or connects unique maDLC bodyparts incorrectly. | Disable `draw_skeleton` for diagnosis, then repair `skeleton` so it only references valid project bodyparts. Unique bodyparts should not be connected to multi-animal bodyparts. |
| Multi-animal colors are confusing. | `visualizeindividuals=True` colors individuals, while `False` colors bodyparts. | Run `check_labels` both ways. Use individual colors to diagnose ID assignment and bodypart colors to diagnose bodypart swaps. |

## CSV/HDF conversion problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `convertcsv2h5` cannot find the CSV. | Filename must be `CollectedData_<config-scorer>.csv` in each configured label folder unless the project scorer is first corrected. | Rename files or update `config.yaml` scorer. If importing another scorer, pass `scorer="<target>"` after confirming the active filename. |
| Converted HDF has the wrong scorer. | The CSV scorer level differed from `config.yaml`. | Re-run `convertcsv2h5(config, scorer="<config-scorer>", userfeedback=False)` on a backup or disposable copy. |
| CSV loads with wrong columns or rows. | Header rows/index columns do not match standard or multi-animal DeepLabCut CSV layout. | Standard CSVs need `scorer/bodyparts/coords` header levels. Multi-animal CSVs need `scorer/individuals/bodyparts/coords`. Row paths should identify `labeled-data/<video-stem>/<image>`. |
| HDF writing fails with a PyTables-related error. | Pandas HDF support is missing from the Python environment. | Install the HDF dependency used by Pandas in the active DeepLabCut environment, or use an environment where DeepLabCut's HDF operations are already verified. |
| Training labels include `likelihood` columns. | Prediction files or non-label exports were reused as annotations. | Use true annotation files with x/y only. DeepLabCut drops `likelihood` during formatting in some paths, but relying on that can hide a wrong data source. |

## Training-dataset and shuffle problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `No data was found!` during dataset creation. | No valid `CollectedData_<scorer>.h5` files were found for configured videos, or labels are under a different scorer. | Run `check_labels`; verify per-video label folder names and scorer level. Convert or rename data as needed. |
| Labels by another scorer are ignored. | Merged label table's first scorer level does not match `config.yaml` scorer. | Use `convertcsv2h5(..., scorer=<config-scorer>)` or edit/convert the HDF/CSV scorer level intentionally. |
| Merged table is empty after reindexing. | `config.yaml` bodyparts do not match label columns. | Compare `bodyparts`/`multianimalbodyparts`/`uniquebodyparts` with the HDF columns exactly. Repair spelling, capitalization, and spaces. |
| `Cannot create shuffle ... as it already exists`. | Requested `Shuffles` index is already present and `userfeedback=True`. | Pick a new shuffle index, or deliberately overwrite using `userfeedback=False` only after deleting/archiving the corresponding trainset/model outputs. |
| `Number of Shuffles and train and test indexes should be equal.` | The lengths of `Shuffles`, `trainIndices`, and `testIndices` differ. | Wrap each split in a list and pass matching counts, e.g. `Shuffles=[3]`, `trainIndices=[train_idx]`, `testIndices=[test_idx]`. |
| `TrainingFraction` ratio mismatch when reusing splits. | Split sizes cannot represent the rounded fraction exactly. | Let `create_training_dataset_from_existing_split` handle padding, or use `mergeandsplit(..., uniform=True)` to produce compatible indices. |
| `metadata.yaml` missing or source shuffle not found. | Existing project was created by an older flow, files were deleted, or the requested shuffle/trainset index is wrong. | Recreate the source shuffle, restore its documentation pickle, or create metadata from existing documentation files before using `create_training_dataset_from_existing_split`. |
| A shuffle exists in metadata but not in model folders. | Files were manually deleted or moved. | Decide whether to recreate the shuffle, remove stale metadata, or point downstream calls at an existing valid shuffle. Do not train/evaluate from inconsistent metadata. |
| TensorFlow weights download unexpectedly starts during dataset creation. | TensorFlow engine selected with a net that checks pretrained weights. | Prefer `engine=deeplabcut.Engine.PYTORCH` for DeepLabCut 3 unless TensorFlow is intentionally required, or ensure the required cache/network/permissions are available. |

## Multi-animal-specific problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `At least one individual should exist`. | `convert2_maDLC` was called with multi-animal bodyparts but no configured individual. | Add at least one name under `individuals` or pass a valid `forceindividual` after editing config. |
| Unique bodyparts train as if they belong to an animal. | Unique columns were placed under a named individual instead of `single`. | Move unique-bodypart columns to the `individuals` level value `single`, and keep them listed under `uniquebodyparts`. |
| Multi-animal bodyparts are not repeated for all animals. | Column MultiIndex is incomplete. | For each `individuals` entry, include each `multianimalbodyparts` name with `x` and `y` coordinates. Missing observations in a frame should be `NaN`, not missing columns. |
| PAF/skeleton validation fails. | Skeleton or custom PAF graph connects invalid bodyparts or unique bodyparts. | Use only valid multi-animal bodypart indices/names for PAF edges. Do not connect `uniquebodyparts` to multi-animal bodyparts. |
| Training crop memory issues are anticipated for large maDLC images. | Multi-animal augmentation may crop large images into patches, but large crop sizes and batch sizes still affect memory. | For dataset creation, record `crop_size` and `crop_sampling`; route actual memory tuning and training settings to the training/evaluation sub-skill. |
| Identity labels seem inconsistent. | For indistinguishable animals, per-frame identity can legitimately swap; for distinguishable animals, it should not. | Decide whether the task needs persistent identity labels. Use `identity: true` only when identity supervision is intentional and labels support it. |

## Safe recovery checklist

Before retrying a failed trainset creation:

1. Back up or copy the project if any labels are valuable.
2. Run `check_labels` and inspect rendered label images.
3. Confirm every configured video stem has one label folder and one `CollectedData_<scorer>.h5`.
4. Confirm standard versus multi-animal column levels match `config.yaml`.
5. Choose new shuffle ids unless intentionally replacing old outputs.
6. Keep training, evaluation, inference, and tracking decisions out of the retry; this sub-skill ends after trainset/shuffle artifacts are valid.
