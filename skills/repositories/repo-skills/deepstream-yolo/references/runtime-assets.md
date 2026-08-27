# Bundled runtime assets

This skill ships the concrete parser, build, config, and layout assets needed to execute the supported DeepStream-Yolo workflows without reopening the original repository checkout.

## Asset tree

| Asset path | Purpose |
| --- | --- |
| `assets/nvdsinfer_custom_impl_Yolo/` | Bundled custom parser / engine builder source and Makefile for DeepStream builds |
| `assets/configs/` | Bundled DeepStream app config, infer config templates, and label files |
| `assets/images/multipleGIEs_tree.png` | Layout illustration for the multi-GIE folder structure |

## How the helpers use it

- `scripts/stage-runtime-tree.sh` copies the bundled assets into a fresh runtime directory without building.
- `scripts/build-nvdsinfer-plugin.sh` stages `assets/nvdsinfer_custom_impl_Yolo/` and the config templates into a fresh runtime directory before building the shared library.
- `sub-skills/multi-gie/scripts/setup-multi-gie-tree.sh` uses the same bundled assets to scaffold `gie1/`, `gie2/`, ... folders.
- The deployment and INT8 workflows can read the staged configs directly from the runtime directory created by the build helper.

## Practical rule

If you need to run, stage, or copy the parser/build/config files, use the bundled `assets/` tree or a runtime directory created from it. Do not depend on the original checkout path.
