---
name: msa-templates
description: "Prepare and validate Chai MSA and template inputs from aligned
  parquet, A3M, ColabFold server, m8, and staged ColabFold outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MSA Templates

Use this sub-skill when a Chai task involves evolutionary alignments, `.aligned.pqt` files, A3M conversion, ColabFold MSA/template servers, template hit `.m8` files, or reusing staged ColabFold outputs.

## Route

- For local MSAs, read `references/msa-template-workflows.md` and validate each `.aligned.pqt` with `scripts/validate_aligned_pqt.py` before folding.
- For A3M inputs, use `chai-lab a3m-to-pqt` for one query sequence per directory, then validate the generated filename and query row.
- For server MSAs/templates, prefer explicit `--use-msa-server` and `--use-templates-server` only when network calls to the ColabFold service are acceptable.
- For local templates, prepare a BLAST m8-style table and use `--template-hits-path`; use `CHAI_TEMPLATE_CIF_FOLDER` when template CIFs are custom or pre-cached.
- For existing ColabFold output trees, run `scripts/stage_colabfold_outputs.py` to create Chai-ready FASTA, `msas/*.aligned.pqt`, and `all_template_hits.m8` files.

## Primary References

- `references/msa-template-workflows.md` covers local MSA preparation, A3M conversion, server-side generation, template inputs, and ColabFold staging.
- `references/api-reference.md` lists CLI/API entry points, `.aligned.pqt` schema details, m8 columns, and mutual-exclusion rules.
- `references/troubleshooting.md` maps common MSA/template symptoms to concrete validation and recovery steps.

## Bundled Scripts

- `scripts/validate_aligned_pqt.py --help` checks required parquet columns, strict source values, query-row placement, aligned lengths, and Chai filename hashes without running inference.
- `scripts/stage_colabfold_outputs.py --help` adapts ColabFold output folders into a Chai-ready local input tree without calling any network service.

## Boundaries

- Use `../cli-inference/SKILL.md` for full `chai-lab fold` execution, GPU/runtime settings, ranking outputs, and `run_inference` result handling.
- Use `../input-data-formats/SKILL.md` for FASTA entity syntax, entity names, and chain naming before matching local m8 query IDs.
- Use `../restraints-glycans/SKILL.md` for contact, pocket, covalent, or glycan restraint files.
