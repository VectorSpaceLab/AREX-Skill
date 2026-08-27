# Integrated coverage notes

## Included capabilities

| Capability | Owner | Evidence | Verification posture |
|---|---|---|---|
| Legacy environment and extension setup | `setup-and-operations` | README, INSTALL, Makefile, Cython setup | CPU diagnostics possible; required CUDA blocked |
| COCO/VOC/CrowdHuman/JSON roidb preparation | `data-preparation` | DATASET, FINETUNE, conversion utilities | tiny schema checks; full datasets deferred |
| Training, bbox/mask evaluation, speed benchmark | `detection-workflows` | root entry scripts, configs, docs | long-running native GPU cases deferred |
| Detector/component/model-family customization | `model-customization` | FRAMEWOKR_OVERVIEW, annotated config, builders | source/config inspection; runtime symbols require mxnext/CUDA |

## Deliberate omissions

- Dataset archives, pretrained weights, benchmark runs, and generated experiment
  output are not runtime skill content.
- Cluster launch helpers are reference-only because they include private paths,
  SSH assumptions, `pkill`, Singularity, and external launcher dependencies.
- The CUDA `gpu_nms` extension is documented as optional/required only for
  paths that select it; `nvcc` was not available during production.
- The inspection environment report is `failed` for the required CUDA backend.
  No import or auto-import claim changes that fact.
