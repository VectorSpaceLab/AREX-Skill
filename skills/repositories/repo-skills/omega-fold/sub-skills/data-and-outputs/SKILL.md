---
name: data-and-outputs
description: "Validate OmegaFold FASTA inputs, inspect pseudo-MSA tensors,
  predict PDB output names, and interpret confidence stored as B-factors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OmegaFold Data and Outputs

Use this sub-skill when an agent needs to validate OmegaFold FASTA input, explain how `pipeline.fasta2inputs` converts sequences into pseudo-MSA cycles, predict output PDB file names, or interpret confidence values stored in PDB B-factor columns.

For end-to-end model inference commands, use [inference CLI](../inference-cli/SKILL.md). For model construction, configs, and `OmegaFold.forward`, use [model API](../model-api/SKILL.md).

## Quick Routes

- Inspect FASTA parsing and output names safely with [`scripts/inspect_fasta_pipeline.py`](scripts/inspect_fasta_pipeline.py); it imports `omegafold.pipeline`, runs CPU-only `fasta2inputs`, and never downloads weights or runs the model.
- Check accepted FASTA syntax, residue normalization, pseudo-MSA tensor keys/shapes, output naming, and PDB confidence semantics in [`references/data-formats.md`](references/data-formats.md).
- Use Python APIs with parameter details, return contracts, examples, and gotchas in [`references/api-reference.md`](references/api-reference.md).
- Debug malformed FASTA, invalid residues, long headers, missing output directories, Biopython/PDB writer problems, empty outputs, and B-factor interpretation with [`references/troubleshooting.md`](references/troubleshooting.md).

## Safe Inspection Pattern

Run the bundled helper before full inference when input/output behavior is unclear:

```bash
python sub-skills/data-and-outputs/scripts/inspect_fasta_pipeline.py --write-tiny-pdb
```

The helper creates a tiny FASTA unless `--fasta` is provided, prints sequence count, normalized residue indices, `p_msa`/`p_msa_mask` shapes for every cycle, predicted PDB paths, and optionally writes a tiny synthetic PDB through `pipeline.save_pdb`.

## Ownership Boundaries

This sub-skill owns FASTA parsing, pseudo-MSA input preparation, output file naming, `save_pdb`, atom14 writer expectations, and confidence-as-B-factor explanations. It intentionally does not cover weight downloads, accelerator selection, resource flags, or full prediction commands; route those to [inference CLI](../inference-cli/SKILL.md).
