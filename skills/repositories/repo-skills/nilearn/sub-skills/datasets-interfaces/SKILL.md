---
name: datasets-interfaces
description: "Use Nilearn dataset/template/atlas fetchers and public interfaces
  for cache-aware, BIDS-aware, and fMRIPrep-aware workflows without accidental
  network-heavy actions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Nilearn Datasets and Interfaces

Use this sub-skill when the task involves `nilearn.datasets` fetchers/loaders,
dataset cache choices, atlas/template selection, OpenNeuro/NeuroVault helpers,
BIDS file discovery, fMRIPrep confound loading, or FSL design text loading.

## Route Here

- **No-network templates:** Prefer local loaders such as `load_mni152_template`,
  `load_mni152_brain_mask`, `load_fsaverage`, and `load_fsaverage_data` when a
  task only needs a template, mask, or bundled `fsaverage5` surface. See
  [workflows](references/workflows.md).
- **Download-aware datasets:** Treat most `fetch_*` functions as network and
  cache operations. Require an explicit `data_dir` for reproducibility and
  confirm large downloads, external terms, or credentials before running. See
  [API reference](references/api-reference.md).
- **Atlas selection:** Choose deterministic label atlases, probabilistic map
  atlases, or coordinate sets based on the downstream masker/analysis contract.
  See [data formats](references/data-formats.md).
- **OpenNeuro and NeuroVault:** Use `fetch_ds000030_urls`, `select_from_index`,
  `fetch_openneuro_dataset`, `fetch_neurovault`, or `fetch_neurovault_ids` only
  with bounded filters and clear download intent. See [troubleshooting](references/troubleshooting.md).
- **BIDS/fMRIPrep/FSL interfaces:** Use `get_bids_files`, `parse_bids_filename`,
  `load_confounds`, `load_confounds_strategy`, and `get_design_from_fslmat` for
  local derivative inspection and confound extraction. See
  [data formats](references/data-formats.md).

## Route Elsewhere

- Route first-level or second-level statistical model construction, contrasts,
  and BIDS GLM writing to `../glm-analysis/SKILL.md`.
- Route decoding, connectome, or machine-learning examples that merely consume
  fetched datasets to `../ml-decoding-connectivity/SKILL.md`.
- Route plotting, HTML reports, display objects, and figure export for dataset
  outputs to `../plotting-reporting/SKILL.md`.
- Route low-level Niimg loading, masking, resampling, and signal cleaning after
  data discovery to `../data-io-signal/SKILL.md`.
- Route surface-specific mesh/image object manipulation to
  `../surface-workflows/SKILL.md`.

## Quick Checklist

1. Decide whether a local `load_*` helper is sufficient before using any
   `fetch_*` downloader.
2. Set `data_dir` explicitly, or document the environment-variable/home cache
   fallback chosen by `get_data_dirs`.
3. Bound network fetches with subject counts, filters, atlas dimensions, or
   NeuroVault/OpenNeuro URL subsets.
4. Inspect returned `Bunch` keys before assuming whether `maps`, `labels`,
   `lut`, file paths, images, or DataFrames are present.
5. For fMRIPrep, pass the processed image path, not the TSV path; the associated
   confounds TSV/JSON must be in the same directory with supported BIDS names.

## Bundled Script

Run `python scripts/inspect_dataset_fetchers.py --help` for options. The default
`python scripts/inspect_dataset_fetchers.py` mode lists public dataset/interface
entry points and exercises only safe local loaders when Nilearn and its runtime
dependencies are importable; it does not trigger downloads.

## References

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Data formats](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Fetcher inspection script](scripts/inspect_dataset_fetchers.py)
