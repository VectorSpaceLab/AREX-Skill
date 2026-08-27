# API Reference

This reference groups public Nilearn dataset and interface entry points by
agent decision. It intentionally avoids cataloging every atlas variant in full;
for exact parameter validation, inspect the function signature in the active
Nilearn version before running network fetches.

## Cache and Data Directory APIs

| API | Network by default? | Use for | Notes |
| --- | --- | --- | --- |
| `get_data_dirs(data_dir=None)` | No | Explain where Nilearn will look for datasets. | Priority is explicit `data_dir`, then `NILEARN_SHARED_DATA`, then `NILEARN_DATA`, then `~/nilearn_data`. A path list may use `os.pathsep`. |
| Most `fetch_*` APIs | Yes unless already cached or local test URL is supplied | Download/cache public datasets, atlases, templates, or indexes. | Prefer explicit `data_dir`, set `verbose=0` in automated probes, and consider `resume=True` where available. |
| Local `load_*` APIs | No for shipped resources; can download for non-shipped meshes | Load package-provided templates or already available surface data. | `fsaverage5` is shipped; other fsaverage meshes may download through `fetch_surf_fsaverage`. |

## Safe Local Loaders

These are the first choice for no-network examples and smoke checks:

| API | Returns | Important options |
| --- | --- | --- |
| `load_mni152_template(resolution=None)` | 3D `Nifti1Image` skull-stripped T1 template | `resolution=2` resamples to 2 mm. |
| `load_mni152_gm_template(resolution=None)` / `load_mni152_wm_template(resolution=None)` | 3D tissue probability-like template images | Use for grey/white matter examples without downloads. |
| `load_mni152_brain_mask(resolution=None, threshold=0.2)` | 3D mask image | Thresholds the local MNI template. |
| `load_mni152_gm_mask(resolution=None, threshold=0.2, n_iter=2)` / `load_mni152_wm_mask(...)` | 3D tissue masks | Applies thresholding plus binary closing. |
| `load_sample_motor_activation_image()` | Example statistical map image | Package-local sample image; useful for tiny no-network map workflows. |
| `fetch_surf_fsaverage(mesh="fsaverage5", data_dir=None)` | `Bunch` of fsaverage mesh/data file paths | `mesh="fsaverage5"` is shipped; other meshes can download. |
| `load_fsaverage(mesh="fsaverage5", data_dir=None)` | `Bunch` of `PolyMesh` objects | Avoid non-`fsaverage5` in no-network mode unless already cached. |
| `load_fsaverage_data(mesh="fsaverage5", mesh_type="pial", data_type="sulcal", data_dir=None)` | `SurfaceImage` | Use for surface-data smoke checks and route deeper surface handling to `surface-workflows`. |

## Dataset Fetcher Families

