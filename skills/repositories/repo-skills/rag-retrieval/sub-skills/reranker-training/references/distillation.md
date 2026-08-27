# LLM Teacher To BERT Reranker Distillation

RAG-Retrieval includes an example flow for using an LLM reranker teacher to score query-document pairs and then training a smaller BERT reranker on those teacher scores.

## Distillation Shape

The teacher-data input uses query positives and negatives:

```json
{"query": "...", "pos": ["positive passage"], "neg": ["negative passage"]}
```

The teacher scoring step expands every `pos` and `neg` passage into query-document pairs, runs the LLM teacher, and writes pointwise training data:

```json
{"query": "...", "content": "passage", "score": 0.83}
```

When training the BERT student on this output, set the pointwise label key to the teacher-score field:

```yaml
train_dataset: "data/distilled-reranker.jsonl"
train_dataset_type: "pointwise"
train_label_key: "score"
val_dataset_type: "pointwise"
val_label_key: "score"
min_label: 0
max_label: 1
loss_type: "pointwise_mse"
model_type: "bert_encoder"
```

`pointwise_mse` is the safest default for continuous teacher probabilities. `pointwise_bce` can be used for soft-label classification if the score is already bounded in `[0, 1]` and treated as a probability-like target.

## Teacher Scoring Behavior

The example teacher scorer is a generative LLM wrapper that:

- builds a Chinese prompt asking whether passage B contains the answer to query A.
- uses a chat template with a generation prompt.
- generates deterministically with `temperature=0.0` and `do_sample=False`.
- reads the probability of the Chinese token for “yes” as the relevance score.
- writes one output row per expanded query-document pair.

This is a reference pattern, not a mandatory prompt. For another language or domain, adapt the prompt and the positive token while preserving the output contract: `query`, `content`, and a numeric score field.

## Heavy Model Caveats

LLM teacher scoring can be more expensive than BERT student training:

- It may require a large GPU or device mapping strategy.
- It may be slow for large `pos`/`neg` collections because every passage becomes a separate query-document pair.
- Prompt wording, language, and the selected “yes” token strongly affect scores.
- Scores should be inspected for calibration before using them as regression targets.
- Keep teacher scoring separate from the BERT student training run so failures do not corrupt student checkpoints.

Plan a small pilot first: score a few hundred query-document pairs, inspect score distribution by positive/negative source, validate the generated pointwise JSONL, then scale up.

## Expected Inputs And Outputs

Input for teacher scoring:

- JSONL with `query` and optional `pos` / `neg` arrays.
- Teacher checkpoint or model id available in the runtime environment.
- Output path for distilled pointwise JSONL.

Output for BERT training:

- JSONL with `query`, `content`, and a numeric teacher score field.
- A BERT training config using `train_dataset_type: pointwise` and `train_label_key` matching that score field.
- A validation split when possible, preferably with the same score field and held-out queries.

## Safe Planning Checklist

Before running distillation:

- Confirm the teacher model can be loaded in the target environment.
- Decide whether the teacher prompt language matches the training corpus language.
- Decide whether to keep positives and negatives both in the output, or to sample them to balance training.
- Choose `pointwise_mse` for continuous scores unless there is a reason to optimize BCE.
- Validate the output JSONL with the bundled validator using the same `train_label_key` as the student config.
- Compare score histograms for `pos` and `neg` passages to ensure the teacher separates them enough to train a student.

## When To Avoid Distillation

Avoid or postpone LLM-to-BERT distillation when:

- the teacher is not clearly stronger than the target BERT reranker.
- teacher scores collapse into a narrow range for both positives and negatives.
- the corpus language or prompt language do not match.
- runtime memory or cost makes teacher scoring unreliable.
- high-quality human or click labels are already available and sufficient for direct pointwise or grouped training.
