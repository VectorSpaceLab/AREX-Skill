# Batch Prediction Workflows

## One-Step Small Prediction

Use this for a small FASTA/CSV when public MSA server use, model parameter availability, and local prediction hardware are acceptable.

```bash
colabfold_batch input_sequences.fasta out_dir --num-models 5 --model-type auto
```

Validation:

- `out_dir/log.txt` records version, query order, model execution, ranking, and failures.
- `out_dir/config.json` records command-equivalent runtime settings.
- Each completed job writes a `.done.txt` marker unless `--zip` was used.
- If an output already has `.done.txt` or `.result.zip`, reruns skip it unless `--overwrite-existing-results` is set.

## Two-Step MSA Then GPU Prediction

Use this when MSA generation can run on CPU/network resources separately from GPU prediction, or when scheduling GPU time is expensive.

```bash
# Step 1: no model prediction, no AlphaFold parameter download
colabfold_batch input_sequences.fasta out_dir --msa-only

# Step 2: reuse stored MSA/template intermediates and predict structures
colabfold_batch input_sequences.fasta out_dir --num-models 5 --model-type auto
```

For a complex, keep the same input and output directory across both steps so the second run can reuse matching `.a3m`/pickle intermediates. Review `out_dir/log.txt` after step 1 for MSA/template errors before allocating GPU time.

## Complex Prediction Plan

Multimer input is represented by multiple chains in one query. With `--model-type auto`, complex detection selects `alphafold2_multimer_v3`; explicit multimer versions are allowed when reproducing older behavior.

```bash
colabfold_batch complex.fasta complex_out \
  --model-type alphafold2_multimer_v3 \
  --pair-mode unpaired_paired \
  --pair-strategy greedy \
  --rank multimer \
  --num-models 5
```

Use `--pair-strategy complete` only when complete species pairing across all chains is more important than retaining partially paired sequences. If memory is tight, reduce `--num-models`, use `--max-msa`, or test `--num-models 1` first.

## Prediction From Precomputed A3M Directory

Use this after `colabfold_search` or another MSA route has produced A3M files.

```bash
colabfold_batch msas/ predictions/ --model-type auto --num-models 5
```

An A3M input overrides `--msa-mode`. This keeps prediction separate from local database search; use the `msa-search` sub-skill for database layout, search flags, and split/merge decisions.

## Single-Sequence or No-MSA Prediction

Use this when no MSA should be queried or when a fast baseline is needed.

```bash
colabfold_batch input_sequences.fasta out_dir --msa-mode single_sequence --num-models 1
```

This avoids MSA server use but generally lowers confidence for many targets. It still requires AlphaFold prediction dependencies and parameters.

## Template-Aware Prediction

Remote/server template query:

```bash
colabfold_batch input_sequences.fasta out_dir --templates --max-template-date 2022-01-01 --max-template-hits 20
```

Custom template directory:

```bash
colabfold_batch input_sequences.fasta out_dir \
  --templates \
  --custom-template-path templates_pdb_dir \
  --custom-template-cache-path template_cache
```

PDB-hit/mmCIF mirror route:

```bash
colabfold_batch input.a3m out_dir \
  --templates \
  --pdb-hit-file pdb70.m8 \
  --local-pdb-path pdb_mmcif_dir
```

Validation:

- `--templates` must be present for custom template and PDB-hit options to take effect.
- `--custom-template-path` and `--pdb-hit-file` are mutually exclusive.
- For per-entry template paths in CSV input, set `--custom-template-cache-path` and do not set `--custom-template-path`.
- Template domain names are written as `<jobname>_template_domain_names.json` when templates are enabled.

## AlphaFold3 JSON Export

Use this when the goal is AF3 input JSON, not ColabFold prediction.

```bash
colabfold_batch input_sequences.fasta af3_out --af3-json
```

Behavior:

- Structure prediction is skipped entirely.
- JSON files are written per query in the output directory.
- A3M files are also written from the generated or supplied MSA data.
- Non-protein molecule syntax belongs to the input-format route; verify FASTA syntax before running.

## Faster Prediction on Supported GPUs

On Ampere-or-newer NVIDIA GPUs, Pallas/Triton kernels can speed up Evoformer execution.

```bash
colabfold_batch input_sequences.fasta out_dir --use-pallas true
```

Use only with a compatible JAX/Triton stack. Source code rejects `use_pallas` when bfloat16 is disabled; the CLI keeps bfloat16 enabled by default.

## Scaling Pattern

1. Plan the command with `scripts/plan_colabfold_batch_command.py`.
2. Run `colabfold_batch --help` and environment checks before heavy work.
3. Test one short query with `--num-models 1` and explicit output directory.
4. Inspect `log.txt`, `config.json`, `.a3m`, score JSON, and PDB/mmCIF outputs.
5. Increase `--num-models`, seeds, recycles, templates, and batch size only after the small job succeeds.

## Notebook Evidence Handling

The bundled references capture the notebook workflows as command-line plans. Do not instruct future agents to run or depend on notebooks from a source checkout; treat notebooks as historical workflow examples only.
