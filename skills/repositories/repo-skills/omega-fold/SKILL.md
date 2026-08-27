---
name: omega-fold
description: "Use OmegaFold for protein structure prediction from FASTA to PDB,
  including CLI inference, FASTA/PDB handling, and Python model API inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OmegaFold

Use this repo skill when a task involves OmegaFold, de novo protein structure prediction from amino-acid FASTA input, OmegaFold PDB outputs, the `omegafold` CLI, or the Python APIs `omegafold.make_config`, `omegafold.OmegaFold`, and `omegafold.pipeline`.

OmegaFold is release inference code. It is not a training, fine-tuning, dataset-building, model-serving, or general PDB-editing toolkit.

## Start Here

1. For command-line prediction from FASTA to PDB, read [inference-cli](sub-skills/inference-cli/SKILL.md).
2. For FASTA validation, pseudo-MSA tensors, PDB output names, and confidence/B-factor interpretation, read [data-and-outputs](sub-skills/data-and-outputs/SKILL.md).
3. For programmatic model construction, configs, forward inputs/outputs, and API debugging, read [model-api](sub-skills/model-api/SKILL.md).
4. For installation, dependency, Python, Torch, CUDA/MPS, and smoke-check guidance shared across routes, read [install and environment](references/install-and-environment.md).
5. For cross-cutting failures, read [root troubleshooting](references/troubleshooting.md), then route to the nearest sub-skill troubleshooting file.

## Route by Task

| User task | Read |
| --- | --- |
| Build or validate an `omegafold INPUT_FILE.fasta OUTPUT_DIRECTORY` command | [sub-skills/inference-cli/SKILL.md](sub-skills/inference-cli/SKILL.md) |
| Decide `--model`, `--device`, `--weights_file`, `--subbatch_size`, or `--num_cycle` | [sub-skills/inference-cli/references/inference-workflow.md](sub-skills/inference-cli/references/inference-workflow.md) |
| Check whether the CLI is installed without downloading weights | [sub-skills/inference-cli/scripts/omegafold_cli_smoke.py](sub-skills/inference-cli/scripts/omegafold_cli_smoke.py) |
| Explain accepted FASTA syntax, ambiguous residues, sequence sorting, or output PDB names | [sub-skills/data-and-outputs/references/data-formats.md](sub-skills/data-and-outputs/references/data-formats.md) |
| Exercise `pipeline.fasta2inputs` or `pipeline.save_pdb` safely | [sub-skills/data-and-outputs/scripts/inspect_fasta_pipeline.py](sub-skills/data-and-outputs/scripts/inspect_fasta_pipeline.py) |
| Instantiate `OmegaFold`, call `make_config`, load weights, or inspect `forward` | [sub-skills/model-api/references/api-reference.md](sub-skills/model-api/references/api-reference.md) |
| Inspect API signatures/configs without loading checkpoints | [sub-skills/model-api/scripts/inspect_model_api.py](sub-skills/model-api/scripts/inspect_model_api.py) |
| Diagnose install/import/backend issues before choosing a route | [references/install-and-environment.md](references/install-and-environment.md) and [references/troubleshooting.md](references/troubleshooting.md) |

## Minimal Install Expectations

OmegaFold distribution metadata is `OmegaFold` and the import module is `omegafold`. The package exposes the console script `omegafold=omegafold.__main__:main`.

For legacy-compatible installations, prefer Python 3.8, 3.9, or 3.10 with Biopython and a Torch build compatible with the target accelerator. The release requirements pin `torch==1.12.0+cu113`; when using that stack, keep `numpy<2` to avoid NumPy ABI warnings or import/runtime failures.

Safe import check:

```bash
python - <<'PY'
import omegafold
print(omegafold.make_config(1).struct_embedder)
print(omegafold.make_config(2).struct_embedder)
PY
```

Safe CLI check:

```bash
omegafold --help
```

Use the bundled [scripts/check_omega_fold_environment.py](scripts/check_omega_fold_environment.py) when you need a single no-download environment report before choosing a sub-skill.

## Safety Rules

- `omegafold --help`, bundled helper scripts, and API signature inspection are safe no-download checks.
- Full `omegafold INPUT_FILE.fasta OUTPUT_DIRECTORY` inference may download model weights, allocate a large model, use GPU/MPS/CPU resources, and take substantial time.
- Do not run full inference unless the user accepts downloads/runtime or provides a local checkpoint through `--weights_file`.
- Do not assume FASTA file order equals output order; OmegaFold sorts records by sequence length before processing.
- Do not interpret OmegaFold PDB B-factors as experimental crystallographic B-factors; the CLI writes per-residue confidence multiplied by `100` into the B-factor field.
- Do not present random no-weight outputs as meaningful predictions; load the matching model 1 or model 2 checkpoint before inference.

## Repository Facts

- Primary workflow: de novo structure prediction from one or more FASTA sequences to one PDB per sequence.
- Public CLI: `omegafold INPUT_FILE.fasta OUTPUT_DIRECTORY [options]`.
- Public Python entry points: `omegafold.make_config`, `omegafold.OmegaFold`, `omegafold.pipeline.fasta2inputs`, `omegafold.pipeline.save_pdb`.
- Model ids: `1` and `2` only.
- Device auto-selection: CUDA, then MPS, then CPU.
- Provenance and staleness baseline: [references/repo-provenance.md](references/repo-provenance.md).
