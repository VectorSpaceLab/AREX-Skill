# Output Interpretation Troubleshooting

Use this guide when an AlphaFold 3 output directory looks incomplete, confusing, compressed, or low confidence.

## Missing Top-Level Prediction Files

Symptoms:

- No `<job>_model.cif` at the job directory root.
- No `<job>_ranking_scores.csv`.
- Only `<job>_data.json` or data-pipeline artifacts are present.

Likely causes and checks:

- Inference did not run, failed, or was intentionally skipped. Data-pipeline-only runs can produce processed input JSON without model outputs.
- The job name was sanitized; inspect filenames for a sanitized prefix rather than the literal input name.
- Large-output compression was enabled; look for `.cif.zst` and `_confidences.json.zst` variants.
- The run wrote to a timestamped sibling directory because the requested output directory already existed.

## Missing Per-Sample Directories

Expected sample directories are named `seed-<seed>_sample-<sample>`. Missing directories usually mean inference did not finish for that seed/sample or the run used fewer diffusion samples than expected. Check `ranking_scores.csv`: each completed sample should have a row with its `seed`, `sample`, and `ranking_score`.

## Missing Embeddings or Distogram

Embeddings and distograms are optional outputs. Their absence is normal unless the run explicitly requested them:

- Embeddings require the embeddings save flag and appear as `seed-<seed>_embeddings/<job>_seed-<seed>_embeddings.npz`.
- Distograms require the distogram save flag and appear as `seed-<seed>_distogram/<job>_seed-<seed>_distogram.npz`.

If a user expected them but they are missing, route run-flag questions to `../running-predictions/`. Explain that these arrays are large: pair embeddings scale as `num_tokens * num_tokens * 128`, and distograms scale as `num_tokens * num_tokens * 64`, both stored as compressed NumPy archives.

## Compressed Large Files

When large-output compression is enabled, AlphaFold 3 compresses the largest text/binary prediction outputs with zstandard:

- mmCIF files become `*.cif.zst`.
- Full confidence JSON files become `*_confidences.json.zst`.

Summary confidence JSON files, ranking CSV, terms, embeddings `.npz`, and distogram `.npz` remain normally readable. If a downstream tool cannot read `.zst`, decompress a copy or rerun without compression. Do not treat `.zst` as evidence of a failed run.

## Output Directory Collision

If an expected output directory is absent but a similar directory with a suffix exists, AlphaFold 3 likely avoided overwriting an existing directory. This is normal unless the user intended to resume or combine data-pipeline and inference steps in the same directory. In that case, route flag guidance to `../running-predictions/` and discuss `--force_output_dir` cautiously because it allows reuse of a non-empty directory.

## Low Ranking Scores

A low or negative `ranking_score` can come from weak global/interface confidence, high disorder, or severe clashes. Start with:

1. Sort `ranking_scores.csv` descending by `ranking_score`.
2. Inspect the top sample's `*_summary_confidences.json`.
3. Check `has_clash`; a severe clash applies a large score penalty.
4. Compare `ptm`, `iptm`, and `fraction_disordered` to understand whether the score is low because the complex is uncertain, disordered, or physically clashing.

Do not compare raw ranking scores across unrelated jobs as if they were calibrated probabilities.

## Interpreting Failed or Low-Confidence Predictions

Use the failure mode that matches the user's scientific question:

- High local pLDDT but high cross-chain PAE: chains may be individually plausible but not confidently docked.
- Low pLDDT in flexible regions: may represent disorder rather than a modeling error.
- Low pTM for a very small chain: TM-derived metrics can be strict for short entities; inspect local pLDDT and PAE.
- Low ipTM for a complex: interface placement is uncertain; check chain-pair metrics for the specific interaction.
- High `chain_pair_iptm` but `has_clash=true`: do not choose the model without inspecting geometry; clashes may invalidate the interface.

## Antibody-Antigen Ranking Confusion

If a user asks for the best antibody-antigen prediction, do not blindly choose the highest full-complex `ranking_score`. Instead:

- Identify antibody and antigen chain IDs and their matrix indices.
- Compare off-diagonal `chain_pair_iptm` for that pair across samples.
- Use `chain_pair_pae_min` as supporting evidence; lower is better.
- Reject or down-rank samples with severe clashes or poor interface-local confidence.

## Summary JSON Present, Full JSON Missing

If summary confidence JSON exists but full confidences JSON appears missing, check for `_confidences.json.zst`. Compression applies to full confidence JSON but not summary JSON. A standard JSON reader cannot parse `.zst` directly.

## Integrated Triage: Low Score, Clashes, and Missing Optional Outputs

When a completed job has a very low ranking score and missing optional outputs, handle the questions in this order:

1. Run `scripts/summarize_outputs.py <job_dir>` to confirm which top-level, per-sample, summary, embedding, and distogram files exist.
2. Read `ranking_scores.csv` and the top sample's summary confidence JSON; if `has_clash=true`, account for the large clash penalty before interpreting `ranking_score` as only low confidence.
3. If clashes are severe on older GPUs, route to `../running-predictions/references/troubleshooting.md` and check the CUDA capability 7.x known issue before blaming the input alone.
4. If embeddings or distograms are absent, confirm whether the run used the corresponding save flags; absence is normal when those flags were false.
5. Separate scientific uncertainty from runtime/configuration issues: confidence metrics explain prediction quality, while missing optional outputs and GPU/backend warnings explain run configuration.

## Script Triage

Run `scripts/summarize_outputs.py` from this sub-skill to inventory a job directory. It is intentionally conservative: it reports present/missing files and readable keys but does not decide scientific validity for the user.
