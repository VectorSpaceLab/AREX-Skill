# Training Troubleshooting

## Data Download and Layout

- Full training data is about 16.5 GB; the sample data is about 47 MB and is better for smoke tests.
- Missing `list.csv`, `valid_clusters.txt`, or `test_clusters.txt` prevents cluster construction before training starts.
- Missing `pdb/` or sampled `.pt` files causes loader failures or empty examples.
- Run `scripts/check_training_layout.py` before launching an expensive GPU job.

## Dependencies

- Base inference/training requires Python, PyTorch, and NumPy.
- `training/utils.py` imports `dateutil.parser`; install `python-dateutil` if missing.
- `training/parse_cif_noX.py` imports SciPy KDTree and `pdbx` reader modules for mmCIF preparation paths.
- Dataset preparation code may assume external structure-alignment tooling; treat CIF parsing as a separate data-preparation task from normal retraining.

## CUDA and Mixed Precision

- Full training is expected to use CUDA; CPU is only realistic for import checks or tiny smoke tests.
- `--mixed_precision True` uses `torch.cuda.amp`; if CUDA/driver/AMP issues appear, retry a small smoke with `--mixed_precision False`.
- Out-of-memory usually means the token budget is too high; reduce `--batch_size`, `--max_protein_length`, or `--num_examples_per_epoch`.

## Batch Size Means Tokens

`training/utils.py` groups examples by sequence length and starts a new batch when `length * number_of_examples` would exceed `--batch_size`. A `--batch_size` of `10000` is a residue-token budget, not 10,000 proteins.

## Output Folder Surprises

`training.py` calls `time.strftime` on `--path_for_outputs`. Literal paths work normally, but percent-format tokens in the path can expand to date/time strings. The script appends a trailing slash, creates `model_weights/`, and writes `log.txt` only when not resuming.

## Resume Checkpoints

- `--previous_checkpoint` must point to an existing `.pt` checkpoint file.
- Resume with architecture flags compatible with the checkpoint, especially `--hidden_dim`, layer counts, and `--num_neighbors`.
- The optimizer state is restored, so mismatched optimizer/device assumptions can surface during resume.

## Custom Checkpoint Inference

- Inference loads `<path_to_model_weights>/<model_name>.pt`.
- If the file is `epoch_last.pt`, use `--model_name epoch_last`.
- If the file is `epoch50_step12345.pt`, use `--model_name epoch50_step12345`.
- `--path_to_model_weights` must be the directory, not the checkpoint file.

## Empty or Bad Training Rows

- `list.csv` rows are filtered by resolution and deposition date.
- In debug mode, only the first rows are used and validation is set equal to training.
- Bad characters, overlength examples, missing assemblies, or missing chain tensors can reduce usable examples.
