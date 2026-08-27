# Data Formats

## Dataset `Bunch` Outputs

Nilearn dataset fetchers usually return `sklearn.utils.Bunch`, a dict-like
object whose keys are also attributes. Do not assume a single schema across all
fetchers. Inspect keys and route downstream work based on what is present.

Common fields:

| Field | Meaning | Typical downstream route |
| --- | --- | --- |
| `maps` | Atlas/statistical map path, image, or 4D map file. | `maskers-regions`, `data-io-signal`, or `plotting-reporting`. |
| `labels` | Region/component names or a `DataFrame` of label metadata. | Pair with atlas map semantics before masker use. |
| `lut` | Look-up table with at least index/name-style region metadata. | Prefer over position-based label guesses for deterministic atlases. |
| `atlas_type` | Usually `deterministic` or `probabilistic`. | Determines labels masker vs maps masker decisions. |
| `template` | Space/template label such as `MNI152NLin6Asym`, `MNI152`, `fsaverage`, `MNIColin27`, or `Talairach`. | Match or resample user images before analysis. |
| `description` | Dataset description string. | Useful for provenance and user-facing summaries. |
| `func`, `anat`, `events`, `session_target`, `confounds`, `phenotypic`, `ext_vars` | Example dataset files/tables. | GLM, decoding, connectome, or signal-cleaning workflows depending on task. |
| `images`, `images_meta`, `collections_meta`, `word_frequencies` | NeuroVault-specific downloaded images and metadata. | Metadata filtering, plotting, or analysis after explicit download. |

## Atlas Contracts

- **Deterministic atlas:** `maps` is usually a 3D label image where integer
  values map to region labels or `lut` rows. Some atlases, such as AAL, use
  explicit `indices` rather than list positions; do not treat `labels[i]` as
  map value `i` unless the fetcher states that contract.
- **Probabilistic atlas:** `maps` is usually a 4D image where each volume is a
  region/component map. Labels, when present, align with volumes.
- **Coordinate sets:** coordinate fetchers return arrays/tables such as `rois`
  and labels, not a NIfTI map. Use spheres/seed workflows rather than labels
  image workflows.
- **Surface atlas/data:** outputs may be GIFTI file paths, Freesurfer annotation
  labels, `PolyMesh`, or `SurfaceImage`. Keep hemisphere and vertex-count
  contracts with `surface-workflows`.

## BIDS Path Signals

`parse_bids_filename` extracts:

- `file_path`: original path string;
- `file_basename`: basename only;
- `extension`: suffix after the first dot in the last underscore-separated
  filename part, such as `nii.gz`, `json`, or `tsv`;
- `suffix`: final BIDS suffix, such as `bold`;
- `entities`: parsed key-value fields such as `sub`, `ses`, `task`, `run`,
  `space`, `desc`, `hemi`, `den`, and `res`.

`get_bids_files` expects a BIDS-like folder layout. With `sub_folder=True`, it
searches under `sub-*`, optional `ses-*`, and a modality folder such as `func`.
For derivatives, pass the derivatives root as `main_path`.

## fMRIPrep Confounds Files

`load_confounds` discovers files from the processed image path:

- Regular NIfTI: image name matches `*_desc-preproc_bold.nii.gz` with optional
  `space-*`; confounds are adjacent `*_desc-confounds_timeseries.tsv` or older
  `*_desc-confounds_regressors.tsv` plus JSON sidecar.
- CIFTI: image name matches `*_bold.dtseries.nii`; adjacent confounds use the
  same BIDS entities.
- GIFTI: pass a left/right pair matching `*_hemi-L*_bold.func.gii` and
  `*_hemi-R*_bold.func.gii`; confounds are discovered from the shared entities.
- ICA-AROMA full: pass `*_desc-smoothAROMAnonaggr_bold.nii.gz` and use
  `strategy=("ica_aroma",)` with `ica_aroma="full"`.
- TEDANA: pass `*_desc-optcom_bold.nii.gz`; Nilearn expects exactly two TSVs,
  one mixing file and one metrics/status file, and does not use a JSON sidecar.

Returned `sample_mask` is `None` when no volumes are removed; otherwise it is an
array of retained time indices after non-steady-state and scrubbing outliers. A
list input returns lists of confounds and masks unless it is recognized as one
GIFTI pair.

## Confound Column Expectations

- Motion uses `trans_x`, `trans_y`, `trans_z`, `rot_x`, `rot_y`, `rot_z`, plus
  suffixes for derivatives/quadratic variants.
- `wm_csf` uses `csf` and `white_matter`, plus selected suffixes.
- `global_signal` uses `global_signal`, plus selected suffixes.
- `high_pass` loads columns containing `cosine`.
- `scrub` needs `framewise_displacement` and `std_dvars`.
- `non_steady_state` columns are always detected when present.
- Anatomical CompCor requires JSON metadata to map component columns.
- CamelCase confound headers indicate unsupported fMRIPrep 1.0/1.1-era files;
  headerless numeric columns indicate an even older unsupported format.

## FSL Design Matrix Text

`get_design_from_fslmat` reads an FSL design matrix file after the `/Matrix`
line and returns numeric rows as a `pandas.DataFrame`. Provide `column_names`
that match the number of matrix columns when downstream code needs stable names.
