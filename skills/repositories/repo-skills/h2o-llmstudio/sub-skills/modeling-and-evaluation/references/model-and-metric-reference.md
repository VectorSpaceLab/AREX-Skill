# Model and metric reference

This reference summarizes H2O LLM Studio's modeling layer for the five supported problem types. Import paths are runtime Python paths; they are not links to construction-time source files.

## Common contracts

- Each problem type exposes a `ConfigProblemBase` in `llm_studio.python_configs.<problem_type>_config`.
- Each model wrapper is named `Model` and accepts `Model(cfg)`.
- Installed API signatures verified for the wrappers:
  - Causal LM: `forward(self, batch: dict, padding: bool = True) -> dict`; `generate(self, batch: dict, cfg: Any, streamer=None)`.
  - Classification: `forward(self, batch: dict, padding: bool = True) -> dict`.
  - Regression: `forward(self, batch: dict, padding: bool = True) -> dict`.
  - DPO: `forward(self, batch: dict, padding: bool = True) -> dict`; `generate(self, batch: dict, cfg: Any, streamer=None)`.
  - Sequence-to-sequence: `forward(self, batch: dict, padding: bool = True) -> dict`; `generate(self, batch: dict, cfg: Any, streamer=None)`.
- `forward()` returns a dictionary. During training it must include `loss` when labels are present. During validation it can include metric-specific tensors such as `perplexity`, classification `logits`, regression `predictions`, and DPO `additional_log_*` values.
- Generation wrappers call the shared `generate(backbone, batch, cfg, streamer, remove_prompt=...)` helper. That helper pads `prompt_input_ids` and `prompt_attention_mask`, applies tokenizer stop-word criteria plus the `STOP_STREAMING` environment stop switch, uses the backbone generation config, and removes prompt tokens for causal LM/DPO but not for sequence-to-sequence.

## Problem type map

| Problem type | Config class | Model wrapper | Backbone family | Generation? | Dataset/result posture |
|---|---|---|---|---:|---|
| `text_causal_language_modeling` | `llm_studio.python_configs.text_causal_language_modeling_config.ConfigProblemBase` | `llm_studio.src.models.text_causal_language_modeling_model.Model` | `transformers.AutoModelForCausalLM` | Yes, except `Perplexity` eval | Uses prompt/answer conversation chains. Generated answer ids become `predicted_text`; `target_text` comes from answers. |
| `text_sequence_to_sequence_modeling` | `llm_studio.python_configs.text_sequence_to_sequence_modeling_config.ConfigProblemBase` | `llm_studio.src.models.text_sequence_to_sequence_modeling_model.Model` | `transformers.AutoModelForSeq2SeqLM` | Yes, except `Perplexity` eval | Uses separate prompt and answer token tensors; generation keeps the generated sequence without removing a causal prompt prefix. |
| `text_dpo_modeling` | `llm_studio.python_configs.text_dpo_modeling_config.ConfigProblemBase` | `llm_studio.src.models.text_dpo_modeling_model.Model` | `transformers.AutoModelForCausalLM` | Yes, except `Perplexity` eval | Uses chosen/rejected answer tensors. DPO generation is intentionally equivalent to causal LM generation for the same prompt/backbone. |
| `text_causal_classification_modeling` | `llm_studio.python_configs.text_causal_classification_modeling_config.ConfigProblemBase` | `llm_studio.src.models.text_causal_classification_modeling_model.Model` | `transformers.AutoModelForCausalLM` plus a linear classification head | No | Forward-only. Postprocesses logits into probabilities, predictions, and probability-string `predicted_text`. |
| `text_causal_regression_modeling` | `llm_studio.python_configs.text_causal_regression_modeling_config.ConfigProblemBase` | `llm_studio.src.models.text_causal_regression_modeling_model.Model` | `transformers.AutoModelForCausalLM` plus a linear regression head | No | Forward-only. Postprocesses regression outputs into numeric predictions and comma-joined `predicted_text`. |

## Forward behavior by problem type

### Causal language modeling

- Creates a causal LM backbone with `create_nlp_backbone(..., model_class=AutoModelForCausalLM)`.
- If LoRA is enabled, wraps the backbone with PEFT LoRA/DoRA/RSLoRA support.
- Pads `input_ids`, `attention_mask`, `special_tokens_mask`, and `labels` using the tokenizer padding side.
- Calls the shared causal `forward(backbone, input_ids, attention_mask)` helper, which tries `position_ids` and falls back if the backbone does not accept them.
- With labels, computes the configured cross-entropy loss.
- In eval mode with metric `Perplexity`, adds per-sample `perplexity` values.

### Sequence-to-sequence modeling

- Creates a seq2seq backbone with `AutoModelForSeq2SeqLM`.
- Pads prompt tensors separately from answer tensors; answer padding is right-sided.
- Replaces answer labels where `answer_attention_mask == 0` with `-100` before passing `labels=` to the backbone.
- Uses the backbone's own `output.loss` and can add per-sample `perplexity` in eval mode.
- Calls generation with `remove_prompt=False` because the generated sequence is not a causal continuation of the prompt tensor.

### DPO modeling

