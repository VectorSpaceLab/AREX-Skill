# VLA-Adapter Package Overview (external native checkout)

Read this to orient a future agent before choosing a sub-skill. It summarizes
the separately provisioned native checkout's package/workflow surfaces and
which operations require extra hardware, data, or services. The generated
skill itself contains only builders, validators, and documentation; it does
not bundle the native runtime.

VLA-Adapter is an official implementation of a tiny-scale
vision-language-action policy built around a Prismatic VLM backbone using
Qwen2.5-0.5B, DINO/SigLIP vision features, optional proprioception, LoRA or
frozen fine-tuning, and continuous action heads. The repo contains:

- Native `prismatic`: importable package for model configs, loaders, VLA
  constants, action tokenization, projectors/action heads, training utilities,
  and HF `Auto*` classes.
- Native VLA training/evaluation entry points for LoRA/proprio/Pro workflows.
- Native LIBERO and CALVIN benchmark evaluation logic.
- Native ALOHA real-world training/deployment/evaluation instructions and
  clients.
- Native FastAPI action servers using JSON or MsgPack payloads.
- Native checkpoint conversion and LoRA-merge utilities for
  Prismatic/OpenVLA layouts.

These are layout/API facts only. This adapter does not implement `load`,
`load_vla`, action heads, projectors, server/client logic, or conversions.
## Dependency classes


| Class | Needed for | Notes |
| --- | --- | --- |
| Base package dependencies | Importing `prismatic`, dataclasses, local API inspection | Python 3.10 is the documented environment; repo metadata allows `>=3.8`. |
| PyTorch CUDA | Real training, model action prediction, benchmark rollouts, serving | CPU import checks are not proof that action generation works. |
| TensorFlow / TFDS / dlimp | RLDS data loading for fine-tuning | Keep protobuf/TensorFlow/TFDS versions compatible. |
| FlashAttention 2 | Training acceleration | Documented as installed after editable install; treat failures as optional unless the user requires maximum throughput. |
| LIBERO / robosuite / MuJoCo stack | LIBERO rollouts | Also needs datasets, initial states, and EGL/Mesa libraries on many machines. |
| CALVIN stack | CALVIN ABC→D rollouts | Requires external CALVIN repo/dataset and `CALVIN_ROOT`. |
| ROS / cv_bridge / Cobot Magic hardware | Real ALOHA client | Never run real robot commands without operator/hardware confirmation. |
| Hugging Face access | Downloading backbones/checkpoints | Public VLA-Adapter checkpoints exist, but gated upstream LLMs or private mirrors may require tokens. |

## Model and checkpoint surfaces

- Public VLA-Adapter checkpoints cover LIBERO Spatial, Object, Goal, Long and
  their Pro variants, plus CALVIN-ABC-Pro.
- The local VLM backbone path commonly points to a Prismatic Qwen2.5 +
  DINO/SigLIP model directory.
- A VLA checkpoint used for evaluation or serving should contain compatible
  model config code, tokenizer/processor assets, and normalization statistics;
  `dataset_statistics.json` is essential for action unnormalization when using
  native VLA checkpoints.
- `unnorm_key` must match the dataset statistics key. LIBERO scripts often map
  `libero_spatial` to `libero_spatial_no_noops` when that key is present.

## Important package facts verified from installation

- Distribution: `vla-adapter`, version `0.0.1`.
- Import package: `prismatic`.
- `prismatic.load(model_id_or_path, hf_token=None, cache_dir=None,
  load_for_training=False, image_sequence_len=None)` loads a Prismatic VLM.
- `prismatic.models.load.load_vla(model_id_or_path, hf_token=None,
  cache_dir=None, load_for_training=False, step_to_load=None,
  model_type="pretrained", image_sequence_len=None)` loads an OpenVLA-style VLA.
- Robot constants are selected from command-line text: LIBERO and CALVIN use
  action dimension 7, proprio dimension 8, and 8-action chunks; ALOHA uses
  action/proprio dimension 14 and 25-action chunks.

## Skill map

- Installation/data/checkpoints: `sub-skills/setup-and-data/`.
- Fine-tuning: `sub-skills/training/`.
- Benchmark evaluation: `sub-skills/evaluation/`.
- Serving and ALOHA deployment: `sub-skills/deployment/`.
- Package APIs and checkpoint conversion: `sub-skills/package-apis/`.
