# Embedding Training Troubleshooting

## Schema Detection Fails

Symptoms:

- Dataset construction raises a key error for `self.data_type`.
- Training starts with an unexpected data type.
- Pair-score records are treated like plain pairs.

Likely causes:

- First usable JSONL row does not match the intended schema.
- `pos`, `neg`, or `scores` has the wrong type.
- Raw pair-score data uses singular `score` instead of list-valued `scores`.
- Empty `pos` lists produce no expanded records.

Fix:

- Validate with `scripts/validate_embedding_training_config.py --config ... --data ...`.
- Ensure pair data has `query` and non-empty `pos`.
- Ensure triplet data has `query`, non-empty `pos`, and non-empty `neg`.
- Ensure pair-score data has `query`, non-empty `pos`, and numeric `scores` with the same length as `pos`.

## `neg_nums` Resampling Surprises

Source behavior repeats `neg` entries when `len(neg) < neg_nums`, then samples `neg_nums` values. This is allowed but can lower negative diversity.

Fix:

- Lower `neg_nums` to the minimum available negative count.
- Add more hard negatives per query.
- Use larger `batch_size` for more in-batch negatives if memory allows.

## `scores` vs `score` Mismatch

Raw input should use list-valued `scores`. The dataset expands each positive passage into an internal singular `score` field. Supplying raw singular `score` is not the documented source format and can break schema inference.

Fix:

```json
{"query": "q", "pos": ["doc1", "doc2"], "scores": [0.8, 0.2]}
```

## Teacher Dimension Typo Compatibility

The source parser defines both `teacher_embedding_dim` and a suppressed typo compatibility key `teacher_emebedding_dim`. After loading YAML, it fills `teacher_embedding_dim` from the typo only if the correct key is absent.

Fix:

- Prefer `teacher_embedding_dim` in new configs.
- If maintaining an old config with `teacher_emebedding_dim`, validate that it resolves to a positive integer.
- Do not define both with different values.

## Teacher Memmap Shape Errors

Symptoms:

- `np.memmap` fails to open with requested shape.
- Training reads wrong teacher vectors.
- Distillation loss behaves nonsensically.

Checks:

- Count lines in the text JSONL.
- Confirm byte size equals `line_count * teacher_embedding_dim * 4` for raw float32 memmap.
- Confirm the teacher creation process wrote rows in the same order as the text JSONL.
- Confirm merged teacher files use `teacher1_dim + teacher2_dim`.

Use:

```bash
python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py \
  --config /path/to/distill.yaml \
  --data /path/to/text.jsonl \
  --teacher-embeddings /path/to/teacher.mmap
```

## MRL Dimension Problems

Symptoms:

- Dense layer or slice dimensions are invalid.
- Distillation fails because an MRL dimension exceeds teacher width.
- Retrieval index and query embedding dimensions do not match.

Fix:

- Use a comma-separated integer string such as `"256,512,1024,1536"`.
- Keep every value positive and unique.
- For distillation, keep `max(mrl_dims) <= teacher_embedding_dim`.
- At inference/index time, slice embeddings consistently to the same dimension.

## Model or Tokenizer Downloads Fail

The validator does not download models, but training does. Source model loading uses `SentenceTransformer(..., trust_remote_code=True)` and `AutoTokenizer.from_pretrained(...)`.

Fix:

- Pre-download models in the user environment if network is unavailable during training.
- Use a local model path in `model_name_or_path`.
- Confirm any `trust_remote_code` requirement is acceptable for the user's security policy.
- Match `torch` and CUDA versions before installing the rest of the dependencies.

## Gradient Checkpointing Issues

`gradient_checkpointing: true` calls `model.model.gradient_checkpointing_enable()`. Some model wrappers may not expose that method.

Fix:

- Disable `gradient_checkpointing` for unsupported models.
- Use a model family known to expose the Hugging Face gradient checkpointing method.
- Prefer reducing `batch_size` or increasing `gradient_accumulation_steps` when checkpointing is unavailable.

## Distributed Config Mismatch

Symptoms:

- Accelerate launch hangs or starts fewer/more processes than expected.
- FSDP wrapper class does not match model architecture.
- DeepSpeed config conflicts with batch size or mixed precision.

Fix:

- Match `CUDA_VISIBLE_DEVICES` count to Accelerate `num_processes`.
- Use FSDP for BERT-like models and DeepSpeed ZeRO for LLM-like models as a starting point.
- Adjust FSDP `fsdp_transformer_layer_cls_to_wrap` for non-BERT architectures.
- Run a short foreground smoke launch before using `nohup`.

## WandB or TensorBoard Logging Fails

The parser default and example configs use `log_with: "wandb"`.

Fix:

- Switch to `log_with: "tensorboard"` when Weights & Biases auth/network is unavailable.
- Configure WandB offline mode in the user environment if needed.
- Keep `log_interval` positive.
- Ensure `output_dir` is writable because Accelerate stores run files there.

## Validation Helper Import Errors

The validator uses the Python standard library plus optional `yaml` and `numpy`.

Fix:

- Install PyYAML for YAML parsing, or run in the same environment intended for training.
- Install NumPy only when validating teacher array shape.
- The helper intentionally avoids importing torch, transformers, sentence-transformers, or RAG-Retrieval modules.
