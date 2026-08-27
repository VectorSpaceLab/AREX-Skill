# SaProt Setup and Dependencies

## Purpose

Read this before choosing an environment strategy for SaProt tasks. SaProt can be used at several levels: static config/data checks, structure conversion with Foldseek, local model inference, or full PyTorch Lightning training/evaluation.

## Dependency Tiers

| Tier | Needed for | Typical packages/tools |
| --- | --- | --- |
| Static diagnostics | YAML inspection, path checks, JSONL validation, ClinVar AUC aggregation | Python 3.10+, optional `pyyaml`, optional `lmdb` for real LMDB checks |
| Structure conversion | PDB/mmCIF to AA/3Di/combined sequence | Foldseek executable, `biopython`, `numpy` |
| Model inference | tokenizer/model loading, embeddings, mutation scoring, inverse folding | `torch`, `transformers`, local SaProt model directory; `fair-esm` for `.pt` loading; `peft` for LoRA |
| Training/evaluation | pretraining, fine-tuning, ProteinGym/ClinVar sweeps | repo requirements stack: PyTorch, PyTorch Lightning, TorchMetrics, Transformers, EasyDict, WandB, LMDB, Pandas, SciPy, Fair-ESM, compatible CUDA/GPU when selected |

Start with the smallest tier that answers the user’s task. Do not install the full training stack just to inspect a YAML file or validate local paths.

## Public Install Pattern

The repository documents a Python 3.10 environment and a requirements file. For full training/evaluation work, create an isolated environment and install the project requirements there. For lightweight skill helper scripts, install only the dependencies named by the helper error messages.

Minimal static helpers are intentionally safe:

```bash
python scripts/check_sa_prot_environment.py --check-python-imports
python sub-skills/training-evaluation/scripts/saprot_config_check.py -c <config.yaml>
python sub-skills/training-evaluation/scripts/compute_clinvar_auc.py --help
```

Structure conversion helpers require Foldseek plus scientific parsing packages:

```bash
python sub-skills/structure-sequences/scripts/convert_structure_sequence.py --help
```

Model helpers require user-provided local model assets:

```bash
python sub-skills/model-inference/scripts/check_model_assets.py <local-model-dir>
```

## Required Local Assets

SaProt workflows often need assets that are too large or machine-specific to bundle in a skill:

- Foldseek executable for PDB/mmCIF to 3Di conversion and Foldseek-aware mutation configs.
- Local Hugging Face SaProt model directories for `EsmTokenizer`, `EsmForMaskedLM`, and repository model wrappers.
- Local `.pt` checkpoint files only for `utils.esm_loader.load_esm_saprot` style loading.
- LMDB train/valid/test directories for supervised tasks.
- Benchmark directories for ProteinGym or ClinVar zero-shot sweeps.
- Optional GPU/CUDA runtime for practical large-model inference and training.

Validate these assets before writing code that assumes they exist.

## Path Conventions

The original SaProt examples commonly use these relative layouts:

- `bin/foldseek` for the Foldseek binary.
- `weights/PLMs/<model-name>` for Hugging Face model/tokenizer directories.
- `weights/<Task>/<checkpoint>.pt` for task checkpoints.
- `LMDB/<Task>/<normal-or-foldseek>/<split>` for dataset splits.
- `output/<Task>/...` for generated benchmark outputs and logs.

Treat these as conventions inside the user’s active project, not as paths guaranteed by the skill.

## Safe Environment Check

Run the root checker when the user supplies assets:

```bash
python scripts/check_sa_prot_environment.py \
  --check-python-imports \
  --model-dir <local-model-dir> \
  --foldseek <foldseek>
```

The checker reports optional dependency availability, local model directory shape, Foldseek executability, and visible CUDA facts without downloading weights or running training.

## Full Training Cautions

Full training/evaluation can be expensive because configs may request multiple GPUs, fp16 precision, many dataloader workers, WandB logging, and large model/dataset assets. Before execution:

1. Copy the YAML config into the active project.
2. Validate paths and launch risk with the bundled config checkers.
3. Reduce `Trainer.devices`, `dataset.dataloader_kwargs.num_workers`, precision, batch size, and batch limits for a smoke run.
4. Disable WandB unless the user explicitly wants external logging.
5. Ask for confirmation before multi-GPU, multi-node, full benchmark, or checkpoint-overwriting runs.
