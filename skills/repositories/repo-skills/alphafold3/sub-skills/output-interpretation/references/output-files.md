# AlphaFold 3 Output Files

AlphaFold 3 writes one output job directory per input job. The directory name is the sanitized job name: unsafe characters are replaced while case is preserved. If the directory already exists, AlphaFold 3 normally appends a timestamp-like suffix to avoid overwriting; `--force_output_dir` opts into reusing an existing directory.

## Expected Directory Tree

For a job named `example_job`, one seed `1234`, and five diffusion samples, expect this shape:

```text
example_job/
├── TERMS_OF_USE.md
├── example_job_data.json
├── example_job_model.cif
├── example_job_confidences.json
├── example_job_summary_confidences.json
├── example_job_ranking_scores.csv
├── seed-1234_sample-0/
│   ├── example_job_seed-1234_sample-0_model.cif
│   ├── example_job_seed-1234_sample-0_confidences.json
│   └── example_job_seed-1234_sample-0_summary_confidences.json
├── seed-1234_sample-1/
│   └── ...same three per-sample files...
├── seed-1234_embeddings/              # only when embeddings were saved
│   └── example_job_seed-1234_embeddings.npz
└── seed-1234_distogram/               # only when distograms were saved
    └── example_job_seed-1234_distogram.npz
```

There are `num_seeds * num_diffusion_samples` sample directories named `seed-<seed>_sample-<sample>`. By default, inference produces five samples per seed unless the run changes the number of diffusion samples.

## Top-Level Files

- `<job>_model.cif`: the highest-ranked predicted structure across all seeds and samples, in mmCIF format. AlphaFold 3 does not write PDB output directly.
- `<job>_confidences.json`: the full confidence arrays for the top-ranked prediction.
- `<job>_summary_confidences.json`: compact summary metrics for the top-ranked prediction.
- `<job>_data.json`: the input JSON after the data pipeline has added MSA/template data when applicable.
- `<job>_ranking_scores.csv`: one row per prediction with `seed`, `sample`, and `ranking_score`; the maximum score determines the top-level model and confidence files.
- `TERMS_OF_USE.md`: output terms emitted with completed inference outputs.

If inference did not run, top-level prediction files and ranking scores may be absent even if data-pipeline outputs exist.

## Per-Sample Files

Each `seed-<seed>_sample-<sample>/` directory should contain exactly the prediction for that seed/sample:

- `<job>_seed-<seed>_sample-<sample>_model.cif`
- `<job>_seed-<seed>_sample-<sample>_confidences.json`
- `<job>_seed-<seed>_sample-<sample>_summary_confidences.json`

Compare per-sample summary metrics when a user wants a prediction other than the global top-ranked sample, such as the best interface for selected chains.

## Optional Embeddings

Embeddings are written only when the run saves embeddings. They are grouped by seed, not by sample:

```text
seed-<seed>_embeddings/<job>_seed-<seed>_embeddings.npz
```

The `.npz` file is a compressed NumPy archive with:

- `single_embeddings`: shape `[num_tokens, 384]`, dtype `float16`.
- `pair_embeddings`: shape `[num_tokens, num_tokens, 128]`, dtype `float16`.

Embeddings can be several GiB for large inputs, so absence is normal unless the run explicitly requested them.

## Optional Distograms

Distograms are written only when the run saves distograms. They are grouped by seed:

```text
seed-<seed>_distogram/<job>_seed-<seed>_distogram.npz
```

The `.npz` file is a compressed NumPy archive with one member:

- `distogram`: shape `[num_tokens, num_tokens, 64]`, dtype `float16`.

Distograms can also be very large and are not required for ordinary structure inspection.

## Compression

When large-output compression is enabled, AlphaFold 3 writes mmCIF and full confidence JSON files with a `.zst` suffix using zstandard:

- `<job>_model.cif.zst`
- `<job>_confidences.json.zst`
- `<job>_seed-<seed>_sample-<sample>_model.cif.zst`
- `<job>_seed-<seed>_sample-<sample>_confidences.json.zst`

Summary confidence JSON files, ranking CSV, terms files, embeddings `.npz`, and distogram `.npz` are not converted to `.zst` by this flag. A validator should therefore accept either uncompressed or `.zst` variants for model CIF and full confidences, but should still expect summary JSON and ranking CSV as plain text when inference completed.

## Naming Gotchas

- Directory names and file prefixes use the sanitized job name, not necessarily the literal input name.
- Sample directories use `sample-0`, `sample-1`, and so on.
- Embeddings and distograms are per seed, not per sample.
- A timestamped output directory usually means the requested job output directory already existed and `--force_output_dir` was not used.
