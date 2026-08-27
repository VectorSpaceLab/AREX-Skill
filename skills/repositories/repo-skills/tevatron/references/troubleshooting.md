# Tevatron Troubleshooting

Use this root reference for cross-cutting problems before changing dependencies, backend packages, data files, or launcher commands. For workflow-specific symptoms, continue to the nearest sub-skill troubleshooting file.

## First Checks

Run these before expensive training, encoding, search, reranking, or multimodal jobs:

```bash
python scripts/check_tevatron_environment.py --json
python scripts/check_tevatron_environment.py --require search
python scripts/check_tevatron_environment.py --require lora
```

Interpret the output by workflow:

- Base Tevatron import should report `tevatron`, `transformers`, and `datasets` as available.
- Search workflows need `numpy` and `faiss`.
- PyTorch training/encoding/reranking need `torch`.
- LoRA workflows need `torch` and `peft`.
- DeepSpeed workflows need `torch` and `deepspeed`.
- Multimodal workflows usually need `torch`, `Pillow`, model processors, and sometimes Qwen utility packages.
- vLLM routes need `torch` and `vllm` with compatible GPU/runtime support.
- JAX/TPU routes need `jax`, `flax`, and `optax`, plus any route-specific Tevax/Magix dependencies.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: tevatron` | Package not installed in the active environment | Install the package or editable checkout, then rerun the base import check. |
| `ModuleNotFoundError: torch` | Base package metadata does not install PyTorch | Install a PyTorch wheel compatible with the selected CPU/CUDA/ROCm/MPS backend before running model drivers. |
| `ModuleNotFoundError: faiss` | Search dependencies are optional | Install `faiss-cpu` for CPU checks or a compatible GPU FAISS stack for GPU retrieval. |
| `ModuleNotFoundError: peft` | LoRA workflow selected without LoRA dependency | Install `peft` and confirm the selected model supports the requested LoRA target modules. |
| `ModuleNotFoundError: deepspeed` | DeepSpeed launcher/config selected without dependency | Install DeepSpeed only for training routes that actually use ZeRO or DeepSpeed launchers. |
| `ModuleNotFoundError: qwen_omni_utils` | Qwen-Omni multimodal route selected | Install the Qwen utility package and verify processor/model compatibility. |
| `ModuleNotFoundError: vllm` | vLLM encode route selected | Install `vllm` only after confirming GPU, CUDA, model, and LoRA support. |
| JAX/Flax/Optax import failures | Optional TPU/JAX route selected | Install the JAX stack appropriate for CPU/GPU/TPU, then use the JAX-specific sub-skill guidance. |

Do not install every optional stack at once. Tevatron supports multiple backends and model families; installing all of them can trigger large downloads, CUDA ABI conflicts, or long builds.

## Version and Backend Mismatch

- Tevatron examples often combine Hugging Face Transformers, PyTorch, LoRA, DeepSpeed, FlashAttention, FAISS, vLLM, JAX, or Qwen processors. These packages have independent compatibility constraints.
- If `torch.cuda.is_available()` is false on a GPU machine, check whether the installed PyTorch wheel is CPU-only, the container exposes GPUs, and the driver supports the wheel's CUDA runtime.
- FlashAttention is optional but many LLM examples default to `flash_attention_2`; switch `--attn_implementation eager` or `sdpa` when FlashAttention is unavailable and the selected model supports the fallback.
- FAISS CPU is sufficient for tiny smoke checks and small examples; FAISS GPU requires matching CUDA libraries and may not be provided by `faiss-cpu`.
- vLLM model support is stricter than normal Transformers loading. Confirm the model architecture, LoRA adapter support, tensor parallel settings, and available GPU memory before using vLLM drivers.

## Data and Path Problems

Start with `sub-skills/data-preparation/` whenever a command fails before model loading or reports missing IDs/text/assets.

Common root causes:

- Local JSONL passed without `--dataset_name json`.
- `--dataset_path`, `--corpus_path`, or `--encode_in_path` points to the wrong record kind.
- Training records use document IDs but the corpus file is missing those IDs.
- Query/corpus IDs are duplicated or blank.
- Multimodal rows reference image/audio/video assets but `--assets_path` is missing or relative paths are resolved from an unexpected directory.
- Rerank input contains a first-stage run file instead of pairwise JSONL.

Use the bundled validators/converters in `sub-skills/data-preparation/scripts/` and `sub-skills/reranking/scripts/` with tiny fixtures before launching expensive jobs.

## Command and CLI Misuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training command exits without training | `--do_train` omitted or inherited Hugging Face arguments not set | Use `sub-skills/training/scripts/build_training_command.py` to generate a command plan and confirm `--do_train`. |
| Checkpoint overwrite or resume confusion | `--output_dir`, `--overwrite_output_dir`, and last-checkpoint behavior conflict | Decide whether to resume or overwrite before launching; keep output directories separate for experiments. |
| Search finds no passage files | Shell glob not quoted or pattern matches zero files | Quote `--passage_reps 'corpus*.pkl'` and check files exist before running search. |
| Search output is pickle when text expected | `--save_text` omitted | Add `--save_text` for `qid<TAB>docid<TAB>score` output. |
| Reranker scores look grouped incorrectly | `train_group_size`, positives/negatives, or inference input format is inconsistent | Read `sub-skills/reranking/references/arguments-reference.md` and rebuild pairwise input. |
| Multimodal model fails at processor/collator step | Media fields, processor, or model family does not match the driver | Read `sub-skills/multimodal-llm/references/multimodal-workflows.md` and check optional dependencies. |

## Safe Validation Strategy

1. Validate local data with a bundled script.
2. Generate or inspect command strings without running long jobs.
3. Run minimal import and dependency checks.
4. Use tiny FAISS or conversion fixtures for deterministic local behavior.
5. Only then launch model downloads, GPU training, JAX/TPU jobs, vLLM encoding, or benchmark evaluation.

## When to Switch Sub-Skills

- Data/schema/ranking conversion problem: `sub-skills/data-preparation/references/troubleshooting.md`.
- Training command/dependency/memory problem: `sub-skills/training/references/troubleshooting.md`.
- Encoding/search/FAISS/evaluation problem: `sub-skills/encoding-retrieval/references/troubleshooting.md`.
- Reranker grouped loss/input/score problem: `sub-skills/reranking/references/troubleshooting.md`.
- Multimodal/LLM/Qwen/vLLM/asset problem: `sub-skills/multimodal-llm/references/troubleshooting.md`.
