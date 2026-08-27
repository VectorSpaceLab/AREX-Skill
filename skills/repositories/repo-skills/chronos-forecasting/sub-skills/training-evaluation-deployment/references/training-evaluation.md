# Training, evaluation, and fine-tuning

## Scope
This reference covers the Chronos-2 `fit()` path, original training script/config concepts, KernelSynth synthetic data generation, `fev` evaluation, and relative score aggregation.

If you only need forecasting or DataFrame schema details, switch to the sibling sub-skills instead of using this one as a general API reference.

## Chronos-2 fine-tuning

### `Chronos2Pipeline.fit(...)`

Core signature shape:

```python
fit(
    inputs,
    prediction_length,
    validation_inputs=None,
    finetune_mode="full",
    lora_config=None,
    context_length=None,
    learning_rate=1e-6,
    num_steps=1000,
    batch_size=256,
    output_dir=None,
    min_past=None,
    finetuned_ckpt_name="finetuned-ckpt",
    callbacks=None,
    remove_printer_callback=False,
    disable_data_parallel=True,
    **extra_trainer_kwargs,
)
```

### What it accepts
- `inputs` and `validation_inputs` use the same data shapes as Chronos-2 prediction.
- For covariate-aware fine-tuning, prefer the preprocessing helpers that build prepared inputs for you.
  - Long-format DataFrames: `from_data_frame(...)`
  - Per-series dicts: `from_list_of_dicts(...)`
- The model is copied before training, so the original pipeline stays unchanged.
- The returned pipeline is the fine-tuned copy.

### LoRA vs full fine-tuning
- `finetune_mode="full"` trains all weights.
- `finetune_mode="lora"` enables parameter-efficient fine-tuning through `peft`.
- When `peft` is not installed, the implementation warns and falls back to full fine-tuning.
- Default LoRA config uses a small rank and targets the attention/output patch modules.
- For tiny data, LoRA usually pairs well with a higher learning rate than the default, often around `1e-5`.

### Small-data guidance
Use this pattern when you want a fast, low-risk smoke fine-tune:
- keep `num_steps` very small first, then scale up only if the smoke passes
- keep `batch_size` small enough to fit the model and the covariates
- set `min_past` no lower than the task horizon; the default is `prediction_length`
- add `validation_inputs` only when you need model selection, because it adds overhead
- use `output_dir` explicitly so the final checkpoint is easy to find
- if you need a minimal demo, train on a tiny synthetic set rather than a benchmark corpus

### Important behaviors
- `context_length` defaults to the model’s own context length when omitted.
- `min_past` defaults to `prediction_length` when omitted.
- `finetuned_ckpt_name` controls the saved subdirectory inside `output_dir`.
- `remove_printer_callback=True` silences the default printer callback.
- `disable_data_parallel=True` forces a single-GPU path when CUDA is present.
- The returned checkpoint is also made saveable with `save_pretrained(...)`.

### Save/load notes
- `save_pretrained(...)` delegates to the underlying model and can write a local checkpoint or Hub artifact.
- `from_pretrained(...)` can reopen LoRA adapter directories when `peft` is installed.
- S3 loading is for base models; keep LoRA-on-S3 as unsupported/reference-only.

### `predict_fev(...)`
- Accepts a `fev.Task` and returns `(predictions_per_window, inference_time_s)`.
- `as_univariate=True` ignores covariates and evaluates each target independently.
- `finetune_kwargs` fine-tunes on the first window only, then reuses the resulting pipeline for the rest of the windows.
- Any extra keyword arguments are forwarded to `predict_quantiles(...)`.
- The function auto-raises the batch size to the task's variate count when needed.

### Validation path
When `validation_inputs` is supplied:
- validation is enabled during fine-tuning
- the trainer evaluates every 100 steps
- the best model is loaded at the end
- the final checkpoint is still saved under the configured checkpoint name

## Original training script concepts

The training CLI is designed around hourly GluonTS file datasets and a YAML config.
It is intended for offline training/fine-tuning runs, not for an interactive smoke.

### Main config fields

| Group | Fields |
| --- | --- |
| Data | `training_data_paths`, `probability`, `max_missing_prop`, `shuffle_buffer_length`, `dataloader_num_workers` |
| Forecast shape | `context_length`, `prediction_length`, `min_past`, `num_samples` |
| Optimisation | `max_steps`, `save_steps`, `log_steps`, `per_device_train_batch_size`, `gradient_accumulation_steps`, `learning_rate`, `optim`, `lr_scheduler_type`, `warmup_ratio` |
| Model | `model_id`, `model_type`, `random_init`, `tie_embeddings`, `tokenizer_class`, `tokenizer_kwargs`, `n_tokens`, `n_special_tokens`, `pad_token_id`, `eos_token_id`, `use_eos_token` |
| Runtime | `output_dir`, `tf32`, `torch_compile`, `seed`, `temperature`, `top_k`, `top_p` |

