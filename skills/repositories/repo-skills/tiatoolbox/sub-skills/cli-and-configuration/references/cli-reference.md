# TIAToolbox CLI Reference

TIAToolbox installs a Click console command named `tiatoolbox`. The safe discovery commands are:

```bash
tiatoolbox --help
tiatoolbox --version
tiatoolbox <command> --help
```

Top-level help lists these commands: `deep-feature-extractor`, `multitask-segmentor`, `nucleus-detector`, `nucleus-instance-segment`, `patch-predictor`, `read-bounds`, `save-tiles`, `semantic-segmentor`, `show-wsi`, `slide-info`, `slide-thumbnail`, `stain-norm`, `tissue-mask`, and `visualize`.

## Command Families

| Family | Commands | Route deeper questions to | Use for |
| --- | --- | --- | --- |
| WSI inspection and extraction | `slide-info`, `slide-thumbnail`, `read-bounds`, `save-tiles` | `wsi-io` | Metadata, thumbnails, bounded region reads, and WSI tile export. |
| Image preprocessing | `tissue-mask`, `stain-norm` | `image-preprocessing` | Tissue mask generation and stain normalization before analysis. |
| Model inference | `patch-predictor`, `semantic-segmentor`, `nucleus-instance-segment`, `nucleus-detector`, `multitask-segmentor`, `deep-feature-extractor` | `model-inference` | Pretrained/custom model inference, masks, patch/stride settings, output formats, and devices. |
| Interactive visualization | `visualize`, `show-wsi` | `annotation-visualization` | Browser/Bokeh/TileServer viewing, layers, overlays, and color maps. |

## Shared CLI Patterns

TIAToolbox command options use `--kebab-case` names. Repeated or multi-value options follow Click behavior:

- `--img-input` is common and points to a file or directory; `show-wsi` accepts multiple `--img-input` values.
- `--output-path` usually points to an output directory; many utility commands create it in save mode.
- `--mode show|save` appears on WSI display/save commands; avoid `show` in headless automation unless the user asked for interactive display.
- `--file-types` is a comma-separated string of glob patterns such as `'*.svs, *.ndpi, *.jp2'`.
- `--units` commonly accepts `level`, `power`, `mpp`, or `baseline`, depending on the command.
- Options declared with `nargs=2` or `nargs=4` must be passed as separate tokens, for example `--region 0 0 2000 2000` or `--patch-input-shape 256 256`.
- Boolean Click options in this CLI are value-taking options, not flag toggles: use `--verbose True`, `--overwrite False`, `--patch-mode True`, or `--return-probabilities False`.

## WSI Utility Commands

- `slide-info`: `--img-input`, `--output-path`, `--file-types`, `--mode show|save`, `--verbose`. It reads WSI metadata and can save YAML metadata files.
- `slide-thumbnail`: `--img-input`, `--output-path`, `--file-types`, `--mode show|save`. It saves or displays slide thumbnails.
- `read-bounds`: `--img-input`, `--output-path`, `--region X0 Y0 X1 Y1`, `--resolution`, `--units`, `--mode show|save`. It reads a rectangular WSI region.
- `save-tiles`: `--img-input`, `--output-path`, `--file-types`, `--tile-objective-value`, `--tile-read-size H W`, `--tile-format`, `--verbose`. It exports WSI tiles.

## Preprocessing Commands

- `tissue-mask`: `--img-input`, `--output-path`, `--method Otsu|Morphological`, `--resolution`, `--units mpp|power`, `--mode show|save`, `--file-types`, `--kernel-size H W`. It generates tissue masks from slides or supported image files.
- `stain-norm`: `--img-input`, `--target-input`, `--output-path`, `--file-types`, `--method reinhard|custom|ruifrok|macenko|vahadane`, `--stain-matrix`. It normalizes image stains using a target image or custom stain matrix.

## Model Inference Commands

The model-oriented commands share a large option surface. Representative shared flags include:

- Inputs and outputs: `--img-input`, `--output-path`, `--output-file`, `--file-types`, `--masks`, `--output-type zarr|AnnotationStore`.
- Model selection: `--model`, `--weights`, `--yaml-config-path`.
- Resolution and class metadata: `--input-resolutions`, `--output-resolutions`, `--class-dict`.
- Runtime: `--device cpu|cuda|mps`, `--batch-size`, `--num-workers`, `--memory-threshold`, `--verbose`, `--overwrite`.
- Patch/WSI behavior: `--patch-mode`, `--patch-input-shape H W`, `--patch-output-shape H W`, `--stride-shape H W`, `--scale-factor Y X`, `--auto-get-mask`, `--return-probabilities`.

Command-specific notes:

- `patch-predictor` defaults to a patch classification model and `AnnotationStore` output.
- `deep-feature-extractor` is similar to patch prediction but defaults to feature extraction and `zarr` output.
- `semantic-segmentor` adds `--output-resolutions` and segmentation-oriented output.
- `nucleus-instance-segment` and `multitask-segmentor` support `--return-predictions`, a comma-separated boolean list such as `true,false`.
- `nucleus-detector` adds detection post-processing controls: `--min_distance`, `--threshold_abs`, `--threshold_rel`, and `--postproc_tile_shape H W`.

For model semantics, valid pretrained model names, output schemas, masks, and performance choices, route to `model-inference` rather than expanding full model tables here.

## Visualization Commands

- `visualize`: accepts either `--base-path` containing expected slide/overlay subdirectories, or both `--slides` and `--overlays`; also accepts `--port` and `--noshow`. It starts a tile server plus Bokeh server.
- `show-wsi`: accepts repeated `--img-input` and optional repeated `--name`; it also supports `--colour-by`/`--colour-map` for annotation-rendered layers. If names are provided, the number of names must match the number of images.

Route layer semantics, annotation coloring, and browser/server behavior to `annotation-visualization`.

## Command Construction Checklist

1. Confirm the command exists with `tiatoolbox <command> --help`.
2. Use an argument list internally, for example `['tiatoolbox', 'semantic-segmentor', '--img-input', slide, ...]`.
3. Convert dictionaries/lists to compact JSON with double quotes before shell quoting.
4. Pass multi-token numeric options as separate tokens, not a single quoted string.
5. Ensure input paths exist and model output directories are new, unless `--overwrite True` is intentional and supported by that command.
6. Prefer `--mode save` and `--noshow` in automation to avoid GUI/browser side effects.
