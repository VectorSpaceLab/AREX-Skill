# Utility helpers

These helpers are shared across the training, handler, metric, and distributed routes. Read this file when a workflow asks for tensor conversion, one-hot encoding, logger setup, seeding, deprecation handling, or checkpoint hashing.

| Helper | Purpose | Notes |
| --- | --- | --- |
| `convert_tensor(x, device=None, non_blocking=False)` | Move tensors, sequences, and mappings to a device. | Used by `prepare_batch` helpers and other tensor plumbing. |
| `apply_to_tensor(x, func)` | Apply a function to every tensor inside a nested structure. | Lower-level helper used by `convert_tensor`. |
| `apply_to_type(x, input_type, func)` | Generic nested-structure mapper. | Useful when adapting nested batches or outputs. |
| `to_onehot(indices, num_classes)` | Build a uint8 one-hot tensor from class indices. | TorchScript-friendly and shape-preserving. |
| `setup_logger(name="ignite", level=logging.INFO, stream=None, format=..., filepath=None, distributed_rank=None, reset=False, encoding="utf-8")` | Configure a logger for training runs, evaluators, and distributed workers. | Honors distributed rank and can write both to stream and file. |
| `manual_seed(seed)` | Seed Python `random`, PyTorch, NumPy when available, and XLA when available. | Call this before synthetic smoke checks or deterministic examples. |
| `deprecated(deprecated_in, removed_in="", reasons=(), raise_exception=False)` | Decorator that adds a deprecation warning and docstring note. | Used across compatibility layers and legacy APIs. |
| `hash_checkpoint(checkpoint_path, output_dir)` | Rename a checkpoint file with an SHA256 prefix and move it into `output_dir`. | Returns the new path and the full hash; useful for packaging models. |

## Common usage cues

- Use `convert_tensor` or `apply_to_tensor` when a batch contains nested lists, tuples, dictionaries, or namedtuples.
- Use `setup_logger` when you want log output to include the trainer/evaluator name and rank-aware behavior.
- Use `manual_seed` before synthetic examples so future agents can reproduce the same smoke output.
- Use `hash_checkpoint` only when you actually want to move and rename a checkpoint file.