### What the configs mean
- `training_data_paths` is a list of GluonTS arrow datasets.
- `probability` mixes the files during sampling; it defaults to equal weighting if omitted.
- `model_type="causal"` is used by the GPT-style config.
- `model_type="seq2seq"` is used by the T5-style configs.
- `random_init=true` is used for the T5 pretraining-style configs.
- `tie_embeddings=true` is used for the T5 configs.
- The script filters out short or too-missing series before training.

### Training script caveats
- The script sets `FileDataset(..., freq="h")`, so the training data is expected to be hourly in that path.
- Causal models use last-value imputation for missing values.
- `tf32` is only meaningful on Ampere-class CUDA GPUs and is disabled automatically when unsupported.
- The script writes runs under `output/run-N/` and saves the final checkpoint under `checkpoint-final/`.
- Multi-GPU training uses `torchrun`; single-GPU or CPU runs should use ordinary `python`.

### Training launcher policy

The repository evidence includes a maintainer training launcher, but this generated skill does not bundle it because it is large, dev-dependency-heavy, and can start long GPU/distributed jobs. For self-contained agent work, prefer the high-level `Chronos2Pipeline.fit` pattern above or create a new task-specific launcher in the user's workspace with explicit data paths, output directory, device, and budget. If the user is intentionally working inside a source checkout and asks to use the maintainer launcher, first confirm that checkout context, dev dependencies, GPU/runtime budget, and overwrite policy.

## KernelSynth synthetic data

KernelSynth is the offline synthetic-data generator used in the repo’s training examples.
It is a good source of tiny, controllable inputs for smoke tests.

For a new self-contained generator, preserve the source workflow's safe parameters (`num_series`, `max_kernels`, and an explicit output path) and default to tiny counts. Do not generate the repository's paper-scale default unless the user explicitly requests it.

Notes:
- the intended output is a GluonTS-compatible Arrow file such as `kernelsynth-data.arrow`
- it depends on the dev-style stack, including `gluonts`, `joblib`, `scikit-learn`, `tqdm`, and `numpy`
- the default size in the repo is much larger; use a smaller count for quick local checks

## Evaluation workflow

### Evaluation launcher policy

The repository evidence includes a benchmark evaluation launcher and YAML benchmark lists, but this generated skill does not bundle them because they can download datasets/models and run long benchmark sweeps. For self-contained evaluation, use the public `predict_fev` APIs described in the model sub-skills or create a new bounded evaluation script in the user's workspace. Preserve these source-evidenced parameter concepts when recreating a launcher:

### Parameters to remember
- `config_path` selects the YAML benchmark list.
- `metrics_path` is the output CSV.
- `model_id`/`--chronos-model-id` can be a Hugging Face ID or a local path.
- `device` and `torch_dtype` control inference placement and precision.
- `batch_size` is per inference batch, not per target variate.
- Chronos uses `num_samples`, `temperature`, `top_k`, and `top_p`.
- Chronos-Bolt does not need sampling arguments.
- Chronos-2 adds `cross_learning`.

### Output interpretation
- Evaluation saves per-dataset metrics, then renames `MASE[0.5]` to `MASE` and `mean_weighted_sum_quantile_loss` to `WQL`.
- Lower is better for both metrics.
- Benchmark downloads are network-bound and should be treated as reference-only unless you explicitly want to reproduce the paper setup.

## Relative score aggregation

The repo’s aggregate helper computes the geometric mean of model/baseline ratios after aligning on `dataset`.
That means:
- values below `1.0` are better than the baseline for lower-is-better metrics
- matching dataset names and matching metric columns are required
- the `model` metadata column is ignored before aggregation

Formula shape:

```python
relative = model_df.drop("model", axis="columns") / baseline_df.drop("model", axis="columns")
agg = relative.agg(gmean)
```

### Interpretation tips
- compare like-for-like CSVs only
- if the metric columns differ, fix the upstream evaluation run instead of forcing the ratio
- if the dataset rows differ, re-run or sort/align before aggregating

## Optional dependency matrix

| Package / extra | Used for | Notes |
| --- | --- | --- |
| `peft` | Chronos-2 LoRA loading and fine-tuning | Required for actual LoRA use; otherwise the pipeline falls back to full fine-tuning |
| `fev` | `predict_fev` and benchmark evaluation | Needed for evaluation workflows that bridge into `fev` |
| `boto3` | S3 and AWS-facing flows | Needed for cloud or S3-based deployment references |
| `gluonts[pro]` | training and evaluation CLIs | Part of the repo’s dev-oriented workflow |
| `datasets` | evaluation data loading | Used by the evaluation CLI and `fev` bridge |
| `typer`, `typer-config` | CLI and YAML config support | Used by the training/evaluation scripts |
| `joblib`, `scikit-learn`, `tqdm` | KernelSynth generation | Needed for the synthetic data generator |
| `scipy` | the README snippet’s `gmean` example | The bundled helper can avoid this extra if needed |

## Reference-only boundary
- Do not treat full benchmark reproduction as a smoke test.
- Do not assume network access, AWS credentials, or GPU availability unless the user explicitly provides them.
- For schema and covariate alignment errors, hand off to the data-format sub-skill.
