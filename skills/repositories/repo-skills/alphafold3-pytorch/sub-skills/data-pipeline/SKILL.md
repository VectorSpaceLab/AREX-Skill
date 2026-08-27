---
name: data-pipeline
description: "Prepare and validate AlphaFold 3 mmCIF/PDB, MSA, template, crop,
  sampling, and large-dataset curation inputs without performing unsafe
  acquisition or mutation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data pipeline

Use this sub-skill when the task involves a local structure file, PDB dataset
layout, MSA or template features, crop selection, weighted PDB sampling, or a
plan for PDB/AFDB/CCD curation. Start with the safe preflight helper, then use
the smallest applicable reference:

- [PDB and mmCIF workflows](references/pdb-mmcif-workflows.md) for `PDBInput`,
  `PDBDataset`, `PDBDistillationDataset`, parsing, writing, assembly choice,
  and conversion.
- [MSA and templates](references/msa-and-templates.md) for A3M/HHR/M8 layout,
  pairing, cutoffs, and Kalign.
- [Dataset curation](references/dataset-curation.md) for split dates, CCD,
  AFDB/PDB scale, filtering, clustering, and cache planning.
- [Weighted sampling](references/weighted-sampling.md) for cluster mappings,
  formulas, and sampler-to-dataset integration.
- [Troubleshooting](references/troubleshooting.md) for failure recovery and
  stop conditions.

Run `scripts/validate_data_layout.py --help` before using it. The helper only
checks explicitly supplied local paths, extensions, naming/layout conventions,
CSV mapping headers/IDs, dates, and crop/config consistency. It never
imports the package, downloads, parses-and-rewrites, filters, clusters,
launches workers, starts a server, runs Kalign, or trains a model.

Keep this boundary explicit: model forward and sampling belong to
`model-inference`; generic `Alphafold3Input` construction and atom conversion
belong to `input-representation`; Trainer/YAML ownership belongs to
`training-configuration`; CLI or interactive app operation belongs to
`cli-serving`. This sub-skill can produce the PDB-derived features those
areas consume, but does not execute their work.

## Safe operating sequence

1. Preflight the intended structure, MSA, template, CCD, and cluster paths with
   the bundled validator.
2. Confirm whether the input is curated PDB, arbitrary mmCIF, or AFDB
   distillation data; do not infer this from a filename alone.
3. Choose training/validation/inference/distillation semantics and an explicit
   crop, length, MSA, template, and cutoff policy.
4. Only after a human-approved acquisition and resource plan, load
   `PDBInput`/a dataset and convert to atom inputs. Treat the curation and
   distillation acquisition interfaces as reference-only because they are
   networked, mutating, multiprocessing, or dataset-scale.
5. Record missing optional features as intentional fallbacks, not as silently
   verified biological coverage.
