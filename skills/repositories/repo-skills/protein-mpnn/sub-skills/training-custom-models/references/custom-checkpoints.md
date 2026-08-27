# Custom Checkpoints for Inference

## Checkpoint Files Created by Training

Training writes checkpoints under the chosen output directory:

- `model_weights/epoch_last.pt`: latest checkpoint, overwritten each epoch.
- `model_weights/epoch{N}_step{S}.pt`: periodic snapshots controlled by `--save_model_every_n_epochs`.

Each checkpoint stores model weights plus optimizer state and metadata such as `num_edges` and `noise_level`. Inference reads `num_edges`, `noise_level`, and `model_state_dict`.

## Use a Custom Checkpoint for Design or Scoring

ProteinMPNN inference builds the checkpoint path as:

```text
<path_to_model_weights>/<model_name>.pt
```

Therefore, if the file is `runs/exp_custom/model_weights/epoch_last.pt`, use:

```bash
python protein_mpnn_run.py \
  --path_to_model_weights runs/exp_custom/model_weights \
  --model_name epoch_last \
  --pdb_path path/to/input.pdb \
  --pdb_path_chains "A" \
  --out_folder design_results/custom_model_design \
  --num_seq_per_target 8 \
  --sampling_temp "0.1" \
  --seed 37 \
  --batch_size 1
```

For scoring a known sequence, use the same checkpoint flags plus `--score_only 1` and, if needed, `--path_to_fasta`. Route detailed inference setup to `../inference-design/`.

## Model Name Rules

- `--model_name` is the checkpoint basename without `.pt`.
- `--path_to_model_weights` is the folder containing the checkpoint file, not the file itself.
- The folder must contain a file named exactly `<model_name>.pt`.
- Do not use `--use_soluble_model` when providing custom training weights unless the user intentionally wants the built-in soluble model path instead.
- Keep `--ca_only` consistent with the architecture used to train the checkpoint; the standard training script trains the full-backbone model.

## Debug Case: Folder Exists but Inference Cannot Find Epoch

If inference fails with a missing checkpoint path:

1. List the model folder: `ls path/to/model_weights`.
2. Confirm the file extension is `.pt`.
3. Set `--model_name` to the filename without `.pt`, for example `epoch50_step12345`.
4. Set `--path_to_model_weights` to the directory containing that file.
5. Avoid trailing filename duplication such as `--path_to_model_weights .../epoch_last.pt --model_name epoch_last`.

## After a Tiny Training Smoke

A useful end-to-end smoke is:

1. Run a one-epoch debug training job on sample data.
2. Confirm `model_weights/epoch_last.pt` exists.
3. Run inference on a small PDB using `--path_to_model_weights <debug-output>/model_weights --model_name epoch_last`.
4. Expect poor biological quality from a tiny debug checkpoint; the goal is only to validate wiring.
