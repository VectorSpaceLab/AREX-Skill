# Shared Configuration and Runtime Conventions

## ModelArgs pattern

Most model classes accept `args` as either a dict or a task-specific dataclass such as `ClassificationArgs`, `NERArgs`, `QuestionAnsweringArgs`, `LanguageModelingArgs`, `Seq2SeqArgs`, `T5Args`, `RetrievalArgs`, or `ConvAIArgs`.

```python
args = {"num_train_epochs": 1, "overwrite_output_dir": True, "no_save": True}
model = SomeModel(..., args=args, use_cuda=False)
```

or:

```python
from simpletransformers.classification import ClassificationArgs
args = ClassificationArgs()
args.num_train_epochs = 1
args.no_save = True
```

## Common fields

| Field | Why agents should care |
|---|---|
| `output_dir`, `best_model_dir`, `cache_dir`, `dataset_cache_dir` | Control writes and stale feature/model caches. |
| `overwrite_output_dir`, `reprocess_input_data`, `no_cache`, `no_save` | Essential for safe smoke/debug runs. |
| `max_seq_length`, `train_batch_size`, `eval_batch_size` | Frequent source of memory and truncation issues. |
| `num_train_epochs`, `learning_rate`, `scheduler`, `warmup_ratio`, `warmup_steps` | Training behavior. |
| `use_multiprocessing`, `process_count`, `dataloader_num_workers` | Can cause platform-specific hangs; disable for debugging. |
| `manual_seed` | Reproducibility. |
| `fp16`, `n_gpu`, constructor `use_cuda`, `cuda_device` | Backend/GPU behavior. |
| `wandb_project`, `wandb_kwargs` | Enables external tracking side effects. |
| `save_model_every_epoch`, `save_steps`, `save_best_model` | Checkpoint volume. |

## Smoke-run defaults

```python
args = {
    "num_train_epochs": 1,
    "train_batch_size": 2,
    "eval_batch_size": 2,
    "max_seq_length": 32,
    "overwrite_output_dir": True,
    "reprocess_input_data": True,
    "no_save": True,
    "silent": True,
}
```

Pass `use_cuda=False` at the constructor for CPU smoke runs.

## Production-run checklist

1. Replace `no_save=True` with explicit output/checkpoint policy.
2. Use user-approved `output_dir` and `cache_dir`.
3. Decide whether WandB logging is allowed.
4. Verify model/data downloads and licenses.
5. Confirm GPU availability before enabling CUDA.
6. Record args next to saved model artifacts.

## Inspection helper

Use `scripts/inspect_model_args.py` to list dataclass fields without opening source files.
