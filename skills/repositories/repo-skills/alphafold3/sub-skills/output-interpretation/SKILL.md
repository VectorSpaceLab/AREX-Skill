---
name: output-interpretation
description: "Explain and validate AlphaFold 3 output directories,
  ranking/confidence files, optional embeddings/distograms, compression, and
  output-oriented troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold 3 Output Interpretation

Use this sub-skill when a user asks what an AlphaFold 3 result directory contains, whether a run produced expected outputs, how to choose a prediction, or why optional output files are missing or compressed.

## Quick Routing

- For constructing AlphaFold 3 input JSON, sequence/entity IDs, seeds, or model/data JSON fields, use `../input-preparation/`.
- For CLI flags such as `--save_embeddings`, `--save_distogram`, `--compress_large_output_files`, `--force_output_dir`, or separate data/inference runs, use `../running-predictions/`.
- For writer functions, model runner APIs, and programmatic output generation, use `../python-apis/`.
- For reading completed job directories, confidence metrics, ranking, embeddings, distograms, and output triage, stay here.

## Core References

- `references/output-files.md` describes expected job directory layout, sanitized naming, required and optional files, sample/seed subdirectories, and zstandard compression behavior.
- `references/confidence-metrics.md` explains `ranking_score`, pLDDT, PAE, pTM, ipTM, chain and chain-pair metrics, and antibody-antigen interface ranking.
- `references/troubleshooting.md` covers missing files, absent embeddings/distograms, low rankings or clashes, compressed large files, output directory collisions, and low-confidence predictions.

## Inspect Outputs Quickly

Run the bundled script on a completed AlphaFold 3 job directory:

```bash
python scripts/summarize_outputs.py /path/to/job_output
```

The script uses only the Python standard library. It reports expected top-level files, seed/sample directories, optional embedding/distogram directories, `.npz` member names when available, `ranking_scores.csv` rows, and keys from summary confidence JSON files. It does not import AlphaFold 3 and does not decompress `.zst` files.

## Interpretation Checklist

1. Identify the job directory name and sanitized job prefix; top-level result files normally use that prefix.
2. Confirm one `seed-<seed>_sample-<sample>` directory per seed/sample prediction, each with a model CIF, full confidences JSON, and summary confidences JSON.
3. Use top-level `<job>_ranking_scores.csv` to find the highest `ranking_score`; the top-level `<job>_model.cif` and confidence files are copied from that best-ranked sample.
4. Use summary confidences for ranking and overview metrics; use full confidences for per-atom pLDDT, PAE, contacts, and chain IDs.
5. Treat embeddings and distograms as optional: they appear only when the corresponding save flags were enabled, and they can be very large.
6. If `.cif.zst` or `_confidences.json.zst` files appear, the run used compression for large output files; summary JSON, ranking CSV, terms, embeddings, and distograms remain normally readable.
