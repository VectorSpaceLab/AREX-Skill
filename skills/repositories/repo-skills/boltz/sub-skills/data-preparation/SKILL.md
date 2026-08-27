---
name: data-preparation
description: "Prepare and diagnose Boltz raw training/evaluation data pipelines,
  including CCD, clustering, MSA, RCSB/mmCIF, Redis, mmseqs, and processed file
  layouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Boltz Data Preparation

Use this sub-skill when the user needs to prepare, audit, or troubleshoot raw data before Boltz training or evaluation. It covers CCD preprocessing, sequence clustering, MSA conversion, RCSB/mmCIF structure processing, external service requirements, expected processed directories, and safe diagnostics.

## When To Use

- The user says `prepare Boltz training data`, `process raw MSA`, `run scripts/process`, `create clusters`, `Redis taxonomy`, `CCD preprocessing`, or `RCSB mmCIF pipeline`.
- The user has raw `.cif`/`.cif.gz`, `.a3m`/`.a3m.gz`, sequence FASTA, CCD, taxonomy, or cluster files and needs the processed layout expected by Boltz training.
- The user has processed targets but training fails to find `manifest.json`, `structures/*.npz`, MSA `.npz`, or ligand symmetry/CCD artifacts.

## Route Elsewhere

- For launching Hydra/PyTorch Lightning training after processed targets, processed MSAs, and symmetries are ready, use the Boltz training sub-skill.
- For `boltz predict` input YAML/FASTA authoring, prediction-time MSA server use, or prediction output interpretation, use the Boltz prediction sub-skill.
- For evaluation metrics after predictions already exist, use the Boltz evaluation sub-skill.

## Required Reading

- Read `references/preprocessing-workflows.md` for the stage-by-stage pipeline, external dependencies, and safe command patterns.
- Read `references/data-formats.md` for processed target/MSA/symmetry layouts and training-config wiring.
- Read `references/troubleshooting.md` when diagnosing missing Redis, mmseqs, `.a3m` naming, taxonomy/CCD DB, disk, file-size skips, or config mismatches.

## Safe First Check

Run the bundled dry-run checklist from this sub-skill directory before attempting any expensive preprocessing:

```bash
python scripts/boltz_preprocessing_checklist.py \
  --targets /path/to/processed_targets \
  --msa /path/to/processed_msa \
  --symmetries /path/to/symmetry.pkl \
  --taxonomy-db /path/to/taxonomy.rdb \
  --ccd-db /path/to/ccd.rdb \
  --mmseqs mmseqs \
  --redis-port 7777
```

The checklist only inspects local paths and optional TCP connectivity. It does not start Redis, download archives, run mmseqs, parse mmCIF files, or mutate data.

## Core Safety Rules

- Treat the original preprocessing scripts as reference workflows, not default commands: they need large downloads, Redis, mmseqs, multiprocessing, and dataset-scale side effects.
- Confirm disk capacity before raw MSA or full structure archives; expect tens to hundreds of GB, with temporary extraction often requiring roughly another archive-sized allocation.
- Keep Redis ports and DB filenames explicit: taxonomy DB for MSA processing, CCD DB for mmCIF/RCSB processing.
- Keep processed `target_dir`, `msa_dir`, and `symmetries` aligned with the training config before routing to training.
