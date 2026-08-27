---
name: model-api
description: "Use XLNet TensorFlow graph APIs, config objects, tokenization
  helpers, checkpoints, losses, optimizers, and runtime helpers directly."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model API

Use this sub-skill for direct XLNet model work: graph construction, config inspection, tokenization, checkpoint initialization, optimizer setup, and diagnosis of API/runtime failures.

## Route Here

- Inspect or create `XLNetConfig`, `RunConfig`, and `XLNetModel`.
- Decide whether a custom head should consume `get_pooled_out()` or `get_sequence_output()`.
- Use `modeling.transformer_xl`, `modeling.lm_loss`, or `modeling.summarize_sequence` for custom graph work.
- Attach `function_builder` losses for classification, regression, SQuAD-style QA, or RACE-style multiple choice.
- Set up checkpoint loading, training ops, TPU config, or multi-GPU gradient handling.
- Normalize text and turn it into SentencePiece pieces or ids with `prepro_utils`.

## Reroute Elsewhere

- Downstream task CLIs belong in the task-specific sub-skills for classification, SQuAD QA, or RACE.
- Corpus TFRecord generation and pretraining loops belong in data-pretraining.
- If your task is mostly command assembly rather than graph/API work, do not stay in model-api.

## Fast Workflow

1. Run `scripts/inspect_xlnet_config.py <xlnet_config.json>` first. The config must define `n_layer`, `d_model`, `n_head`, `d_head`, `d_inner`, `ff_activation`, `untie_r`, and `n_token`.
2. Load `XLNetConfig` and `RunConfig` from the JSON or flags. Keep `input_ids`, `seg_ids`, and `input_mask` in `[len, bsz]` order when calling `XLNetModel`.
3. Pick the right output:
   - `get_pooled_out()` for a single vector per example.
   - `get_sequence_output()` for token-level or span-level heads.
   - `get_new_memory()` when you need streaming memory.
   - `get_embedding_table()` when you need tied embeddings or LM projection.
4. Build task heads with the shared initializer from `get_initializer()` and then apply `classification_loss`, `regression_loss`, `get_qa_outputs`, `get_race_loss`, or `lm_loss` as appropriate.
5. For runtime wiring, call `model_utils.init_from_checkpoint()` before the first session run and `model_utils.get_train_op()` after the loss is defined. Use `gpu_utils` only when you need manual tower placement or gradient averaging.
6. Preprocess raw text with `prepro_utils.preprocess_text()` before `encode_pieces()` or `encode_ids()`, and make sure the SentencePiece model from the release zip is available.

## References

- `references/api-reference.md`
- `references/checkpoints-and-runtime.md`
- `references/troubleshooting.md`
- `scripts/inspect_xlnet_config.py`
