# `protein_mpnn_run.py` CLI Reference

This reference covers flags future agents most often need for ProteinMPNN inference. Run commands from a ProteinMPNN checkout so `protein_mpnn_run.py`, `protein_mpnn_utils.py`, and weight folders are adjacent.

## Required Inputs

- `--out_folder PATH`: Required in practice. ProteinMPNN creates output subdirectories below this path.
- Exactly one normal input style should be selected:
  - `--pdb_path target.pdb`: single-structure mode. Optional `--pdb_path_chains "A B"` chooses designed chains; omitted means design all chains found in the PDB.
  - `--jsonl_path parsed_pdbs.jsonl`: batch mode over structures already parsed by helper scripts.
- Optional batch-mode constraints:
  - `--chain_id_jsonl assigned_pdbs.jsonl`: maps each target to designed and fixed chain lists.
  - `--fixed_positions_jsonl`, `--tied_positions_jsonl`, `--omit_AA_jsonl`, `--bias_AA_jsonl`, `--bias_by_res_jsonl`, `--pssm_jsonl`: constraint inputs prepared separately; use `../constraint-inputs/` for construction details.

If both `--pdb_path` and `--jsonl_path` are supplied, the script follows direct PDB mode because it branches on non-empty `pdb_path` first.

## Model Weights

ProteinMPNN selects a folder automatically unless `--path_to_model_weights` is provided.

- Vanilla full-backbone models: `vanilla_model_weights/v_48_002.pt`, `v_48_010.pt`, `v_48_020.pt`, `v_48_030.pt`.
- Soluble full-backbone models: `soluble_model_weights/v_48_002.pt`, `v_48_010.pt`, `v_48_020.pt`, `v_48_030.pt`; enable with `--use_soluble_model`.
- CA-only models: `ca_model_weights/v_48_002.pt`, `v_48_010.pt`, `v_48_020.pt`; enable with `--ca_only`.
- Do not combine `--ca_only` and `--use_soluble_model`: the runner exits because CA-soluble weights are unavailable.
- `--model_name` omits `.pt`, for example `--model_name v_48_020`.
- `--path_to_model_weights custom_folder` points to a folder containing `${model_name}.pt`; it is not a file path.

## Design Controls

- `--num_seq_per_target N`: requested total samples per target, but the runner computes `NUM_BATCHES = N // batch_size`. If `N < batch_size`, zero design batches run; if not divisible, the remainder is dropped.
- `--batch_size N`: number of copies sampled per batch. Use `1` for CPU, small GPUs, score-only debugging, and first dry runs.
- `--sampling_temp "0.1"` or `"0.1 0.2 0.3"`: one or more sampling temperatures. More temperatures multiply output samples.
- `--seed N`: deterministic if nonzero; `0` asks the script to choose a random seed.
- `--backbone_noise FLOAT`: Gaussian backbone perturbation during inference.
- `--max_length N`: skips/truncates targets exceeding the dataset limit during dataset construction.
- `--omit_AAs X` or similar: omits listed amino acids globally during sampling. The default omits `X`.

## Output Mode Flags

Only one major special mode should be used at a time.

- Default design mode: writes sampled FASTA files under `seqs/`; also writes `scores/` if `--save_score 1` and `probs/` if `--save_probs 1`.
- `--score_only 1`: scores native PDB sequences and optional FASTA-provided sequences; writes NPZ files under `score_only/`; does not write new designed FASTA sequences.
- `--path_to_fasta file.fa`: used with `--score_only 1` to score user-provided sequences. The FASTA sequence for multiple designed chains should concatenate alphabetically sorted designed chains with `/`, such as `SEQ_FOR_A/SEQ_FOR_B`.
- `--save_score 1`: in design mode, writes per-sample `score` and `global_score` arrays under `scores/`.
- `--save_probs 1`: in design mode, writes sampled probabilities/log-probabilities and sampled sequence indices under `probs/`.
- `--conditional_probs_only 1`: writes `conditional_probs_only/*.npz` for conditional log probabilities and skips sequence generation.
- `--conditional_probs_only_backbone 1`: changes conditional probabilities to condition only on backbone when used with `--conditional_probs_only 1`.
- `--unconditional_probs_only 1`: writes `unconditional_probs_only/*.npz` for PSSM-like unconditional log probabilities and skips sequence generation.
- `--suppress_print 1`: reduces logging; keep `0` while debugging.

## Chain Semantics

- In direct PDB mode, `--pdb_path_chains "A B"` means chains A and B are redesigned; all other parsed chains are fixed.
- In JSONL mode with no `--chain_id_jsonl`, all chains are designed.
- Designed chains appear in FASTA records in sorted masked-chain order, separated by `/` for multichain designs.
- Fixed chains contribute to `global_score` but not to the designed-region `score`.
