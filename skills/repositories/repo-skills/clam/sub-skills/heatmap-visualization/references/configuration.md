# Heatmap Configuration Reference

`create_heatmaps.py` loads YAML with `yaml.safe_load(open(os.path.join('heatmaps/configs', args.config_file)))`. Pass only the config filename to `--config_file` after placing or copying the YAML under `heatmaps/configs/`; passing a full path is usually wrong because the script prepends `heatmaps/configs/`.

## Required YAML Sections

A practical heatmap config has these top-level sections from the CLAM template:

- `exp_arguments`: experiment identity, output directories, class count, and inference batch size.
- `data_arguments`: slide locations, process-list CSV, slide extension, labels, and optional multi-source directory mapping.
- `patching_arguments`: patch size, overlap, pyramid level, and custom downsampling used for heatmap scanning.
- `encoder_arguments`: image encoder name and input image size.
- `model_arguments`: checkpoint path and CLAM model initialization arguments.
- `heatmap_arguments`: rendering, ROI, smoothing, percentile-score, and output-image controls.
- `sample_arguments`: optional patch-sampling requests from attention scores.

## `exp_arguments`

Important keys:

- `n_classes`: integer number of output classes. Must match both the checkpoint and `data_arguments.label_dict` values.
- `save_exp_code`: output tag used below the raw and production save roots.
- `raw_save_dir`: root for intermediate assets such as masks, HDF5 features, attention score maps, block maps, copied config, and per-slide processing summaries.
- `production_save_dir`: root for final rendered heatmaps, original-slide snapshots, and sampled patch PNGs.
- `batch_size`: ROI patch inference batch size for the encoder and CLAM attention model. Lower it for GPU memory failures.

`--save_exp_code` on the command line overrides `exp_arguments.save_exp_code`.

## `data_arguments`

Important keys:

- `data_dir`: either a string slide directory or a dictionary mapping source keys to slide directories.
- `data_dir_key`: process-list column used to choose a slide directory when `data_dir` is a dictionary.
- `process_list`: CSV filename resolved under `heatmaps/process_lists/`. If `null`, the script lists slides from `data_dir`.
- `preset`: optional segmentation/patching preset CSV path, commonly a path such as `presets/bwh_biopsy.csv`.
- `slide_ext`: extension appended to `slide_id` when absent, such as `.svs`.
- `label_dict`: mapping from class names to integer encodings. Its values should cover `0..n_classes-1`.

The process list must include `slide_id` when provided. It may include `label`, segmentation overrides (`seg_level`, `sthresh`, `mthresh`, `close`, `use_otsu`, `keep_ids`, `exclude_ids`), filter overrides (`a_t`, `a_h`, `max_n_holes`), visualization overrides (`vis_level`, `line_thickness`), and patching overrides (`use_padding`, `contour_fn`). The script fills missing segmentation/filter/visualization/patching columns from defaults or the preset.

If `heatmap_arguments.use_roi: true`, every processed row needs ROI coordinates `x1`, `x2`, `y1`, and `y2`. Coordinates are level-0 slide coordinates, used as `top_left=(x1, y1)` and `bot_right=(x2, y2)`.

## `patching_arguments`

Important keys:

- `patch_size`: square patch size used for reading WSI regions.
- `overlap`: fraction in `[0, 1)` for overlapping heatmap scanning. `--overlap` on the command line overrides this value.
- `patch_level`: OpenSlide pyramid level used for patch reads.
- `custom_downsample`: additional downsampling factor included in visualization patch-size calculations.

The script always computes a coarse non-overlapping block map. If `heatmap_arguments.calc_heatmap` is true, it also computes the overlapping/ROI attention HDF5 selected by `overlap` and `use_roi`.

## `encoder_arguments`

Important keys:

- `model_name`: supported CLAM choices are `resnet50_trunc`, `uni_v1`, and `conch_v1` for this workflow.
- `target_img_size`: default is `224`, matching the current CLAM feature-extraction guidance.

