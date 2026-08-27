# Tracker, Parameter, Model, and Training Catalog

## When to read

Read this when choosing tracker/parameter names, matching a paper display name to source modules, or selecting an LTR training setting. For execution details, route to the relevant sub-skill.

## Runtime tracker families

| Family/display name | Tracker module | Runtime parameter modules | Notes |
| --- | --- | --- | --- |
| ATOM | `atom` | `default`, `default_vot`, `multiscale_no_iounet`, `atom_prob_ml`, `atom_gmm_sampl` | `multiscale_no_iounet` is the CPU-oriented baseline; most other settings are network/checkpoint backed. |
| DiMP / PrDiMP / SuperDiMP | `dimp` | `dimp18`, `dimp18_vot18`, `dimp50`, `dimp50_vot18`, `dimp50_vot19`, `prdimp18`, `prdimp50`, `prdimp50_vot18`, `super_dimp` | VOT parameter files prioritize VOT reset protocol; non-VOT settings emphasize redetection/longer-term robustness. |
| SuperDiMPSimple | `dimp_simple` | `super_dimp_simple` | Used as a lightweight/base tracker in some KeepTrack workflows. |
| ECO / UPDT-style baseline | `eco` | `default`, `mobile3` | Includes DCF/Fourier/complex tensor utilities; implementation differs from original ECO. |
| KeepTrack | `keep_track` | `default`, `default_fast` | Handles distractor objects with target-candidate association; training may need generated target-candidate JSON. |
| KYS | `kys` | `default`, `default_vot` | Scene-aware tracking; optional spatial-correlation-sampler dependency is documented for KYS. |
| LWL | `lwl` | `lwl_ytvos`, `lwl_boxinit` | Video object segmentation tracker; box-initialized and YouTubeVOS variants. |
| RTS | `rts` | `rts50` | Segmentation-centric robust tracking; can require pregenerated masks and LWL/STA weights for training. |
| TaMOs | `tamos` | `tamos_resnet50`, `tamos_swin_base` | Multi-object generic tracking baseline for LaGOT-style tasks. |
| ToMP | `tomp` | `tomp50`, `tomp101` | Transformer-based model prediction tracker with ResNet backbones. |

Use module names in commands and code. Display names such as `DiMP-50`, `SuperDimp`, or `TaMOs-SwinBase` are not import names.

## Model zoo context

The model zoo documents pretrained model links and benchmark results for ATOM, DiMP-18/50, PrDiMP, SuperDiMP, KYS, KeepTrack, ToMP-50/101, RTS, TaMOs-50/SwinBase, and VOS models such as LWL/RTS. It also documents raw result archives and benchmark protocols.

Operational guidance:

- Treat all model/result downloads as network side effects requiring user approval.
- Save tracker checkpoints under the `network_path` configured in `pytracking/evaluation/local.py`.
- The parameter module, not the display name alone, determines which checkpoint file is expected.
- Reported benchmark numbers are context, not local verification; reproduce only with the matching dataset, checkpoint, protocol, and run count.

## LTR training setting modules

| Training module | Setting files |
| --- | --- |
| `bbreg` | `atom`, `atom_gmm_sampl`, `atom_paper`, `atom_prob_ml` |
| `dimp` | `dimp18`, `dimp50`, `prdimp18`, `prdimp50`, `super_dimp`, `super_dimp_simple` |
| `keep_track` | `keep_track` |
| `kys` | `kys` |
| `lwl` | `lwl_boxinit`, `lwl_stage1`, `lwl_stage2` |
| `rts` | `rts50` |
| `tamos` | `tamos_resnet50`, `tamos_swin_base` |
| `tomp` | `tomp101`, `tomp50` |

Training command shape:

```bash
python ltr/run_training.py <train_module> <train_name>
```

Use `sub-skills/ltr-training/scripts/build_training_command.py` to validate module/name pairs and print a safe command before launching training.

## Common tracker-to-training relationships

- ATOM runtime parameters are trained from `bbreg` settings.
- DiMP/PrDiMP/SuperDiMP runtime parameters map to `dimp` training settings.
- KeepTrack training depends on a base tracker and target-candidate data; route data-generation planning through `analysis-and-packaging` and training through `ltr-training`.
- LWL and RTS involve VOS/segmentation weights, masks, and dataset-specific settings.
- TaMOs and ToMP use modern tracking model settings with ResNet/Swin/Transformer components.

## Selection heuristics

- For a quick runtime smoke or command-building task, start with `atom/default` or `dimp/dimp50` only if the checkpoint is present; otherwise use command-only validation.
- For CPU-only mechanics, ATOM `multiscale_no_iounet` can exercise a limited baseline, but do not generalize that to network-backed tracker performance.
- For VOT protocol tasks, prefer parameter files with `_vot` names where available and route VOT setup to `analysis-and-packaging`.
- For segmentation/VOS tasks, use LWL or RTS routes and verify `segmentation_path`, masks, and dataset-specific configuration.
- For multi-object generic tracking, use TaMOs/LaGOT routes and confirm target initialization/object-id expectations.
