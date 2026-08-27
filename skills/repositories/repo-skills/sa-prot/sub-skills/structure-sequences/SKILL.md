---
name: structure-sequences
description: "Convert protein structures into SaProt structure-aware amino-acid
  plus 3Di sequences and diagnose Foldseek and pLDDT masking issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Structure Sequences

Use this sub-skill when an agent needs to convert a PDB or mmCIF protein structure into SaProt input sequences: amino-acid sequence, Foldseek 3Di sequence, or the combined AA+3Di format consumed by SaProt models.

## What this covers

- Run Foldseek `structureto3didescriptor` with chain-name output and convert its AA and 3Di columns into SaProt-ready records.
- Build combined tokens by pairing each amino acid with a lowercase 3Di character, for example `M#`, `Ev`, or `Qp`.
- Mask low-confidence AlphaFold-style regions by replacing the 3Di character with `#` when pLDDT is below the chosen threshold.
- Convert one or more selected chains and explain chain-name mismatches from Foldseek output.
- Diagnose missing Foldseek binaries, missing structure files, empty Foldseek output, Bio.PDB parser failures, and pLDDT length mismatches.

## Bundled converter

Use the bundled converter instead of importing SaProt repository utilities:

```bash
python scripts/convert_structure_sequence.py \
  --foldseek foldseek \
  --structure protein.cif \
  --chain A \
  --plddt-mask auto \
  --output-json protein.sequence.json \
  --output-fasta protein.sequence.fasta
```

Important arguments:

- `--foldseek` points to an executable Foldseek binary or to a command available on `PATH`.
- `--structure` is a `.pdb` or `.cif` structure file readable from the current working directory.
- `--chain` is repeatable; omit it to emit every chain Foldseek reports.
- `--plddt-mask` accepts `auto`, `true`, or `false`; use `true` for AlphaFold-style structures when low-confidence residues should be masked.
- `--plddt-threshold` defaults to `70.0` and controls when a 3Di position becomes `#`.
- `--seq-type` controls FASTA output: `combined`, `aa`, or `foldseek`.

See `references/sequence-formats.md` for token and masking details, and `references/troubleshooting.md` for failure handling.

## Boundaries and routing

- If a combined sequence already exists and the task is mutation scoring, embeddings, or model loading, route to `model-inference`.
- If the task is storing converted sequences in LMDB or wiring dataset configuration fields, route to `datasets-configs`.
- If the task is launching fine-tuning, pretraining, or evaluation runs, route to `training-evaluation`.
- Do not depend on original repository paths at runtime; copy or call the bundled converter from this sub-skill.