Feature dimension expectations:

- `resnet50_trunc`: use `model_arguments.embed_dim: 1024`.
- `uni_v1`: use `model_arguments.embed_dim: 1024` and set `UNI_CKPT_PATH` before runtime.
- `conch_v1`: use `model_arguments.embed_dim: 512`, install the CONCH dependency, and set `CONCH_CKPT_PATH` before runtime.

Keep the heatmap encoder consistent with the encoder family used to train the checkpoint. CLAM heatmap inference recomputes features from slide patches before applying the trained attention model.

## `model_arguments`

Important keys:

- `ckpt_path`: path to the trained CLAM checkpoint. The runtime loads it with `torch.load` and strict `model.load_state_dict`.
- `model_type`: `clam_sb` or `clam_mb` are the supported heatmap model types in `infer_single_slide`; non-CLAM MIL models are not implemented for heatmap attention inference.
- `initiate_fn`: must be `initiate_model` for the current script path.
- `model_size`: `small` or `big`; must match training.
- `drop_out`: dropout probability used at model construction; must match training checkpoint structure.
- `embed_dim`: feature dimension consumed by the model; match encoder and checkpoint.

`create_heatmaps.py` injects `exp_arguments.n_classes` into `model_arguments` before calling `utils.eval_utils.initiate_model`, so a wrong `n_classes` can also produce checkpoint shape errors.

## `heatmap_arguments`

Important keys:

- `vis_level`: downsample level for final rendering; `-1` uses the OpenSlide level closest to 32x downsample.
- `alpha`: heatmap overlay alpha; `0` shows background only, `1` shows foreground only.
- `blank_canvas`: render on a blank canvas instead of the slide image.
- `save_orig`: also save the original H&E visualization at the selected level.
- `save_ext`: output extension such as `jpg` or `png`.
- `use_ref_scores`: convert overlapping ROI scores relative to the non-overlapping reference score distribution.
- `blur`: apply Gaussian smoothing in the WSI heatmap renderer.
- `use_center_shift`: shift default corner points when testing foreground membership.
- `use_roi`: use `x1`, `x2`, `y1`, `y2` from the process list to restrict heatmap computation/rendering.
- `calc_heatmap`: compute the overlapping or ROI heatmap HDF5. The block map is still generated separately.
- `binarize`: render a binary attention map instead of continuous scores.
- `binary_thresh`: threshold for binarization; use a value in `[0, 1]` when `binarize` is true.
- `custom_downsample`: downsample factor for final heatmap visualization.
- `cmap`: Matplotlib colormap name such as `jet`.

`use_ref_scores` changes percentile conversion: when true, overlapping scores are percentile-normalized against coarse reference scores rather than converted independently during rendering.

## `sample_arguments`

The `samples` list controls optional patch exports from attention scores. Each item can include:

- `name`: subfolder tag for the sampled patch set.
- `sample`: boolean toggle.
- `seed`: random seed for range sampling.
- `k`: number of patches to export.
- `mode`: `topk`, `reverse_topk`, or `range_sample`.
- `score_start` and `score_end`: percentile window for `range_sample`; defaults are `0` and `1` in the heatmap script if absent.

Sampled patches are saved under `production_save_dir/save_exp_code/sampled_patches/<label_pred_tag>/<sample-name>/` with filenames containing coordinates and attention score.

## Safe Preflight Validation

From this sub-skill directory, run the bundled validator before expensive heatmap inference:

```bash
python scripts/validate_heatmap_config.py /path/to/heatmaps/configs/config_template.yaml
```

Use `--process-list-root /path/to/heatmaps/process_lists` when the config stores only a process-list filename. The validator reports errors for missing required structure and warnings for likely runtime mismatches, but it intentionally does not load slides, checkpoints, PyTorch, OpenSlide, or encoders.
