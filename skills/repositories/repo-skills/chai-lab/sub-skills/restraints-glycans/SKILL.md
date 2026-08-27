---
name: restraints-glycans
description: "Author, validate, and troubleshoot Chai-1 restraint CSVs, covalent
  bonds, and glycan inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chai-1 Restraints and Glycans

Use this sub-skill when a task involves Chai-1 contact restraints, pocket restraints, covalent bond restraints, glycan FASTA records, or restraint CSV validation.

## Start Here

1. Read `references/restraints-and-glycans.md` for the CSV schema, contact/pocket/covalent semantics, residue/atom notation, chain naming, and glycan syntax.
2. Read `references/api-reference.md` when using `chai_lab.chai1.run_inference`, `parse_pairwise_table`, `write_pairwise_table`, or `PairwiseInteraction` directly.
3. Run `scripts/validate_restraints.py --help` and use the helper before launching inference.
4. Read `references/troubleshooting.md` when parsing succeeds but restraints do not affect the result, covalent atom lookup fails, or glycan syntax is rejected.

## Typical Workflow

- Confirm the FASTA chain naming mode first: automatic Chai chains are `A`, `B`, `C`, ... by FASTA order unless inference uses `fasta_names_as_cif_chains=True`.
- Create a restraint CSV with unique `restraint_id` values and `connection_type` set to `contact`, `pocket`, or `covalent`.
- Use residue notation such as `A219`, residue-atom notation such as `A219@CA`, and atom-only notation such as `@C1` only for covalent ligand/glycan sides where Chai should target the first token/residue.
- Validate cheap schema, notation, chain-name, glycan-string, and simple residue-position errors with `python scripts/validate_restraints.py restraints.csv --fasta input.fasta`.
- Pass the CSV through `constraint_path` in Python or the corresponding `chai-lab fold --constraint-path` CLI option.

## Boundaries

- For general FASTA entity syntax, modified residues, ligands, DNA/RNA, and entity-name uniqueness, use `../input-data-formats/SKILL.md`.
- For MSA directories, `.aligned.pqt`, ColabFold server use, and template hit files, use `../msa-templates/SKILL.md`.
- For full folding commands, output directories, devices, seeds, samples, and `StructureCandidates`, use `../cli-inference/SKILL.md`.
