---
name: enumeration
description: "Configure and validate REINVENT4 enumeration workflows, peptide
  amino-acid libraries, seed files, and attachment-point chemistry."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Enumeration

Use this sub-skill when a task mentions `enumeration.toml`, `run_type = "enumeration"`, peptide enumeration, amino-acid libraries, `scaffolds.smi`, `warheads.smi`, attachment points, LibInvent, LinkInvent, Mol2Mol seed files, or PepInvent masked peptide files.

## Read First

- `references/enumeration-workflow.md` for the `run_type = "enumeration"` config shape, peptide mask enumeration, scoring reuse, CLI invocation, and output CSV checks.
- `references/seed-files-and-chemistry.md` for scaffold, warhead, Mol2Mol, PepInvent, and enumeration amino-acid library file conventions.
- `references/troubleshooting.md` for attachment-point, separator, peptide-mask, config-key, scoring-block, and output failures.
- `scripts/validate_seed_files.py` for safe no-run validation of enumeration configs and seed files before launching REINVENT4.

## Fast Path

1. Confirm the job is `run_type = "enumeration"`; use the sibling `sampling` sub-skill for generator sampling and the sibling `scoring` sub-skill for standalone score-only jobs.
2. Put `smiles_file`, `amino_acid_library_file`, `aa_names_column`, `smiles_column`, optional `batch_size`, and optional `output_csv` under `[parameters]`.
3. Keep peptide templates in `smiles_file` as one CHUCKLES-like row per line with `?` masks and `|` fragment separators. Runtime peptide enumeration supports one or two masks per template row.
4. Add a normal `[scoring]` block to score enumerated peptides; validate the scoring block with the `scoring` sub-skill if components or transforms are complex.
5. Run a static check before execution:
   ```bash
   python sub-skills/enumeration/scripts/validate_seed_files.py enumeration.toml --kind enumeration
   ```
6. Run a small CPU job first:
   ```bash
   reinvent --device cpu --seed 123 --log-filename enumeration.log enumeration.toml
   ```

## Scope Boundaries

- This sub-skill owns `run_type = "enumeration"`, peptide/amino-acid enumeration parameters, seed-file conventions, attachment-point sanity checks, output CSV expectations, and chemistry/library-design validation.
- For scoring component design, transforms, aggregation, and plugin discovery, use the sibling `scoring` sub-skill.
- For `run_type = "sampling"` with LibInvent, LinkInvent, Mol2Mol, or PepInvent models, use the sibling `sampling` sub-skill after validating seed-file shape here when attachment points or masks are the problem.
- For transfer learning, staged learning, model vocabulary, invalid generated tokens, or trained-agent checkpoints, use the sibling `learning` or `sampling` sub-skill.
