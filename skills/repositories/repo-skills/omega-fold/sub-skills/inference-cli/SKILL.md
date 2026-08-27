---
name: inference-cli
description: "Run OmegaFold CLI inference from FASTA to PDB safely, including
  devices, weights, resources, dry-run validation, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OmegaFold inference CLI

Use this sub-skill when a task needs to run or validate OmegaFold command-line inference from a FASTA file to PDB outputs. Prefer the installed `omegafold` console script; use the installed-package fallback `python -m omegafold` only when the console script is unavailable but the package import works.

## Fast path

1. Validate the CLI without downloading model weights:
   ```bash
   python scripts/omegafold_cli_smoke.py
   ```
2. Inspect a FASTA and print a planned command without running inference:
   ```bash
   python scripts/omegafold_cli_smoke.py --fasta INPUT_FILE.fasta --output-dir OUTPUT_DIRECTORY --model 2 --device cuda
   ```
3. Run full inference only when weights, device, memory, and runtime are acceptable:
   ```bash
   omegafold INPUT_FILE.fasta OUTPUT_DIRECTORY --model 1 --device cuda
   ```

## Route by need

- Use [CLI reference](references/cli-reference.md) for flags, defaults, model choices, command templates, and installed-module fallback syntax.
- Use [inference workflow](references/inference-workflow.md) for safe validation, weights/cache decisions, device/resource planning, and output expectations.
- Use [troubleshooting](references/troubleshooting.md) for install/import errors, Python and Torch compatibility, missing weights, device mismatch, OOM, and output mistakes.
- Use [scripts/omegafold_cli_smoke.py](scripts/omegafold_cli_smoke.py) for no-download CLI help checks and FASTA dry-run planning.
- For FASTA normalization details, output file naming, PDB confidence fields, and validation of generated structures, route to [data-and-outputs](../data-and-outputs/SKILL.md).
- For direct Python use of `OmegaFold`, `make_config`, `fasta2inputs`, and tensor contracts, route to [model-api](../model-api/SKILL.md).

## Safety defaults

- `omegafold --help` is safe: it prints parser help and does not load weights.
- `omegafold INPUT_FILE.fasta OUTPUT_DIRECTORY ...` is not a smoke test: argument parsing selects a model, may download weights, then loads a large `torch` checkpoint before inference.
- Avoid full inference unless the user has approved network/download cost or has provided a local `--weights_file`, and the selected `--device` has enough memory.
