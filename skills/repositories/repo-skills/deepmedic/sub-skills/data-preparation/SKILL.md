---
name: data-preparation
description: "Prepare, validate, and troubleshoot DeepMedic 0.8.4 NIFTI
  subjects, modality manifests, labels, ROI masks, CSV inputs, and intensity
  normalization before training, validation, or inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepMedic data preparation

Use this skill when a Researcher must turn a new multi-modal NIFTI dataset into
DeepMedic input, or diagnose a path, list, grid, label, ROI, or normalization
failure. Establish the subject ordering and spatial contract first; only then
hand the prepared inputs to the session-specific skill.

## Route by need

- Read [references/data-formats.md](references/data-formats.md) for the
  canonical NIFTI, manifest, CSV, label, ROI, and normalization contracts.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a
  preflight check, loader warning, shape error, label error, or z-score result
  is unexpected.
- Run the safe standalone checker at
  [scripts/validate_nifti_manifest.py](scripts/validate_nifti_manifest.py) for
  explicit channel list files. It does not import DeepMedic or mutate data.
- After data passes this skill, route architecture decisions to
  [../model-architecture/SKILL.md](../model-architecture/SKILL.md), training
  execution to [../training/SKILL.md](../training/SKILL.md), and testing/output
  handling to [../inference/SKILL.md](../inference/SKILL.md).

## Required preparation workflow

1. **Define the subject table.** Give every subject one row/order. For each
   row, record the modality paths in fixed channel order, and optionally one
   label and one ROI path. Never independently sort one modality list after
   assembling the table.
2. **Choose one input representation.** Use classic per-channel list files or
   the supported dataframe branch. For list files, put one data path per line;
   relative data paths are relative to that list file. For CSV, use
   `channel_<name>` columns and remember that the implementation sorts those
   column names alphabetically. See the data-formats reference for required
   `ground_truth`, optional `roi_mask`, and optional `prediction_filename`
   signals.
3. **Prepare the spatial grid.** All modalities, labels, and ROI masks for a
   subject must be co-registered and have the same voxel-array shape and voxel
   size. Resample/crop/orient the complete subject set together before making
   manifests. Use one voxel size throughout the database. Do not expect
   DeepMedic to register or resample files at load time.
4. **Prepare labels and ROI.** Training labels are required. Background is `0`
   and task classes are contiguous increasing integers (`0, 1, 2, ...`); with
   `N` output classes, values must be in `[0, N)`. ROI is optional: absent ROI
   means whole-volume sampling/inference and whole-volume normalization
   statistics. A provided ROI uses positive voxels as inside.
5. **Validate without changing data.** Run the bundled checker once for all
   channel list files, with optional labels/ROI. It checks list lengths, file
   existence, NIFTI loading/dimensionality, per-subject shape and voxel-size
   agreement, and optional affine and label constraints. Use
   `--read-data` for a full payload read. Also inspect voxel-size consistency
   across subjects and verify co-registration visually or with a trusted
   imaging QA process; those are not fully proven by a header check.
6. **Decide normalization explicitly.** Prefer data whose intensity policy is
   known. If applying runtime z-score, configure one mode only: all channels or
   a boolean per-channel list. Statistics use positive ROI voxels, or the full
   volume without ROI; cutoffs only control statistic estimation. Check for an
   empty/constant selected region and avoid double-normalizing exported data.
7. **Record the handoff.** Preserve the final channel order, case count, input
   representation, grid/resampling policy, label set/class count, ROI policy,
   normalization parameters, validator result, and any intentional missing
   modality (`-`) in the task notes. A later session skill should consume this
   record rather than reconstructing it from filenames.

## Exact runtime contracts

The source-backed data I/O and preprocessing signatures are:

```text
load_volume(filepath)

saveImgToNiiWithOriginalHdr(imgToSave, filepathTarget,
                            filepathOriginToCopyHeader,
                            npDtype=np.dtype(np.float32), log=None)

savePredImgToNiiWithOriginalHdr(labelImageCreatedByPredictions,
                                namesForSavingPreds,
                                listOfFilepathsToEachChannelOfEachPatient,
                                case_i, suffixToAdd="",
                                npDtype=np.dtype(np.float32), log=None)

saveFmImgToNiiWithOriginalHdr(fmImageCreatedByVisualisation,
                              namesForSavingPreds,
                              listOfFilepathsToEachChannelOfEachPatient,
                              image_i, index_of_typeOfPathway_to_visualize,
                              index_of_layer_in_pathway_to_visualize,
                              index_of_FM_in_pathway_to_visualize, log=None)

save4DImgWithAllFmsToNiiWithOriginalHdr(multidimImageWithAllVisualisedFms,
                                        namesForSavingFms,
                                        listOfFilepathsToEachChannelOfEachPatient,
                                        image_i, log=None)

normalize_zscore_subj(log, channels, roi_mask, prms,
                      verbose_lvl=0, job_id='', in_place=True)

parse_filelist(filelist_path, make_abs=False)
parse_fpaths_of_channs_from_filelists(list_of_filelists, abs_path_root)
get_paths_from_df(log, df, abs_path, req_gt=True)
```

`load_volume` returns a 3-D NumPy array: 2-D becomes `x,y,1`; 4-D is allowed
only with singleton fourth dimension. The NIFTI save helpers copy the source
header affine and relevant zooms; the generic helper creates parent folders
and appends `.nii.gz` when the target does not already end in that suffix.
Prediction/feature helpers derive output names from per-case name tokens and
use the first channel as the header source. They are output helpers, not a
replacement for input registration.

`normalize_zscore_subj` expects channels shaped `[channels, x, y, z]` and an
ROI shaped `[x, y, z]` or `None`. `prms` contains
`apply_to_all_channels`, `apply_per_channel`, `cutoff_percents`,
`cutoff_times_std`, and `cutoff_below_mean`; incompatible all/per-channel
selection is rejected. It returns `(channels, applied)`, mutating the input
by default. The long-form behavior and failure cases are in the references.

## Scope boundary

This sub-skill does not choose CNN pathways, class-head architecture, patch
sizes, optimizer settings, training schedules, checkpoint loading, or feature
map inference. Do not “repair” a data error by changing those settings. Use
the three linked sibling skills only after this input contract is satisfied.

## Evidence and version caveat

This operating contract follows DeepMedic 0.8.4 source behavior for I/O,
manifest parsing, dataframe extraction, subject loading, label checks, and
normalization. The prose documentation calls dataframe input new/not yet
used, while the 0.8.4 parser contains active dataframe branches; follow the
code when the two conflict. The prose also says `.nii`, while the bundled
examples use `.nii.gz`; the loader delegates to NiBabel and the examples show
that both common NIFTI suffixes are an intended safe contract. The bundled
example names illustrate two modalities, labels, and brain masks only; they
are not a requirement that a new task have exactly two channels or a brain
ROI.
