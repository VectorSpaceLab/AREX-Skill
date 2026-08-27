# `colabfold_batch` CLI Reference

## Command Shape

```bash
colabfold_batch INPUT RESULTS [options]
```

`INPUT` may be a FASTA file, CSV/TSV file, A3M file, or directory of FASTA/A3M files. `RESULTS` is created or reused as the output directory. When `INPUT` is a FASTA/CSV without embedded A3M lines, ColabFold may query an MSA server unless `--msa-mode single_sequence` or a local MSA workflow is used.

## Minimal Commands

```bash
# One-step MSA server + prediction
colabfold_batch input_sequences.fasta out_dir

# Split MSA generation from GPU prediction
colabfold_batch input_sequences.fasta out_dir --msa-only
colabfold_batch input_sequences.fasta out_dir

# Predict from an existing directory of A3M files
colabfold_batch msas/ predictions/

# Generate AlphaFold3 input JSON only; no structure prediction
colabfold_batch input_sequences.fasta out_dir --af3-json
```

## MSA and Template Options

- `--msa-only`: generate and store MSAs/templates with `num_models=0`; no structure prediction or AlphaFold parameter download is required.
- `--msa-mode {mmseqs2_uniref_env,mmseqs2_uniref_env_envpair,mmseqs2_uniref,single_sequence}`: choose MSA source; A3M input overrides this choice.
- `--pair-mode {unpaired,paired,unpaired_paired}`: choose multimer MSA pairing behavior; default is `unpaired_paired`.
- `--pair-strategy {complete,greedy}`: `greedy` pairs when at least two MSAs share species, while `complete` requires species across all MSAs.
- `--templates`: enable template use. Without this flag, `--custom-template-path`, per-entry template paths, and `--pdb-hit-file` are ignored or invalid.
- `--custom-template-path DIR`: use local PDB files as custom templates; also set `--templates`.
- `--custom-template-cache-path DIR`: required when CSV inputs specify per-entry template paths.
- `--pdb-hit-file FILE --local-pdb-path DIR --templates`: use PDB hits from an M8-like file and a local mmCIF mirror.
- `--max-template-date YYYY-MM-DD` and `--max-template-hits N`: constrain template selection.

Do not combine `--custom-template-path` and `--pdb-hit-file`. Per-entry template paths in CSV also cannot be combined with `--custom-template-path`.

## Prediction Options

- `--model-type auto`: resolves to `alphafold2_ptm` for monomers and `alphafold2_multimer_v3` for complexes.
- `--model-type alphafold2|alphafold2_ptm|alphafold2_multimer_v1|alphafold2_multimer_v2|alphafold2_multimer_v3|deepfold_v1`: choose a specific model family.
- `--num-models 1..5`: reduce for quick checks, keep `5` for fuller model diversity.
- `--model-order 1,2,3,4,5`: execution/ranking order; source sorts the selected order before use.
- `--num-recycle N`: increase recycles for quality at higher runtime cost.
- `--recycle-early-stop-tolerance FLOAT`: stop recycles after convergence.
- `--num-ensemble N`: run more ensemble samples through the trunk.
- `--random-seed N --num-seeds M`: sample multiple seeds from `N` to `N+M-1`.
- `--max-seq N --max-extra-seq N` or `--max-msa max_seq:max_extra_seq`: constrain MSA depth to manage memory or sample conformations.
- `--disable-cluster-profile`: experimental multimer setting.
- `--use-dropout`: enable inference dropout for careful uncertainty/conformation sampling.
- `--initial-guess [PDB_OR_CIF]`: seed prediction with a PDB/CIF. If no file is provided, the main input must be PDB/CIF.
- `--calc-extra-ptm`: calculate pairwise ipTM/actifpTM and chain-wise pTM for complexes.
- `--no-use-probs-extra`: use binary contacts instead of probabilities for extra pTM metrics.
- `--data DIR`: point to an AlphaFold parameter data directory containing a `params/` subdirectory.

## Output Options

- `--rank {auto,plddt,ptm,iptm,multimer}`: choose model ranking metric. `auto` follows model/query type.
- `--stop-at-score FLOAT`: stop early once threshold is met; pLDDT for single-chain and pTM-like score for multimer routes.
- `--jobname-prefix TEXT`: replace input header job names with a prefix plus running number.
- `--save-all`, `--save-recycles`, `--save-single-representations`, `--save-pair-representations`: save larger raw/intermediate outputs for downstream analysis.
- `--skip-output msa,plots,pae_json`: omit selected nonessential outputs.
- `--overwrite-existing-results`: recompute jobs instead of respecting `.done.txt` or `.result.zip` completion markers.
- `--zip`: write `<jobname>.result.zip` and delete per-job result files after successful zipping, while keeping shared `cite.bibtex` and `config.json`.
- `--sort-queries-by {none,length,msa_depth,random}`: defaults to `length`; sorting by length/depth reduces recompilation.

## Backend and Runtime Options

- `--host-url URL`: use a non-default MSA server endpoint.
- `--disable-unified-memory`: clear ColabFold's unified-memory environment settings when TensorFlow/JAX memory behavior is problematic.
- `--recompile-padding N`: pad changing sequence lengths by `N` residues to reduce JAX recompilation; must be non-negative.
- `--use-pallas [true|false]`: enable Pallas/Triton kernels for faster Evoformer execution on supported GPUs; source requires bfloat16.
- `--debug-logging`: add verbose logs to `RESULTS/log.txt`.

## AlphaFold3 JSON Export

`--af3-json` calls the AF3 JSON generation route and returns before prediction. It can still generate MSAs using the chosen MSA mode and writes per-query JSON plus A3M outputs. Use it when the target job is AlphaFold3 input preparation, not ColabFold structure prediction.

## Preflight Validation

Before executing a heavy command:

1. Confirm the input parses and query names are unique; route to `../inputs-and-formats/SKILL.md` if needed.
2. Decide whether public MSA server use is acceptable or whether local MSAs should be prepared first; route to `../msa-search/SKILL.md` for local search.
3. Confirm `colabfold_batch --help` runs in the environment.
4. For prediction, confirm `colabfold[alphafold]`, `jax`, and model parameters are available or that parameter download is approved.
5. For GPU jobs, confirm device visibility and memory before scaling beyond a tiny representative query.
