# Capability Map

## Purpose

Use this map to choose the right sub-skill and to understand what was verified, what is dry-run only, and what remains blocked by external data/checkpoints or legacy CUDA/TensorFlow constraints.

| Capability | Kind | Evidence | Owner | Runtime assets | Verification expectation |
| --- | --- | --- | --- | --- | --- |
| Legacy install and dependency triage | support workflow | README prerequisites, Dockerfiles, `lib/setup.py`, env report | `installation-and-configuration` | `scripts/check_environment.py`, install/config/troubleshooting refs | Help/checker smoke; full native build only on compatible CUDA/NVCC host |
| Config presets and overrides | support workflow | `lib/model/config.py`, `experiments/cfgs/*.yml`, CLI `--set` use | `installation-and-configuration` | `references/configuration.md` | Source/CPU config facts verified; user-specific overrides require exact-type checks |
| VOC/COCO data layout and registry keys | support workflow | `datasets/factory.py`, `pascal_voc.py`, `coco.py`, `README.md` | `dataset-and-assets` | `scripts/validate_layout.py`, data-layout reference | Path/name validation; full dataset parsing requires supplied datasets |
| Pretrained and ImageNet checkpoint assets | support workflow | README model setup, demo mappings, train/test scripts | `dataset-and-assets` | model-artifacts reference, layout validator | Path/sidecar validation; no downloads performed |
| Demo inference | primary workflow | `tools/demo.py`, `model/test.py`, README demo section | `inference-and-demo` | `scripts/demo_command_builder.py`, demo/NMS refs | Dry-run command and checkpoint validation; full inference requires checkpoint and native runtime |
| Training and validation | primary workflow | `train_faster_rcnn.sh`, `trainval_net.py`, `train_val.py`, README | `training-and-evaluation` | command builder, training/eval and CLI refs | Dry-run only by default; real run is expensive and data/checkpoint/backend dependent |
| Testing/evaluation/reval | primary workflow | `test_faster_rcnn.sh`, `test_net.py`, `reval.py`, dataset evaluators | `training-and-evaluation` | command builder and references | Dry-run or reval planning; native AP requires datasets/detections/checkpoints |
| Deprecated VGG16 conversion | support workflow | `convert_vgg16.sh`, `convert_from_depre.py` | `training-and-evaluation` | command builder and CLI/troubleshooting refs | Dry-run/reference only; real conversion requires old checkpoint files and TF1 reader |
| Architecture/API modification | maintainer/research workflow | `lib/nets`, `lib/layer_utils`, `lib/model`, `lib/roi_data_layer`, `lib/utils` | `api-and-architecture` | `scripts/inspect_source_api.py`, API/architecture refs | AST/source inspector; graph execution unverified |

## Verification limits to preserve

- Full CUDA/native build was not verified: `nvcc` was unavailable in the production environment and `lib/setup.py` fails before metadata without it.
- TensorFlow 1.15 CPU import was used only as an inspection substitute for the repository's TensorFlow r1.x code style.
- No VOC/COCO datasets, COCO API source checkout, pretrained model archive, ImageNet weights, or trained checkpoint was downloaded or executed.
- The generated helpers are intentionally read-only or dry-run by default.

## Integrated difficult cases selected for final verification

1. **Cross-skill setup-to-demo diagnosis:** A user wants the ResNet101 VOC07+12 demo but has no checkpoint and no compiled NMS modules. The expected answer routes through installation checks, dataset/model-artifact validation, and demo command construction while refusing to claim runnable inference.
2. **Training command with stale assets:** A user asks for a VOC07+12 ResNet101 test command with `TEST.MODE top` and a custom tag. The expected answer uses the training command builder, validates tag/checkpoint path implications, and warns about data/checkpoint/native-backend prerequisites.
