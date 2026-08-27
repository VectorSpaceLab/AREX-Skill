# Donut Workflow Map

Use this map before choosing a sub-skill or bundled script. It distills the repository's public workflows into runtime-owned entry points.

## Capability ownership

| Capability | Owner | Bundled entry points | Notes |
| --- | --- | --- | --- |
| Single-image checkpoint inference | Inference | `sub-skills/inference/SKILL.md`, `sub-skills/inference/scripts/run_inference.py` | Supports local or Hub checkpoints, task prompts, DocVQA questions, CPU/CUDA selection, and JSON/raw-token output. |
| Gradio demo | Inference | `sub-skills/inference/scripts/launch_demo.py` | Replaces the source demo launcher with a skill-owned wrapper for modern Gradio. |
| Prompt and JSON token debugging | Inference + root API | `sub-skills/inference/references/demo-and-prediction.md`, `references/api-reference.md` | Use when a generated token string cannot be parsed or the task token is mismatched. |
| Dataset JSONL validation | Training | `sub-skills/training/scripts/check_training_config.py`, `sub-skills/training/scripts/evaluate_dataset.py --validate_only` | Checks `file_name`, JSON-encoded `ground_truth`, `gt_parse`, `gt_parses`, and missing image files. |
| Fine-tuning config review and launch | Training | `sub-skills/training/references/configuration.md`, `sub-skills/training/scripts/check_training_config.py`, `sub-skills/training/scripts/train_donut.py` | Covers CORD, DocVQA, RVL-CDIP, and TrainTicket-style configs. |
| Checkpoint evaluation | Training | `sub-skills/training/scripts/evaluate_dataset.py` | Mirrors the source test workflow without depending on the original `test.py`. |
| Synthetic document generation | SynthDoG | `sub-skills/synthdog/SKILL.md`, `sub-skills/synthdog/scripts/render_config.py`, `sub-skills/synthdog/scripts/template.py` | Uses external background, paper, corpus, and font resources; large assets are not bundled. |
| Environment/API smoke check | Root | `scripts/runtime_smoke.py` | Verifies imports, signatures, token round-trip, optional CUDA, and optional SynthDoG dependencies. |

## Decide by user wording

- **"Run Donut on this receipt/image/document"** → inference.
- **"Which prompt should I use for DocVQA/CORD/RVL-CDIP?"** → inference, then root API for prompt output details.
- **"Fine-tune/train/resume/evaluate a Donut model"** → training.
- **"My metadata.jsonl fails / gt_parse vs gt_parses"** → training.
- **"Generate synthetic documents / SynthDoG resources/fonts/corpus"** → synthdog.
- **"Install or import error"** → root troubleshooting first, then the nearest workflow troubleshooting file.
- **"Is CUDA needed?"** → training if the user is training; inference if predicting; root smoke for environment probing.

## Source-script import map

| Source surface | Runtime treatment | Reason |
| --- | --- | --- |
| `app.py` | Wrapped by `sub-skills/inference/scripts/launch_demo.py` | Future agents need a self-contained Gradio launcher and current package imports. |
| Direct `DonutModel.inference` examples | Wrapped by `sub-skills/inference/scripts/run_inference.py` | Single-image use is common and should not require source checkout scripts. |
| `train.py` | Copied/adapted as `sub-skills/training/scripts/train_donut.py` | Training is core to the repo and should be runnable without the original checkout. |
| `test.py` | Adapted by `sub-skills/training/scripts/evaluate_dataset.py` | Evaluation and validation are useful as reusable runtime helpers. |
| `lightning_module.py` | Copied/adapted as `sub-skills/training/scripts/lightning_module.py` | The bundled trainer needs the Lightning module/data-module implementation. |
| `config/train_*.yaml` | Copied into `sub-skills/training/references/configs/` and distilled into configuration tables | Examples are useful for training launch and validation without the original checkout. |
| `synthdog/template.py` and helper modules | Copied/adapted into `sub-skills/synthdog/scripts/` | SynthDoG needs the template, elements, and layouts at runtime. |
| `synthdog/resources/*` | Reference-only external-resource contract | Large and user-specific assets would bloat the skill tree. |
| `dataset/`, `result/`, `.git/`, generated review artifacts | Excluded | Data/results/VCS/review files are not public runtime skill content. |

## Backend expectations

- **Inference:** CPU is acceptable for small smoke checks and local debugging; CUDA is preferred for realistic checkpoint latency. CPU fallback is partial because model size can make it slow.
- **Training:** CUDA is required by the original training script design (`gpus`, DDP, 16-bit behavior). Do not present CPU as equivalent training support.
- **Evaluation:** CUDA is preferred for real checkpoint evaluation; validation-only mode is CPU-safe.
- **SynthDoG:** CPU generation is acceptable, but it needs image/text dependencies and external resources.

## Integrated difficult cases to consider during verification

1. **Synthetic-to-training routing:** render a tiny SynthDoG config with external resources, explain the generated `metadata.jsonl`, then validate that dataset shape with the training helper.
2. **Prompt/config mismatch:** a user provides DocVQA-style `gt_parses` but asks for a CORD prompt; route through training data validation and inference prompt rules to explain the mismatch.
