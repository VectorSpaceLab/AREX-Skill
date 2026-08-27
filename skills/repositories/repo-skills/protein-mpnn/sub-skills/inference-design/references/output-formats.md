# Inference Output Formats

ProteinMPNN writes outputs under `--out_folder`. The runner creates subdirectories only for the modes requested.

## Directory Map

- `seqs/`: default design FASTA files, one `<target>.fa` per target.
- `scores/`: design-mode NPZ files when `--save_score 1` is set.
- `probs/`: design-mode NPZ files when `--save_probs 1` is set.
- `score_only/`: score-only NPZ files when `--score_only 1` is set.
- `conditional_probs_only/`: conditional probability NPZ files when `--conditional_probs_only 1` is set.
- `unconditional_probs_only/`: unconditional probability NPZ files when `--unconditional_probs_only 1` is set.

If a subdirectory is missing, first check whether the corresponding flag was enabled. For example, `scores/` is not created unless `--save_score 1` is used.

## Designed FASTA Files

A design FASTA begins with the parsed/native sequence header and sequence, followed by sampled sequences.

Native header fields:

- `score`: average negative log probability over redesigned positions.
- `global_score`: average negative log probability over all residues in all parsed chains.
- `fixed_chains`: chains kept fixed and not sampled.
- `designed_chains`: chains redesigned by ProteinMPNN.
- `model_name` or `CA_model_name`: selected checkpoint basename such as `v_48_020`.
- `git_hash`: commit detected by the runner, or `unknown` if unavailable.
- `seed`: actual seed used; if `--seed 0`, the runner randomly picks one.

Sample header fields:

- `T`: sampling temperature for that sequence.
- `sample`: 1-based sample index within that temperature.
- `score`: negative log probability over redesigned positions for the sampled sequence.
- `global_score`: negative log probability over all parsed residues for the sampled sequence.
- `seq_recovery`: fraction of redesigned positions matching the original sequence.

Multichain designed sequences use `/` separators between designed chains. The output order is sorted by designed-chain labels used internally, so match this order when preparing score-only FASTA input.

## Score-Only NPZ Files

`--score_only 1` writes files under `score_only/` and does not create new designed FASTA files.

Expected arrays:

- `score`: repeated negative log-probability scores over designed positions.
- `global_score`: repeated negative log-probability scores over all parsed residues.
- Some runner branches also include `S` and `seq_str` for the scored sequence; robust consumers should inspect keys instead of assuming only two arrays.

File naming behavior:

- Without `--path_to_fasta`, the runner scores the sequence from the PDB/backbone.
- With `--path_to_fasta`, the runner scores the PDB/backbone sequence first and then each FASTA record, using separate score files for FASTA entries.
- This mode is for scoring existing sequences. If the user expects generated designs, remove `--score_only 1`.

## Probability NPZ Files

### `--save_probs 1` in design mode

Files under `probs/` contain sampled design-time arrays:

- `probs`: sampled amino-acid probabilities.
- `log_probs`: model log probabilities for sampled sequences.
- `S`: sampled sequence indices in ProteinMPNN's alphabet order.
- `mask`: designed-position mask used for loss/scoring.
- `chain_order`: chain order metadata.

### `--conditional_probs_only 1`

Files under `conditional_probs_only/` contain:

- `log_p`: conditional log probabilities with shape conceptually `[samples, length, 21]`.
- `S`: input/native sequence indices.
- `mask`: parsed residue mask.
- `design_mask`: positions included in the design/scoring mask.

`--conditional_probs_only_backbone 1` changes what the conditional probabilities condition on.

### `--unconditional_probs_only 1`

Files under `unconditional_probs_only/` contain:

- `log_p`: unconditional log probabilities from backbone in one forward pass.
- `S`: input/native sequence indices.
- `mask`: parsed residue mask.
- `design_mask`: positions included in the design/scoring mask.

Use this mode for PSSM-like output. It skips designed FASTA generation.

## Interpreting Scores Safely

- Lower `score` generally means the model assigns higher probability to the designed/scored residues.
- Compare scores within the same target, chain mask, model family, and temperature setup; do not treat scores as globally calibrated across unrelated structures.
- `global_score` includes fixed chains and can differ substantially from `score` in multichain or fixed-chain runs.
- In score-only FASTA runs, make sure FASTA chain separators and chain order match the designed chains; otherwise scores may reflect mismatched sequence positions.
