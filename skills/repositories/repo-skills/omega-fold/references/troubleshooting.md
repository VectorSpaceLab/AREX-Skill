# OmegaFold Root Troubleshooting

Use this reference for cross-cutting failures before routing to a sub-skill-specific troubleshooting file.

## Quick Triage

| Symptom | Likely owner | Start with |
| --- | --- | --- |
| `omegafold` command missing, CLI flags unclear, checkpoint download surprises, device/OOM during command-line inference | CLI inference | [inference CLI troubleshooting](../sub-skills/inference-cli/references/troubleshooting.md) |
| Malformed FASTA, invalid residues, surprising PDB names, empty/sparse PDBs, confidence/B-factor confusion | Data/output handling | [data/output troubleshooting](../sub-skills/data-and-outputs/references/troubleshooting.md) |
| `make_config` errors, state-dict mismatch, Python API shape/device errors, no-weight predictions | Model API | [model API troubleshooting](../sub-skills/model-api/references/troubleshooting.md) |
| Import fails before any route works | Environment | [install and environment](install-and-environment.md) |

## Import Fails

First check the package and core dependencies:

```bash
python -m pip show OmegaFold
python - <<'PY'
import torch
import Bio
import omegafold
print('ok')
PY
```

Common fixes:

- Use Python 3.8, 3.9, or 3.10 for the legacy release install path.
- Install Biopython.
- Install a Torch build compatible with the selected Python and accelerator.
- If using Torch 1.12, install `numpy<2`.

## Help Works but Full Inference Fails

`omegafold --help` only proves parser import. Full inference also needs:

- A valid FASTA input file.
- A writable output directory path.
- A valid checkpoint for `--model 1` or `--model 2`, or permission to download it.
- Enough accelerator or CPU memory and time.
- A supported `--device` value.

Use the CLI smoke helper before full inference:

```bash
python sub-skills/inference-cli/scripts/omegafold_cli_smoke.py --fasta input.fasta --output-dir outputs --model 1
```

## Output Exists but Looks Wrong

OmegaFold writes one PDB per sequence. The PDB basename comes from the FASTA header after length sorting and platform path-separator replacement. Confidence is stored in B-factors after multiplying per-residue confidence by `100`.

Use the data helper when output naming or tensor preparation is the question:

```bash
python sub-skills/data-and-outputs/scripts/inspect_fasta_pipeline.py --fasta input.fasta --output-dir outputs
```

## API Snippet Fails

Use the model API helper first:

```bash
python sub-skills/model-api/scripts/inspect_model_api.py --check-invalid-model
```

Then confirm the snippet uses `pipeline.fasta2inputs` for inputs, aligns `make_config(1 or 2)` with the checkpoint family, unwraps a top-level `model` key from checkpoints when present, and moves model and inputs to the same device.

## Do Not Mask These Failures

- Do not treat no-weight predictions as scientifically meaningful.
- Do not suppress state-dict mismatch with `strict=False` unless the user explicitly wants experimental partial loading.
- Do not retry full inference after OOM without lowering `--subbatch_size` or changing resource assumptions.
- Do not start a checkpoint download when the user requested no-network execution.
