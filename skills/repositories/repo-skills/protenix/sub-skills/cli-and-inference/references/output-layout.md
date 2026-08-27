# Output Layout

## Prediction Output Root

`protenix pred --out_dir OUT` sets the inference dump root. The runner creates the output root and an `ERR` directory at startup. Successful predictions are written below the output root by dataset/input name, sample name, and seed.

Typical command:

```bash
protenix pred --input input.json --out_dir output --model_name protenix_base_default_v1.0.0 --use_default_params true
```

Expected code-level layout from the current dumper:

```text
output/
  <dataset_name>/
    <sample_name>/
      seed_<seed>/
        predictions/
          <sample_name>_sample_<rank>.cif
          <sample_name>_summary_confidence_sample_<rank>.json
          <sample_name>_full_data_sample_<rank>.json  # only with --need_atom_confidence true
```

Some older docs describe a flatter `<name>/<seed>/...` layout. Prefer the current dumper layout above when explaining this checkout/package generation.

## Directory Inputs

When `--input` points to a directory, Protenix recursively collects files and keeps only paths ending in `.json`. It initializes one runner, then iterates over the JSON files. Output may contain separate dataset/sample subtrees for each JSON job.

If the command returns quickly with no prediction folders, check whether the directory actually contained `.json` files and whether errors were recorded under `ERR`.

## Ranking and File Names

The dumper sorts output ranks by each sample's `ranking_score` when sorted ranking is enabled. File names use `sample_<rank>` in both CIF and confidence JSON outputs:

```text
<sample_name>_sample_0.cif
<sample_name>_summary_confidence_sample_0.json
```

A lower numeric suffix is the rank position assigned after sorting, not necessarily the original diffusion sample index. Use the summary confidence JSON files to compare `ranking_score`, `plddt`, `ptm`, `iptm`, `gpde`, clash flags, and chain-level confidence values.

## Confidence Outputs

Every prediction sample writes a summary confidence JSON:

```text
output/<dataset_name>/<sample_name>/seed_101/predictions/<sample_name>_summary_confidence_sample_0.json
```

When `--need_atom_confidence true` is passed, Protenix additionally writes cleaned full atom-level confidence data:

```text
output/<dataset_name>/<sample_name>/seed_101/predictions/<sample_name>_full_data_sample_0.json
```

Use atom-level confidence only when the user explicitly needs it; it can increase output size.

## Structure Outputs

Predicted structures are written as CIF files:

```text
output/<dataset_name>/<sample_name>/seed_101/predictions/<sample_name>_sample_0.cif
```

The B-factor field may contain atom pLDDT values when available.

## Error Outputs

The runner creates `OUT/ERR` before inference. Per-input exceptions collected during batch prediction are tracked and logged. If sample-specific error files are present, inspect them first for JSON/schema, missing feature, or preprocessing errors.

Interpretation guide:

| Symptom | Likely level | Route |
| --- | --- | --- |
| `protenix` command not found or help cannot render | Installation/entry point | Stay in this sub-skill for CLI diagnosis. |
| Missing checkpoint/cache before any sample folder appears | Runtime data root/checkpoint setup | Stay in this sub-skill for cache root expectations. |
| Error after a specific JSON starts preprocessing | Input schema or feature paths | Route to `../../input-data-and-features/SKILL.md`. |
| Error from MSA/template/RNA search tools or databases | Preprocessing dependencies | Route to `../../msa-template-and-prep/SKILL.md`. |
| CUDA extension, CUTLASS, cuEquivariance, or layernorm JIT error | Backend/kernel setup | Use fallback command here, then route to `../../advanced-model-configuration/SKILL.md`. |

## Output Directory Surprises

- `--out_dir` is a root, not a single file path.
- Protenix may create nested folders using names from JSON data and generated dataset labels.
- If `--use_template true` or `--use_rna_msa true` causes automatic search, updated JSON files or feature artifacts may also be produced under the output/search area before final prediction.
- Directory input can create multiple nested output subtrees from one command.
- Existing output folders are reused; choose a fresh output root for clean debugging.
