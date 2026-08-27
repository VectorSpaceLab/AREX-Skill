# Protein workflows

The DiG `protein/` subtree performs conformer sampling from protein features
and a trained checkpoint. The source workflow is a direct inference pipeline,
but it still depends on data files and a prebuilt model checkpoint.

## Inputs

- checkpoint path for the trained protein model
- feature pickle or list of feature pickles
- FASTA file or list of FASTA files
- output name or output list
- optional initial state `.npz`

## Main CLI contract

The source inference entry point accepts:

- `-c` / `--checkpoint`
- `-i` / `--pkl`
- `-s` / `--fasta`
- `-o` / `--output`
- `-n` / `--num-samples`
- `-p` / `--output-prefix`
- `--init-state`
- `--save-full-state` / `--no-save-full-state`
- `--use-tqdm` / `--no-use-tqdm`
- `--use-gpu` / `--no-use-gpu`

## Outputs

The workflow writes:

- a PDB file for the sampled conformer(s)
- an `_init_state.npz` file
- a `_final_state.npz` file

If `--save-full-state` is enabled, the PDB output contains multiple MODEL
blocks instead of a single end state.

## Runtime notes

- GPU use is optional in the source CLI, but the workflow is clearly easier on a
  CUDA host.
- The first run may spend time building the SO(3) helper array.
- The input sequence length must match the feature tensor length.
- `--use-gpu` only matters if CUDA is available in the current environment.

## What to do before a real run

- confirm the checkpoint exists and matches the selected model family
- confirm the feature pickle and FASTA correspond to the same protein
- decide whether you are sampling one structure or a `.list` file of many
  entries
- decide whether you need an initial state or a fresh random conformer

## Suggested review flow

1. Use the command renderer to spell out the inputs.
2. Validate that the feature and FASTA files match in length.
3. Check whether the environment has a usable GPU if you plan to use one.
4. Only then schedule the long inference run in a separate session.
