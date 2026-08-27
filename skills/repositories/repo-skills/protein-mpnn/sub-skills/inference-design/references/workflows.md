# ProteinMPNN Inference Workflows

These recipes are distilled from verified inference patterns and runner behavior. Replace paths with the user's local ProteinMPNN checkout paths.

## Single PDB Design

Use this when the user has one PDB and wants to redesign selected chains without first creating parsed JSONL.

```bash
python protein_mpnn_run.py \
  --pdb_path inputs/target_complex.pdb \
  --pdb_path_chains "A B" \
  --out_folder outputs/direct_pdb_design \
  --num_seq_per_target 2 \
  --sampling_temp "0.1" \
  --seed 37 \
  --batch_size 1
```

Notes:

- Omit `--pdb_path_chains` to design every parsed chain.
- Direct PDB mode internally builds the designed/fixed chain dictionary.
- Use this mode for quick CPU-safe dry runs because it avoids helper JSONL setup.

## Parsed JSONL Monomer Batch

Use this when helper scripts have already parsed one or many monomer PDBs into JSONL.

```bash
python protein_mpnn_run.py \
  --jsonl_path outputs/monomer_batch/parsed_pdbs.jsonl \
  --out_folder outputs/monomer_batch \
  --num_seq_per_target 2 \
  --sampling_temp "0.1" \
  --seed 37 \
  --batch_size 1
```

Notes:

- With no `--chain_id_jsonl`, all chains in each parsed target are designed.
- A monomer batch writes one `seqs/<target>.fa` file per parsed target.

## Parsed JSONL Multichain Design

Use this when helper scripts already created both parsed structure JSONL and chain assignment JSONL.

```bash
python protein_mpnn_run.py \
  --jsonl_path outputs/multichain_batch/parsed_pdbs.jsonl \
  --chain_id_jsonl outputs/multichain_batch/assigned_pdbs.jsonl \
  --out_folder outputs/multichain_batch \
  --num_seq_per_target 2 \
  --sampling_temp "0.1" \
  --seed 37 \
  --batch_size 1
```

The assignment JSONL maps each target name to `[designed_chains, fixed_chains]`, for example chains `A B` designed while `C` or other chains stay fixed. Build or modify those helper JSONL files through `../constraint-inputs/`.

## Score Only From PDB Sequence

Use this when the user wants model uncertainty/negative log-probability for existing PDB backbone-sequence pairs, not new designs.

```bash
python protein_mpnn_run.py \
  --pdb_path inputs/target_complex.pdb \
  --pdb_path_chains "A B" \
  --out_folder outputs/score_native \
  --num_seq_per_target 10 \
  --sampling_temp "0.1" \
  --score_only 1 \
  --seed 37 \
  --batch_size 1
```

Notes:

- `score_only` writes `score_only/*.npz` and does not write new `seqs/*.fa` designs.
- `num_seq_per_target` controls how many repeated stochastic scoring passes are made through `N // batch_size`.

## Score Only From FASTA

Use this when the user wants to score custom sequences against a backbone.

```bash
python protein_mpnn_run.py \
  --path_to_fasta inputs/designed_sequences.fa \
  --pdb_path inputs/target_complex.pdb \
  --pdb_path_chains "A B" \
  --out_folder outputs/score_custom_fasta \
  --num_seq_per_target 5 \
  --sampling_temp "0.1" \
  --score_only 1 \
  --seed 13 \
  --batch_size 1
```

Important behavior:

- The runner scores the PDB/native sequence first, then each FASTA sequence.
- FASTA records for multiple designed chains should use `/` separators in alphabetically sorted designed-chain order, such as `CHAIN_A_SEQUENCE/CHAIN_B_SEQUENCE`.
- No new designed sequences are generated; this mode produces score NPZ files only.

## Unconditional Probability Output

Use this to produce PSSM-like log probabilities from backbone alone.

```bash
python protein_mpnn_run.py \
  --jsonl_path outputs/probability_batch/parsed_pdbs.jsonl \
  --out_folder outputs/probability_batch \
  --num_seq_per_target 1 \
  --sampling_temp "0.1" \
  --unconditional_probs_only 1 \
  --seed 37 \
  --batch_size 1
```

This writes `unconditional_probs_only/<target>.npz` with `log_p`, `S`, `mask`, and `design_mask` arrays and skips FASTA design output.

## Conditional Probability Output

Use this to ask for position-wise log probabilities conditioned on sequence and backbone.

```bash
python protein_mpnn_run.py \
  --pdb_path target.pdb \
  --pdb_path_chains "A" \
  --out_folder outputs/conditional_probs \
  --num_seq_per_target 1 \
  --conditional_probs_only 1 \
  --batch_size 1
```

Add `--conditional_probs_only_backbone 1` when the intended quantity is conditional on backbone rather than the full rest of sequence plus backbone.

## Save Scores and Sample Probabilities During Design

Use these flags in default design mode when the user wants numerical arrays in addition to FASTA output.

```bash
python protein_mpnn_run.py \
  --pdb_path target.pdb \
  --pdb_path_chains "A" \
  --out_folder outputs/design_with_arrays \
  --num_seq_per_target 4 \
  --sampling_temp "0.1 0.2" \
  --save_score 1 \
  --save_probs 1 \
  --seed 37 \
  --batch_size 1
```

Expect `seqs/`, `scores/`, and `probs/` subdirectories.

## CA-Only Monomer Design

Use this when the input structure should be parsed using CA atoms and CA-only weights.

```bash
python protein_mpnn_run.py \
  --pdb_path target_ca_only_or_backbone.pdb \
  --pdb_path_chains "A" \
  --out_folder outputs/ca_only_design \
  --ca_only \
  --model_name v_48_020 \
  --num_seq_per_target 2 \
  --sampling_temp "0.1" \
  --seed 37 \
  --batch_size 1
```

Do not add `--use_soluble_model`; CA-soluble weights are not available in the runner.

## Soluble Model Design

Use this for full-backbone soluble-protein-biased weights.

```bash
python protein_mpnn_run.py \
  --pdb_path soluble_target.pdb \
  --pdb_path_chains "A" \
  --out_folder outputs/soluble_design \
  --use_soluble_model \
  --model_name v_48_020 \
  --num_seq_per_target 2 \
  --sampling_temp "0.1" \
  --seed 37 \
  --batch_size 1
```

Use only with full-backbone inputs, not `--ca_only`.

## CPU-Safe Dry Run Pattern

For a first run on an unknown machine, prefer:

```bash
python protein_mpnn_run.py \
  --pdb_path target.pdb \
  --pdb_path_chains "A" \
  --out_folder outputs/dry_run \
  --num_seq_per_target 1 \
  --sampling_temp "0.1" \
  --seed 37 \
  --batch_size 1
```

ProteinMPNN automatically selects CUDA when `torch.cuda.is_available()` is true, otherwise CPU. CPU runs can be slow; reduce target length or samples before changing model code.
