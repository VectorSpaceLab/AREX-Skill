# Boltz Package Overview

Boltz is a Python package for biomolecular interaction prediction. The inspected package version is `2.2.1`; the package imports as `boltz` and exposes the console script `boltz` with the command `boltz predict`.

## Main User Workflows

| Workflow | Entry point | Skill route | Notes |
| --- | --- | --- | --- |
| Structure prediction | `boltz predict INPUT` | `sub-skills/prediction/SKILL.md` | YAML is preferred; FASTA is deprecated but accepted. |
| Binding affinity prediction | `boltz predict affinity.yaml` with `properties: affinity` | `sub-skills/prediction/SKILL.md` | Affinity output has value and binary-probability heads with different meanings. |
| Raw data processing | CCD, clustering, MSA, RCSB/mmCIF stages | `sub-skills/data-preparation/SKILL.md` | External tools and large datasets are common; use dry-run checks first. |
| Training | Hydra/OmegaConf config plus official training launcher | `sub-skills/training/SKILL.md` | Full training is GPU/storage-heavy; start with static validation and debug mode. |
| Evaluation | Prediction JSON/CSV summaries or benchmark reproduction planning | `sub-skills/evaluation/SKILL.md` | Updated Boltz-2 evaluation assets are marked as coming soon in inspected docs. |

## Installed Facts

- Distribution: `boltz`
- Version from package metadata: `2.2.1`
- Python requirement: `>=3.10,<3.13`
- Console script: `boltz = boltz.main:cli`
- Public command: `boltz predict [OPTIONS] DATA`
- Important dependencies include PyTorch, PyTorch Lightning, Hydra, RDKit, NumPy, pandas, Biopython, SciPy, scikit-learn, Click, PyYAML, and wandb.
- Optional CUDA extra installs cuEquivariance-related packages; prediction can also use `--no_kernels` when optional kernels are incompatible.

## Public CLI Facts

`boltz predict` accepts a single input file or directory. It recognizes YAML and FASTA-style inputs for prediction; YAML is preferred. Key option groups include:

- Output/cache/checkpoint: `--out_dir`, `--cache`, `--checkpoint`, `--affinity_checkpoint`, `--override`.
- Runtime/backend: `--devices`, `--accelerator`, `--num_workers`, `--preprocessing-threads`, `--no_kernels`, `--seed`.
- Sampling/model: `--model`, `--recycling_steps`, `--sampling_steps`, `--diffusion_samples`, `--step_scale`, affinity-specific sampling flags.
- MSA server: `--use_msa_server`, `--msa_server_url`, `--msa_pairing_strategy`, basic auth flags, API-key header/value flags.
- Outputs: `--output_format`, `--write_full_pae`, `--write_full_pde`, `--write_embeddings`.

## Safety Model

Safe by default:

- Reading docs/configs.
- Running bundled helper scripts with `--help` or local fixtures.
- Running `boltz --help` and `boltz predict --help`.
- Validating YAML/FASTA/A3M/CSV shapes without launching models.

Ask or plan carefully before:

- Downloading model checkpoints, CCD/molecule archives, raw datasets, MSAs, or benchmark data.
- Calling an MSA server or using credentials.
- Running GPU inference, full training, or OpenStructure benchmark evaluation.
- Starting Redis, running `mmseqs`, processing full mmCIF/MSA corpora, or writing large output trees.
