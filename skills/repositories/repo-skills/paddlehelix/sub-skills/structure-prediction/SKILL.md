---
name: structure-prediction
description: "Plan and validate PaddleHelix HelixFold structure-prediction
  workflows without unsafe downloads or GPU inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Structure Prediction

Use this sub-skill when a request mentions HelixFold3 input JSON, HelixFold inference, MSA or database paths, checkpoint placement, `bf16` versus `fp32`, protein structure output files, or HelixFold-S1 modules.

## Safety Boundary

Do not download genetic databases or model weights, launch training, launch GPU/DCU inference, mutate a user environment, or invoke original repository launch scripts as a default action. If the user explicitly approves execution, construct a command from the bundled references after validating local paths and runtime prerequisites. Reduced HelixFold3/S1 databases are hundreds of GB after extraction, and the inference commands assume a compatible PaddlePaddle GPU stack plus MSA binaries.

Safe default actions:

1. Classify the requested workflow: HelixFold3, HelixFold-S1, HelixFold, or HelixFold-Single.
2. Validate or review inputs using `scripts/validate_helixfold3_input.py` before planning any run.
3. Check that required paths are user-provided: MSA binaries, databases, checkpoint files, input JSON/FASTA, and output directory.
4. Plan command substitutions and resource choices without executing the command.
5. Explain expected output files and ranking/metric files so the user can inspect an existing run.

The lightweight PaddleHelix inspection environment is not a HelixFold runtime environment. Treat PaddlePaddle GPU, MSA tools, OpenMM/PDBFixer, `pgl`, RDKit, model checkpoints, and genetic databases as optional workflow dependencies that must be planned and confirmed before use.

## Route Map

- For HelixFold3 biomolecular JSON, command anatomy, precision choices, outputs, and non-commercial caveats, read `references/helixfold3.md`.
- For HelixFold, HelixFold-Single, and HelixFold-S1 distinctions, training/inference boundaries, and S1 module flow, read `references/helixfold-family.md`.
- For entity JSON, FASTA, database, checkpoint, and output path contracts, read `references/data-formats.md`.
- For common failures such as malformed JSON, missing MSA tools, CUDA/Paddle mismatch, unsupported `bf16`, token/memory limits, or missing checkpoints, read `references/troubleshooting.md`.
- For general protein sequence modeling, tokenization, TAPE-style prediction, or protein function workflows, route to `../protein-sequence-function/SKILL.md`.
- For compound docking or HelixDock workflows, route to `../compound-drug-discovery/SKILL.md`.

## Bundled Validator

Run this only as a local JSON/schema preflight; it does not import Paddle, download data, or start inference:

```bash
python scripts/validate_helixfold3_input.py --help
python scripts/validate_helixfold3_input.py input.json --mode helixfold3 --max-tokens 1200
python scripts/validate_helixfold3_input.py input.json --mode helixfold-s1
```

Use `--mode helixfold-s1` when validating the S1 top-level fields (`job_name`, `recycle`, `ensemble`, `model_type`), `s1_sample_constraint`, S1 sidechain replacements, and the S1 multi-chain expectation. Use `--strict-sequence-alphabet` only when the user wants alphabet-level rejection rather than warnings.

## Planning Checklist

- Confirm commercial/non-commercial constraints before using HelixFold3 model code, model parameters, or the free server output.
- Prefer `fp32` on V100-class GPUs; use `bf16` only on hardware known to support it, such as A100/H100-class GPUs.
- Keep `infer_times`, diffusion batch size, token count, and subbatch/recycle settings conservative when planning for 32 GB GPUs.
- Treat `full_dbs` support for HelixFold3/S1 as unavailable unless the user has current evidence that their local version supports it; documented reduced databases are already large.
- Never assume the validation script proves that checkpoints, MSA tools, databases, CUDA, Paddle, or GPU memory are available. It only proves the input file shape is plausible.
