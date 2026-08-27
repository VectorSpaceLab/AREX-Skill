# OpenAlphaTensor Workflows

## CLI workflow

1. Load `config.json` or override selected keys with CLI flags.
2. Compute `input_size`, `n_steps`, and `n_logits` in `main.py`.
3. Call `train_alpha_tensor(...)` with the derived values.
4. Let the root operation build the model, optimizer, checkpoint state, and trainer.
5. Save the final model and parameter JSON into `save_dir`.

## API workflow

1. Construct all arguments explicitly in Python.
2. Pass the desired `device`, directories, and multi-GPU `extra_devices`.
3. Keep the run reproducible by setting `random_seed` when needed.
4. Resume from checkpoints by pointing `checkpoint_dir` and `checkpoint_data_dir` at existing training state.

## Practical notes

- The public CLI defaults to CUDA but can be pointed at another device string.
- The `checkpoint_dir` and `checkpoint_data_dir` are used both for resuming and for persisting search data.
- The model search is intentionally long-running; the bundled probe script only validates config shape and importability.
