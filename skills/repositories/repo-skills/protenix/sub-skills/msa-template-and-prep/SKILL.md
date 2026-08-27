---
name: msa-template-and-prep
description: "Plan and validate Protenix protein MSA, template search, RNA MSA,
  ColabFold-compatible MSA, and prep workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Protenix MSA, Template, and Prep

## When To Use

Use this sub-skill when a Protenix task needs planning or validation for protein MSA generation, template search, RNA MSA search, ColabFold-compatible MSA conversion, database/tool readiness, or MSA/template/RNA path layouts before inference or training.

Start here for:

- Choosing among `protenix msa`, `protenix mt`, and `protenix prep`.
- Validating existing `pairing.a3m`, `non_pairing.a3m`, `hmmsearch.a3m`, and RNA A3M paths before rerunning expensive search.
- Deciding whether `--msa_server_mode protenix` or `--msa_server_mode colabfold` is appropriate.
- Checking taxonomy-like paired MSA headers for multimer pairing.
- Planning HMMER, kalign, ColabFold/MMseqs, template database, and RNA database requirements.
- Understanding the training MSA layout involving `common/seq_to_pdb_index.json` and `mmcif_msa_template/<id>/` directories.

Route elsewhere for:

- Prediction command construction once MSA/template files already exist: `../cli-and-inference/SKILL.md`.
- Full JSON entity schema, ligand fields, bonds, modifications, and `pairedMsaPath`/`unpairedMsaPath` field placement details: `../input-data-and-features/SKILL.md`.
- Dataset-scale training data generation and training loops: `../training-and-data-pipeline/SKILL.md`.

## Safe First Actions

1. Identify what the user already has: input JSON, protein FASTA, protein MSA directory, RNA MSA file/root, template output, released data root, or custom training MSA root.
2. Treat MSA search, template search, RNA MSA search, ColabFold/MMseqs, database downloads, and bulk training MSA generation as expensive or side-effecting until the user confirms local tools, databases, storage, and permission.
3. Run the bundled read-only checker before rerunning search:
   `python sub-skills/msa-template-and-prep/scripts/check_msa_template_layout.py <path>`.
4. If existing files are valid, reuse them and route prediction to `../cli-and-inference/SKILL.md`.
5. If files are stale or missing, choose the smallest preprocessing command: `msa` for protein MSA, `mt` for protein MSA plus templates, or `prep` for protein MSA plus templates plus RNA MSA.

## Command Choice

| User need | Recommended action |
| --- | --- |
| Protein JSON/FASTA lacks MSA only | Plan `protenix msa --input INPUT --out_dir OUT --msa_server_mode protenix` or `colabfold`. |
| Protein JSON lacks templates too | Plan `protenix mt --input INPUT.json --out_dir OUT` with HMMER and seqres checks. |
| Mixed protein/RNA JSON lacks RNA MSA | Plan `protenix prep --input INPUT.json --out_dir OUT` with both template and RNA HMMER/database checks. |
| Existing JSON paths may be stale | Run the checker and fix paths before any search. |
| Raw ColabFold result needs Protenix layout | Validate/split into per-chain `pairing.a3m` and `non_pairing.a3m`; do not use raw combined A3M directly. |
| Training MSA layout is failing | Validate `common/seq_to_pdb_index.json` and `mmcif_msa_template/<id>/`; route full dataset prep to training. |

## Read Next

- `references/workflows.md` for CLI behavior, `msa_server_mode`, JSON update suffixes, live APIs, ColabFold-compatible MSA handling, and training MSA stages.
- `references/data-layouts.md` for protein, template, RNA, released-data, custom-training, and search-database layouts.
- `references/database-preparation.md` for safe external tool and database readiness decisions.
- `references/troubleshooting.md` for missing binaries/databases, stale paths, taxonomy header problems, missing MSA files, RNA database choices, ColabFold limitations, large outputs, network requirements, and template parser failures.
