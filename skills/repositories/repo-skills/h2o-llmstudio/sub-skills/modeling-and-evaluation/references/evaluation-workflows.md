# Evaluation workflows

This reference covers the runtime contracts for inference, validation evaluation, prediction outputs, plots, and AI-judge metrics.

## `run_inference` contract

Runtime signature:

```python
run_inference(cfg, model, dataloader, mode: str) -> dict[str, list]
```

Behavior:

1. Iterates through the supplied dataloader in eval/inference context and moves batches to `cfg.environment._device` through the configured dataset class.
2. Chooses generation or forward-only inference:
   - If `cfg.prediction.metric != "Perplexity"` and `cfg.problem_type` is not a non-generation problem type, it calls `model.generate(...)` and stores `predicted_answer_ids`.
   - Otherwise it calls `model.forward(batch)`.
   - Non-generation problem types are classification and regression.
3. Uses mixed-precision autocast when configured and not managed by DeepSpeed.
4. Raises a model exception if NaNs are detected during mixed-precision inference.
5. Calls `dataloader.dataset.postprocess_batch_predictions(output)` for per-batch decoding or cleanup.
6. Concatenates batch outputs into one output dictionary.

Practical implications:

- `Perplexity` validation never generates text. It uses a forward pass, and model/dataset code supplies `perplexity` and `target_text` for metric computation.
- Classification and regression requests should not ask for generated natural-language answers. They use logits/regression outputs that are postprocessed into predictions and display strings.
- Generative BLEU/GPT validation requires decodable generated tokens. If generation is not selected, validation tables may show that no predictions were generated for the selected metric.

## `run_eval` contract

Runtime signature:

```python
run_eval(cfg, model, val_dataloader, val_df, mode="validation") -> tuple
```

Behavior on the main rank:

1. Temporarily switches the model to eval mode and calls `run_inference` under `torch.no_grad()`.
2. Truncates synced validation outputs to the validation dataset length.
3. Calls `val_dataloader.dataset.postprocess_output(cfg, val_df, val_data)` to compute target text and metric values.
4. Computes mean validation loss from `loss` if present.
5. Computes and logs mean metric value from `val_data["metrics"]`.
6. Logs `loss` and any keys beginning with `additional_log_`; DPO uses this for rewards, reward margin, and chosen/rejected losses/perplexity.
7. Builds a validation prediction plot through `cfg.logging.plots_class.plot_validation_predictions(...)`.
8. Saves prediction artifacts through `save_predictions(...)`.

Return value:

- Main rank returns `(val_loss, val_metric)`.
- Non-main distributed ranks return `(0, 0)` after synced output handoff.

## Prediction artifacts

Successful evaluation writes these mode-specific files under the configured experiment output directory:

- `<mode>_raw_predictions.pkl`: raw postprocessed validation output dictionary with heavy fields such as tensors converted through the save helper.
- `<mode>_predictions.csv`: validation dataframe with prediction columns when available.
- `<mode>_viz.parquet`: table used for validation visualization.
- `batch_viz.parquet`: table used for first-batch training data visualization when training reaches the first batch.

At the end of a successful run, the training workflow also saves the final config and consolidates prediction outputs for the experiment. Model checkpoint files are managed by the training workflow, not by evaluation metrics.

## Generation routing examples

### Causal LM with BLEU

- `problem_type = text_causal_language_modeling`
- `metric = BLEU`
- Route: `generate(...)` -> decode `predicted_text` -> compare to `target_text` with sentence BLEU.

### Causal LM with Perplexity

- `problem_type = text_causal_language_modeling`
- `metric = Perplexity`
- Route: `forward(...)` -> per-sample `perplexity` tensor -> mean-reduced metric.

### DPO with Perplexity

- `problem_type = text_dpo_modeling`
- `metric = Perplexity`
- Route: `forward(...)` over chosen/rejected answers -> chosen perplexity as primary metric plus rejected perplexity and reward diagnostics in `additional_log_*` fields.

