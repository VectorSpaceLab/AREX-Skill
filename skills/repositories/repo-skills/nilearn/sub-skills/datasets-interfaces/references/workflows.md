# Workflows

## Choose a Data Directory and Cache Policy

1. Prefer an explicit `data_dir` supplied by the user or project config.
2. If no explicit directory is available, call `get_data_dirs()` to explain the
   search order before downloads: `NILEARN_SHARED_DATA`, `NILEARN_DATA`, then
   `~/nilearn_data`.
3. Use one stable cache root per workflow so later calls can reuse downloads.
4. For automation, bound every fetch with `n_subjects`, atlas dimension,
   selected URLs, `max_images`, or an equivalent filter.
5. Do not delete or overwrite caches unless the user asks; use `resume=True`
   when available and `verbose=0` for quiet scripted checks.

Example cache-aware pattern:

```python
from nilearn import datasets

data_dir = "./nilearn_data"
paths = datasets.get_data_dirs(data_dir=data_dir)
atlas = datasets.fetch_atlas_schaefer_2018(
    n_rois=100,
    yeo_networks=7,
    resolution_mm=2,
    data_dir=data_dir,
    verbose=0,
)
print(paths, atlas.maps, atlas.labels[:3])
```

## Prefer No-Network Template Loaders

Use local loaders when a task only needs coordinates, a mask, a template image,
or a smoke input:

```python
from nilearn import datasets

template = datasets.load_mni152_template(resolution=2)
mask = datasets.load_mni152_brain_mask(resolution=2)
fsaverage = datasets.load_fsaverage(mesh="fsaverage5")
sulcal = datasets.load_fsaverage_data(mesh="fsaverage5")
```

Important details:

- `load_mni152_*` functions return in-memory `Nifti1Image` objects.
- `fetch_surf_fsaverage(mesh="fsaverage5")` returns package-shipped file paths;
  other meshes can download.
- `load_fsaverage(mesh="fsaverage5")` returns `PolyMesh` objects; route mesh
  manipulation to `surface-workflows`.
- If a user requests TemplateFlow-specific resources, explain that Nilearn ships
  selected MNI/fsaverage resources and uses download fetchers for broader
  template data.

## Choose an Atlas Fetcher

1. Identify the downstream consumer:
   - labels masker or integer regions: deterministic label atlas;
   - maps masker or soft assignment: probabilistic 4D maps;
   - spheres or seed extraction: coordinate set.
2. Match the space/template (`MNI152NLin6Asym`, `MNI152`, `MNIColin27`,
   `fsaverage`, or Talairach) to the user data or plan a resampling step.
3. Inspect `atlas.atlas_type`, `atlas.template`, `atlas.labels`, `atlas.lut`,
   and `atlas.maps` before wiring to maskers.
4. Route masker fitting/region extraction to `maskers-regions` after the atlas
   choice is made.

Common choices:

- `fetch_atlas_schaefer_2018`: deterministic cortical parcels; tune `n_rois`,
  `yeo_networks`, and `resolution_mm`.
- `fetch_atlas_harvard_oxford` / `fetch_atlas_juelich`: FSL-based deterministic
  or probabilistic atlases; avoid `symmetric_split=True` for probabilistic maps.
- `fetch_atlas_difumo`, `fetch_atlas_msdl`, `fetch_atlas_smith_2009`:
  probabilistic/components maps for maps maskers or network examples.
- `fetch_coords_power_2011`, `fetch_coords_dosenbach_2010`,
  `fetch_coords_seitzman_2018`: coordinate seeds for spheres workflows.
- `fetch_atlas_surf_destrieux`: surface labels; route surface object work to
  `surface-workflows`.

## Use fMRIPrep Confounds

Use `load_confounds_strategy` for common denoising presets and
`load_confounds` when the user needs exact component control.

```python
from nilearn.interfaces.fmriprep import load_confounds_strategy

confounds, sample_mask = load_confounds_strategy(
    "sub-01_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
    denoise_strategy="simple",
    motion="full",
    wm_csf="basic",
)
```

Recovery checklist for fMRIPrep inputs:

1. Pass the processed image path, not the confounds TSV path.
2. Keep the image, `desc-confounds_timeseries.tsv` or
   `desc-confounds_regressors.tsv`, and JSON sidecar in the same directory.
3. Use `denoise_strategy="simple"` first for broad compatibility.
4. Switch to `denoise_strategy="compcor"` only when the JSON sidecar exists and
   the fMRIPrep version supports anatomical CompCor metadata.
5. Use `denoise_strategy="scrubbing"` when the user expects a `sample_mask` for
   high-motion/non-steady-state volumes.
6. For GIFTI, pass a left/right pair; for CIFTI, pass the `.dtseries.nii` path;
   for TEDANA, pass the `desc-optcom_bold.nii.gz` file and expect TEDANA mixing
   and metrics TSVs.
7. Hand `confounds` and `sample_mask` to a masker or `nilearn.signal.clean`; use
   `demean=True` for default `NiftiMasker`, and consider `demean=False` when
   cleaning signals with defaults.

## Use BIDS and OpenNeuro Helpers

For local BIDS discovery:

```python
from nilearn.interfaces.bids import get_bids_files, parse_bids_filename

bold_files = get_bids_files(
    "./bids_root",
    file_tag="bold",
    file_type="nii.gz",
    sub_label="01",
    modality_folder="func",
    filters=[("task", "rest")],
)
parsed = [parse_bids_filename(path) for path in bold_files]
```

For OpenNeuro downloads:

1. Fetch or provide a URL list.
2. Reduce it with `select_from_index` using inclusion/exclusion filters and
   `n_subjects`.
3. Call `fetch_openneuro_dataset(urls=selected, data_dir=...)`.
4. Let `patch_openneuro_dataset` run as part of the fetcher to create BIDS-like
   symlinks where needed.

Avoid `fetch_openneuro_dataset(urls=None)` in unattended work unless the user
explicitly accepts the default full dataset index behavior.

## Use NeuroVault Helpers

Use `fetch_neurovault_ids` when IDs are known and `fetch_neurovault` when the
selection is metadata-driven. Always bound broad searches:

```python
from nilearn.datasets import fetch_neurovault

maps = fetch_neurovault(
    max_images=5,
    image_terms={"modality": "fMRI-BOLD"},
    collection_terms={},
    data_dir="./nilearn_data",
    mode="download_new",
)
```

Set `mode="offline"` when the user only wants local cached NeuroVault data.
Pass `{}` for `image_terms` or `collection_terms` only when intentionally
disabling Nilearn's default filters.

## Use FSL Text Loaders

Use `get_design_from_fslmat(path, column_names=[...])` to load an FSL `.mat`
design matrix as a `pandas.DataFrame`. It reads lines after `/Matrix`; if the
file has additional custom sections, inspect the output shape and column count
before passing it to GLM code.