| Family | Representative APIs | Typical output | Network/data caveats |
| --- | --- | --- | --- |
| Structural templates | `fetch_icbm152_2009`, `fetch_icbm152_brain_gm_mask`, `fetch_oasis_vbm` | `Bunch` or image with template/GM/WM/mask file paths and metadata | `fetch_icbm152_2009` and OASIS download archives; OASIS has external data-use terms and can be large. |
| Functional examples | `fetch_haxby`, `fetch_adhd`, `fetch_miyawaki2008`, `fetch_localizer_*`, `fetch_spm_auditory`, `fetch_spm_multimodal_fmri`, `fetch_fiac_first_level`, `fetch_development_fmri`, `fetch_language_localizer_demo_dataset` | `Bunch` with image paths, behavioral/covariate tables, masks, events, or confounds | Bound subject counts. Some return first-level design material that should be handed to `glm-analysis` for modeling. |
| Atlases and coordinates | `fetch_atlas_aal`, `fetch_atlas_harvard_oxford`, `fetch_atlas_juelich`, `fetch_atlas_schaefer_2018`, `fetch_atlas_yeo_2011`, `fetch_atlas_difumo`, `fetch_atlas_msdl`, `fetch_coords_power_2011`, `fetch_coords_dosenbach_2010`, `fetch_coords_seitzman_2018` | `Bunch` with `maps`, `labels`, `lut`, `atlas_type`, `template`, or coordinate arrays | Deterministic atlases pair labels/LUT with integer map values; probabilistic atlases are often 4D maps. Choose based on masker expectations. |
| Surface datasets | `fetch_surf_fsaverage`, `load_fsaverage`, `load_fsaverage_data`, `fetch_surf_nki_enhanced`, `load_nki`, `fetch_atlas_surf_destrieux` | Surface file paths, `PolyMesh`, `SurfaceImage`, or surface time series | `fsaverage5` is safe locally; NKI and non-shipped meshes may download. Route object manipulation to `surface-workflows`. |
| Statistical maps and derivatives | `fetch_mixed_gambles`, `fetch_megatrawls_netmats`, `fetch_oasis_vbm`, `fetch_neurovault_auditory_computation_task` | Map paths, matrix files, or metadata tables | NeuroVault-derived functions can hit external services; cap counts and prefer offline/cache modes when possible. |
| OpenNeuro and indexes | `fetch_ds000030_urls`, `select_from_index`, `fetch_openneuro_dataset`, `patch_openneuro_dataset` | URL index, selected URL list, downloaded file list and data directory | `fetch_openneuro_dataset(urls=None)` can fetch a full default index and warns; pass a curated URL subset for automation. |
| NeuroVault search | `fetch_neurovault`, `fetch_neurovault_ids` plus filter helpers such as `IsIn`, `Contains`, `Pattern`, `ResultFilter` | `Bunch` with `images`, `images_meta`, `collections_meta`, and optional word features | Default modes query/download; use `max_images`, filters, and `mode="offline"` or `mode="download_new"` deliberately. |

## fMRIPrep Interfaces

| API | Signature highlights | Returns | Notes |
| --- | --- | --- | --- |
| `load_confounds(img_files, strategy=("motion", "high_pass", "wm_csf"), motion="full", scrub=5, fd_threshold=0.5, std_dvars_threshold=1.5, wm_csf="basic", global_signal="basic", compcor="anat_combined", n_compcor="all", ica_aroma="full", tedana="aggressive", demean=True)` | Full component selection. | `(confounds, sample_mask)` as a `DataFrame`/list and `None`/array/list. | Pass image files: preprocessed NIfTI/CIFTI/GIFTI, AROMA output, or TEDANA optcom output depending on strategy. |
| `load_confounds_strategy(img_files, denoise_strategy="simple", **kwargs)` | Presets: `simple`, `scrubbing`, `compcor`, `ica_aroma`. | Same as `load_confounds`. | Presets limit accepted kwargs and warn about irrelevant options. |

Strategy components accepted by `load_confounds` are `motion`, `high_pass`,
`wm_csf`, `global_signal`, `compcor`, `ica_aroma`, `tedana`, `scrub`, and
`non_steady_state`. `compcor` requires `high_pass`. `non_steady_state` is
always detected and does not need to be listed.

## BIDS and FSL Interfaces

| API | Use for | Notes |
| --- | --- | --- |
| `get_bids_files(main_path, file_tag="*", file_type="*", sub_label="*", modality_folder="*", filters=None, sub_folder=True)` | Glob BIDS-like raw or derivatives files. | For derivatives, pass the derivatives directory as `main_path`. Filters are `(entity, label)` tuples such as `("task", "rest")`. |
| `parse_bids_filename(img_path)` | Parse one BIDS-like filename. | Returns `file_path`, `file_basename`, `extension`, `suffix`, and `entities`. |
| `save_glm_to_bids(*args, **kwargs)` from `nilearn.interfaces.bids` | Legacy redirect only. | The public interface moved to `nilearn.glm`; route modeling/export tasks to `glm-analysis`. |
| `get_design_from_fslmat(fsl_design_matrix_path, column_names=None)` | Load FSL `.mat` design text into a `pandas.DataFrame`. | Reads rows after `/Matrix`; provide `column_names` when meaningful. |
