# Evaluation workflows

## 1) Built-in perplexity path

Use this path when you want the package's native perplexity score from a loaded causal model.

### Inputs
- `model`: a loaded xTuring causal model instance.
- `dataset`: a `TextDataset` or `InstructionDataset` that has already passed validation.
- `batch_size`: DataLoader batch size, default `1`.

### What happens
1. The model is put into eval mode and moved to `DEFAULT_DEVICE`.
2. A collator is built through `BasePreprocessor.create(dataset.config_name, tokenizer, finetuning_max_length, dataset.meta)`.
3. The dataset is wrapped in a DataLoader with `shuffle=False` and `drop_last=False`.
4. Each batch is sent through the model with labels to collect batch losses.
5. The final return is an aggregate perplexity scalar computed as `torch.exp(torch.stack(losses).sum() / len(dataset))`.

### What you get
- A single scalar perplexity tensor.
- No per-sample report.
- No JSON artifact unless you add your own persistence.

### Practical notes
- The evaluation path reuses the finetuning max-length setting, so long examples can be truncated.
- Batch size affects throughput, not the result schema.
- The score is an aggregate over returned loss values. The denominator is `len(dataset)`, not token count, so this is a package-specific perplexity scalar rather than a full token-normalized benchmark report.
- If you need token-level or sample-level reporting, build a custom evaluator.
- If CUDA is unavailable, the runtime falls back to CPU and evaluation can be slow.

## 2) Adapter scaffold path

Use this path when you want a stable evaluation contract and JSON result persistence around an adapter.

### Inputs
- `adapter`: a subclass of `BaseEvalAdapter`.
- `model`, `dataset`, `task_name`: opaque values forwarded to the adapter.
- `metadata`: optional caller metadata.
- `output_path`: optional result file path.

### Flow
1. Call `run_eval_adapter(...)`.
2. The wrapper timestamps the run before and after `adapter.run(...)`.
3. If the adapter did not set `started_at`, `finished_at`, or `duration_seconds`, the wrapper fills them in.
4. If `output_path` is set, the wrapper persists `EvalRunResult.as_dict()` as JSON.

### Current scaffold behavior
- `BaseEvalAdapter` is only the interface.
- `LMEvalAdapter` is a placeholder for lm-evaluation-harness style integrations.
- The adapter returns `status="planned"`, no metrics, and `metadata["integration_status"]="scaffold_only"`.
- `tasks`, `num_fewshot`, and `batch_size` are stored in the result metadata.
- Caller metadata is merged after the scaffold fields, so it can add or override keys.

### Example artifact shape
```json
{
  "adapter_name": "lm_eval",
  "task_name": "arc_easy",
  "status": "planned",
  "metrics": [],
  "metadata": {
    "tasks": ["arc_easy"],
    "requested_task": "arc_easy",
    "num_fewshot": 0,
    "batch_size": 1,
    "integration_status": "scaffold_only"
  },
  "started_at": "...",
  "finished_at": "...",
  "duration_seconds": 0.012
}
```

### Persistence rules
- `persist_eval_result(...)` creates missing parent directories.
- The file is written as UTF-8 JSON with `indent=2` and `ensure_ascii=False`.
- The function returns the final `Path`.

## Boundary
This sub-skill does not execute external benchmark harnesses yet. Treat `LMEvalAdapter` as a contract scaffold, not a finished benchmark runner.