### Classification with Accuracy/AUC/LogLoss

- `problem_type = text_causal_classification_modeling`
- Any classification metric
- Route: `forward(...)` only -> logits -> probabilities and predictions -> metric.
- Do not request `generate()` for classification; the model wrapper does not expose generation as part of its installed API contract.

### Regression with MAE/MSE

- `problem_type = text_causal_regression_modeling`
- Any regression metric
- Route: `forward(...)` only -> regression head predictions -> metric.

## Metric-specific behavior

### BLEU

- Inputs: `results["predicted_text"]`, `results["target_text"]`.
- Validates equal lengths and non-empty data.
- Computes sentence BLEU using effective order.
- Empty target text produces score `0.0` for that sample.
- Direction is maximize; reduction is mean.

### GPT judge

- Inputs: validation prompts, `predicted_text`, `target_text`, selected GPT model, selected GPT prompt template.
- Uses an OpenAI-compatible Chat Completions client.
- Environment knobs:
  - `OPENAI_API_BASE`: endpoint base URL for OpenAI-compatible local or remote endpoints.
  - `OPENAI_API_KEY`: credential.
  - `OPENAI_API_TYPE=azure`: switch to Azure client.
  - `OPENAI_API_DEPLOYMENT_ID`: Azure deployment name.
  - `OPENAI_API_VERSION`: Azure API version; default is `2023-05-15`.
  - `LLM_RETRY_ATTEMPTS`: retry count; default is `3`.
  - `LLM_TIMEOUT`: request timeout in seconds; default is `60`.
  - `GPT_EVAL_MAX`: safety cap used before training/evaluation; if validation rows exceed the cap and metric contains `GPT`, the training workflow warns and changes the metric to `BLEU`.
- The judge prompt asks for two output lines: `EXPLANATION: ...` and `SCORE: ...`.
- Score parsing expects a parseable number after the literal `SCORE:`.
- API failures are caught per sample and return score `0.0` with an empty explanation.
- GPT evaluation parallelizes calls with eight multiprocessing workers, so endpoint rate limits and credential budgets matter.

Do not run GPT judge evaluation until the user has approved network/API use and any expected cost. For local LLM judges, require an OpenAI-compatible Chat Completions endpoint.

### MT-Bench prompt template behavior

When the GPT template name is `mt-bench`:

- The default prompt template evaluates helpfulness, relevance, accuracy, depth, creativity, and detail on a 1-to-10 scale.
- Rows whose validation dataframe category is one of `math`, `reasoning`, or `coding` use a reference-answer template instead of the general template. That template compares the assistant answer with the reference answer before scoring.
- After scoring, category means are logged.
- Required formatting remains `EXPLANATION: ...` and `SCORE: ...`; malformed responses are treated as score-parse failures.

### Classification metrics

- `Accuracy` expects `predictions` shaped like target labels and returns one score per sample.
- `AUC` expects `logits` and target labels. For multiclass targets, one-hot target expansion is used when needed and `roc_auc_score(..., multi_class="ovr")` is applied.
- `LogLoss` expects `probabilities` and target labels. Multi-label log loss is computed per answer column and averaged.

### Regression metrics

- `MSE` and `MAE` parse comma-separated target strings into floats and compare them with numeric prediction arrays.
- Multi-output regression computes per-row mean error across output columns.

## Plot interpretation

Validation plot rows contain:

- input text assembled from system, prompt, and prior answer context;
- target text;
- predicted text when generation or postprocessing produced it;
- per-sample metric values when metric output is vector-valued;
- GPT explanations when GPT evaluation returns raw explanations.

If a metric produces only a scalar mean, there may be no per-row metric column. If generation was not selected, predicted text can be absent or replaced by a no-prediction message.

## Safe synthetic checks

- Route a classification metric request: inspect `text_causal_classification_modeling` and verify that supported metrics are `AUC`, `Accuracy`, and `LogLoss`, all forward-only.
- Inspect every problem type with `--verify-imports` to confirm class importability without instantiating a model or touching model weights.
