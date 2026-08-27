# ProteinMPNN Training Workflow

## When Training Is Appropriate

ProteinMPNN training retrains the sequence-design model from prepared PDB biounit tensors. It is different from normal sequence design: the training script consumes a curated dataset directory, writes logs and checkpoints, and expects GPU-capable PyTorch for practical runs. Skip full training in routine verification because the public dataset is large and training is expensive.

## Dependencies

Minimum runtime dependencies are Python, PyTorch, and NumPy. Training data loading also imports `python-dateutil`. Dataset preparation from mmCIF uses SciPy and `pdbx`/mmCIF reader modules and may require external structure-alignment tooling depending on the preparation path.

## Important `training.py` Flags

- `--path_for_training_data`: directory containing `list.csv`, `valid_clusters.txt`, `test_clusters.txt`, and the `pdb/` tensor tree.
- `--path_for_outputs`: output run directory; `training.py` applies `time.strftime` to this string, then creates the folder and `model_weights/` inside it.
- `--previous_checkpoint`: `.pt` file to resume from; restores model, optimizer, epoch, and step.
- `--num_epochs`: number of epochs to run after the starting epoch.
- `--save_model_every_n_epochs`: writes numbered checkpoints at this interval.
- `--reload_data_every_n_epochs`: rebuilds sampled in-memory train/validation sets periodically.
- `--num_examples_per_epoch`: maximum PDB examples loaded into one epoch sample.
- `--batch_size`: token budget per batch, not number of examples; the loader groups similarly sized proteins until `max_length * examples <= batch_size`.
- `--max_protein_length`: filters assembled proteins longer than this length.
- `--hidden_dim`, `--num_encoder_layers`, `--num_decoder_layers`, `--num_neighbors`, `--dropout`, `--backbone_noise`: model architecture and augmentation settings.
- `--rescut`: resolution cutoff used while reading `list.csv`.
- `--debug True`: reduces data loading to a small subset, sets `num_examples_per_epoch=50`, `max_protein_length=1000`, and `batch_size=1000`.
- `--gradient_norm`: clips gradients when positive.
- `--mixed_precision`: uses CUDA AMP when true; on CPU, prefer setting this false for smoke tests.

## Tiny Debug Smoke

Use this only as a wiring check, preferably with the small sample training dataset. It still imports the training stack and may use multiprocessing, so keep output in a disposable folder.

```bash
python training/training.py \
  --path_for_training_data path/to/pdb_2021aug02_sample \
  --path_for_outputs runs/debug_training \
  --num_epochs 1 \
  --num_examples_per_epoch 20 \
  --batch_size 1000 \
  --max_protein_length 1000 \
  --debug True \
  --mixed_precision False
```

Expected results:

- `runs/debug_training/log.txt` exists unless resuming from `--previous_checkpoint`.
- `runs/debug_training/model_weights/epoch_last.pt` exists after the first completed epoch.
- Console/log lines look like `epoch: 1, step: 74, time: 45.7, train: 23.565, valid: 17.468, train_acc: 0.072, valid_acc: 0.113`.

## SLURM Adaptation Pattern

The repository sample uses one GPU, large memory, 12 CPU cores, and a week walltime. Adapt partition, GPU type, memory, environment activation, paths, and example count to the user's cluster:

```bash
#!/bin/bash
#SBATCH -p gpu
#SBATCH --mem=128g
#SBATCH --gres=gpu:a100:1
#SBATCH -c 12
#SBATCH -t 7-00:00:00
#SBATCH --output=training_run.out

python training/training.py \
  --path_for_outputs runs/exp_custom \
  --path_for_training_data path/to/pdb_2021aug02 \
  --num_examples_per_epoch 1000 \
  --save_model_every_n_epochs 50
```

For real training, keep `--mixed_precision True` on CUDA unless there is a hardware or driver issue. Reduce `--batch_size`, `--num_examples_per_epoch`, or `--max_protein_length` when memory is exhausted.

## Outputs

`training.py` creates:

- `log.txt`: tab header followed by epoch records containing epoch, step, seconds, train perplexity, validation perplexity, train accuracy, and validation accuracy.
- `model_weights/epoch_last.pt`: overwritten at every epoch; contains `epoch`, `step`, `num_edges`, `noise_level`, `model_state_dict`, and `optimizer_state_dict`.
- `model_weights/epoch{N}_step{S}.pt`: periodic checkpoint when `(epoch % save_model_every_n_epochs) == 0`.

## Resume Training

Resume by pointing `--previous_checkpoint` to a checkpoint file and reusing compatible architecture flags. The script restores model state, optimizer state, epoch, and total step. If `--previous_checkpoint` is set, `training.py` does not rewrite the log header; keep the same output folder only when appending intentionally.
