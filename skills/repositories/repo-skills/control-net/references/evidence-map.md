# ControlNet Evidence Map

This reference summarizes the repository evidence used to build the runtime skill and how source artifacts were distilled into bundled references/scripts.

## Included Evidence

| Evidence source | Why it matters | Skill owner |
| --- | --- | --- |
| `README.md` | Install expectations, model list, Gradio app commands, guess mode, transfer discussion links, high-level architecture | Root, `gradio-inference-apps`, `model-and-weight-utilities` |
| `docs/annotator.md` | Detector UI list and color/channel cautions | `annotators-and-preprocessing` |
| `docs/train.md` | Fill50K layout, dataset code, add-control command, tutorial training loop | `training-and-datasets`, `model-and-weight-utilities` |
| `docs/faq.md` | Zero-convolution learning explanation | `model-and-weight-utilities` |
| `docs/low_vram.md` | `config.save_memory` guidance and caveat | Root, `gradio-inference-apps`, `training-and-datasets`, `model-and-weight-utilities` |
| `annotator/` | Utility image conversion/resizing and detector wrappers | `annotators-and-preprocessing` |
| `cldm/` and `ldm/` | ControlNet model classes, DDIM sampler, config instantiation, low-VRAM hooks | `model-and-weight-utilities`, `gradio-inference-apps` |
| `models/cldm_v15.yaml`, `models/cldm_v21.yaml` | SD1.5/SD2.1 config targets and key differences | `model-and-weight-utilities`, `training-and-datasets` |
| `gradio_*.py` | Inference/annotator UI parameters and unsafe top-level side effects | `gradio-inference-apps`, `annotators-and-preprocessing` |
| `tool_add_control.py`, `tool_add_control_sd21.py`, `tool_transfer_control.py` | Checkpoint initialization and transfer algorithms | `model-and-weight-utilities` |
| `tutorial_dataset.py`, `tutorial_dataset_test.py`, `tutorial_train.py`, `tutorial_train_sd21.py` | Dataset contract and training workflow | `training-and-datasets` |
| `test_imgs/` | Small sample-image evidence for safe preprocessing examples | `annotators-and-preprocessing`, verification artifacts |
| `environment.yaml` | Documented dependency family and Python/Torch expectations | Root troubleshooting |

## Excluded Or Static-Only Evidence

| Path or workflow | Decision | Reason |
| --- | --- | --- |
| `.git/`, `__pycache__/` | Exclude | VCS/cache internals |
| `skills/tests/` | Exclude from runtime skill | Review/test artifact area |
| `annotator/ckpts/` | Exclude assets | External detector checkpoint location; do not bundle weights |
| `github_page/` | Reference only | Static website images and PDF; not needed for runtime guidance |
| `font/` | Exclude | UI asset not central to workflows |
| Missing `training/fill50k/` and large model files | Document only | External downloads required |
| Gradio app launch | Static-only | Top-level scripts load checkpoints, move to CUDA, and launch servers |
| Tutorial training execution | Static-only | Requires data, checkpoints, GPU, and may download models/tokenizers |
| Checkpoint conversion execution | Dry-run only | Real conversion writes large output checkpoints and needs external inputs |

## Source Script Import Map

| Source artifact | Decision | Bundled replacement | Owner | Check |
| --- | --- | --- | --- | --- |
| `gradio_annotator.py` | Adapt static inspection | `sub-skills/annotators-and-preprocessing/scripts/inspect_annotator_inputs.py` | `annotators-and-preprocessing` | `--help`, `--self-check`, AST parse when checkout supplied |
| `annotator/util.py` | Adapt utility semantics | `sub-skills/annotators-and-preprocessing/scripts/inspect_annotator_inputs.py` | `annotators-and-preprocessing` | Tiny grayscale/RGB/RGBA conversion and 64-multiple resize checks |
| `gradio_*2image.py` | Adapt static inspection | `sub-skills/gradio-inference-apps/scripts/extract_gradio_signatures.py` | `gradio-inference-apps` | `--help`, AST signature extraction |
| `tutorial_dataset.py` | Adapt schema/range checks | `sub-skills/training-and-datasets/scripts/validate_fill50k_dataset.py` | `training-and-datasets` | `--help`, tiny fixture generation/validation |
| `tutorial_train.py`, `tutorial_train_sd21.py` | Reference-only | `sub-skills/training-and-datasets/references/training-workflows.md` | `training-and-datasets` | Static workflow extraction; execution skipped |
| `tool_add_control.py`, `tool_add_control_sd21.py` | Adapt dry-run mapping | `sub-skills/model-and-weight-utilities/scripts/inspect_weight_mapping.py` | `model-and-weight-utilities` | `--help`, `--self-test`, optional config dry-run |
| `tool_transfer_control.py` | Reference/adapt algorithm | `sub-skills/model-and-weight-utilities/references/weight-utilities.md` | `model-and-weight-utilities` | Static algorithm extraction; execution skipped |

## Native Ground-Truth Candidates

- Safe native/static candidates: root checkout/config check, annotator utility tiny-array check, Gradio AST signature extraction, Fill50K tiny fixture validator, model weight mapping self-test/config dry-run.
- Unsafe or skipped native candidates: Gradio server launches, detector model execution, tutorial training, real checkpoint conversion, full image generation, model/tokenizer downloads.

Verification artifacts produced during DisCo review record which candidates were selected, run, or skipped; this runtime skill only preserves the public evidence and source-script decisions.
