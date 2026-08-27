---
name: input-data-and-formats
description: "Validate AlphaFold FASTA, MSA, template, notebook, and
  data-pipeline inputs without running external searches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold Input Data and Formats

Use this sub-skill when a task is about preparing or diagnosing AlphaFold inputs before prediction: FASTA records, standard amino-acid validation, MSA/A3M/Stockholm parsing, template-search inputs, multimer chain mapping, notebook helper behavior, or external alignment binary assumptions.

## Start Here

- Validate FASTA content with [`scripts/validate_fasta.py`](scripts/validate_fasta.py) before building prediction commands or reusing MSAs.
- Read [`references/data-formats.md`](references/data-formats.md) for FASTA, A3M, Stockholm, deletion matrix, and multimer chain-format rules.
- Read [`references/api-reference.md`](references/api-reference.md) for parser, monomer pipeline, multimer pipeline, and template-featurizer API contracts.
- Read [`references/notebook-workflows.md`](references/notebook-workflows.md) when adapting Colab-style sequence validation, chunked MSA merging, placeholder templates, or cell-order checks.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for invalid residues, sequence length, chain-count, missing binary, stale MSA, template cutoff, and mmCIF/PDB parsing failures.

## Routing Boundaries

- Use this sub-skill for input sequence validation, parser behavior, data-pipeline signatures, template cutoff logic, multimer chain mapping, notebook helpers, and MSA/template format reasoning.
- Use `prediction-cli` for `run_alphafold` flags, model/db preset orchestration, output-directory naming, and `use_precomputed_msas` command planning.
- Use `docker-and-data-setup` for database download layout, Docker mounts, GPU container setup, and external data acquisition.
- Use `outputs-and-confidence` for prediction artifacts, confidence JSON, ranked structures, AlphaFold Server JSON, and AFDB output formats.

## Safe Workflow

1. Parse and validate FASTA records first; AlphaFold parser utilities are permissive and do not enforce standard residues or length limits by themselves.
2. Determine whether the target is monomer, homomer, or heteromer from the number of FASTA records and unique cleaned sequences.
3. Confirm that multimer targets stay within the PDB-format chain limit of 62 chains.
4. Treat MSA and template searches as expensive external operations requiring HMMER, HH-suite, Kalign, and database paths; reason from formats and API contracts unless the user explicitly asks to run them.
5. Reuse precomputed MSAs only when the sequence, output directory, database set, and search configuration are intentionally unchanged.

## Bundled Helper

```bash
python sub-skills/input-data-and-formats/scripts/validate_fasta.py target.fasta --mode auto --json
```

The helper is standalone, uses only the Python standard library, performs no imports from AlphaFold, and never calls external alignment, template, Docker, or prediction tools.