- Creates a causal LM backbone and the configured preference loss.
- Losses that require a reference model create a frozen reference backbone unless LoRA without unfreezing allows reference scores through `disable_adapter()`.
- For each batch, forwards both `chosen` and `rejected` tensors, computes label log probabilities with `get_batch_logps`, then calls the configured DPO-family loss.
- Adds training/validation log fields: chosen and rejected rewards, reward margin, chosen/rejected cross-entropy, and for `Perplexity` validation also chosen/rejected perplexity.
- DPO forward is intentionally slower than plain causal LM because it evaluates chosen/rejected policy scores and, for reference-model losses, chosen/rejected reference scores.

### Causal classification

- Creates a causal LM backbone, then applies `nn.Linear(vocab_size, cfg.dataset.num_classes, bias=False)` to the final token hidden/logit representation.
- Pads `prompt_input_ids`, `prompt_attention_mask`, `special_tokens_mask`, and `labels`.
- Computes loss against `batch["class_label"].float()`; cross-entropy loss reshapes labels to long integers, binary cross-entropy uses logits and labels directly.
- Returns `logits` for postprocessing. Dataset postprocessing produces:
  - `probabilities` via softmax for `CrossEntropyLoss`;
  - `probabilities` via sigmoid for `BinaryCrossEntropyLoss`;
  - `predictions` via argmax, threshold `> 0.5`, or multi-label thresholding as appropriate.

### Causal regression

- Creates a causal LM backbone, then applies `nn.Linear(vocab_size, len(cfg.dataset.answer_column), bias=False)` to the final token representation.
- Pads the same prompt-side keys as classification.
- Computes configured regression loss against `batch["class_label"].float()`.
- Returns `predictions`, which dataset postprocessing formats into comma-joined rounded strings for display/output.

## Loss factories

| Problem type family | Factory import | Supported names | Default/fallback | Notes |
|---|---|---|---|---|
| Causal LM and sequence-to-sequence | `llm_studio.src.losses.text_causal_language_modeling_losses.Losses` | `TokenAveragedCrossEntropy`, `SampleAveragedCrossEntropy` | `TokenAveragedCrossEntropy` | Both shift logits left and labels right for next-token prediction; sample-averaged loss averages per sample. |
| Classification | `llm_studio.src.losses.text_causal_classification_modeling_losses.Losses` | `CrossEntropyLoss`, `BinaryCrossEntropyLoss` | `CrossEntropyLoss` | Cross entropy is for single-label binary/multiclass; BCE-with-logits is for binary or multi-label style targets. |
| Regression | `llm_studio.src.losses.text_causal_regression_modeling_losses.Losses` | `MSELoss`, `MAELoss` | `MSELoss` | MSE uses `nn.MSELoss`; MAE uses `nn.L1Loss`. |
| DPO | `llm_studio.src.losses.text_dpo_modeling_losses.Losses` | `DPOLoss`, `DPOHingeLoss`, `DPOIPOLoss`, `KTOPairLoss`, `CPOLoss`, `SimPOLoss` | `DPOLoss` | DPO, hinge, IPO, and KTO require reference scores; CPO and SimPO do not. Some losses average log probabilities before preference loss. |

## Metric factories and result keys

| Metric family | Factory import | Names | Direction | Reduce | Required result keys |
|---|---|---|---|---|---|
| Generative LM | `llm_studio.src.metrics.text_causal_language_modeling_metrics.Metrics` | `BLEU`, `GPT`, `Perplexity` | BLEU/GPT max; Perplexity min | mean | BLEU/GPT require `predicted_text` and `target_text`; GPT also uses validation text; Perplexity requires `perplexity`. |
| Classification | `llm_studio.src.metrics.text_causal_classification_modeling_metrics.Metrics` | `AUC`, `Accuracy`, `LogLoss` | AUC/Accuracy max; LogLoss min | mean | Accuracy uses `predictions` and comma-split `target_text`; AUC uses `logits` and `target_text`; LogLoss uses `probabilities` and `target_text`. |
| Regression | `llm_studio.src.metrics.text_causal_regression_modeling_metrics.Metrics` | `MAE`, `MSE` | both min | mean | Both use numeric `predictions` and comma-split numeric `target_text`. |

Metric factories return a tuple `(metric_function, maximize_or_minimize, reduce)`. Unknown metric names fall back to each factory's default (`BLEU`, `LogLoss`, or `MSE`), so validate spelling before interpreting a score.

## Plot classes and files

- Causal LM plots write batch visualization data to `batch_viz.parquet` and validation visualization data to `<mode>_viz.parquet` under the configured output directory.
- Validation plots include input text, target text, predicted text when available, the selected metric per sample when available, and GPT explanations when the GPT metric runs with raw explanations.
- Large validation tables are downsampled for rendering: metric-bearing tables keep the lowest 300, a random middle 300, and highest 300 after sorting by metric; otherwise up to 900 rows are sampled.
- Classification reuses the language-model validation plot but has a classification-specific batch plot that tokenizes `prompt_input_ids`.
- DPO plots visualize chosen/rejected answers in data views and reuse language-model validation prediction tables.
