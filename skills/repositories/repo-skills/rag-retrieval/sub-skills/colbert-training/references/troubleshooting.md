# ColBERT Training Troubleshooting

## `colbert_dim` Mismatch

Symptoms:

- Loading `colbert_linear.pt` fails with a size mismatch.
- A `BAAI/bge-m3` fine-tune was launched with `--colbert_dim 768` and later scoring expects `1024`.
- Scores look inconsistent after loading a checkpoint with a different dimension than training.

Fix:

- Use the same `colbert_dim` for training and loading.
- Prefer `1024` for `BAAI/bge-m3` ColBERT-style fine-tuning.
- Use `768` for the README-style BERT example unless intentionally choosing a different projection size.
- Re-train or discard incompatible `colbert_linear.pt` weights if the projection dimension changed.

## Too Few Negatives

Symptoms:

- Many rows have fewer negatives than `--neg_nums`.
- Training runs but hard-negative diversity is poor.
- Validation helper warns that rows will resample negatives.

Behavior:

- The dataset repeats a row’s `neg` list enough times and samples `neg_nums` items from the repeated pool.
- Empty `neg` lists are invalid and should be fixed before training.

Fix:

- Lower `--neg_nums` to fit the data distribution, or mine/add more hard negatives.
- Treat resampling as a stopgap, not a replacement for diverse negatives.

## Model or Tokenizer Downloads

Symptoms:

- `AutoModel.from_pretrained` or `AutoTokenizer.from_pretrained` fails.
- A launch hangs or fails before training begins.

Fix:

- Confirm the model id is reachable or provide a local Hugging Face-compatible checkpoint directory.
- Pre-download models in the target environment if network access is restricted.
- Keep the validator in the preflight path; it does not download models and can separate data issues from model availability issues.

## FSDP Config and GPU Counts

Symptoms:

- FSDP wrapping errors mention an unexpected transformer layer class.
- Training launches with a different number of processes than visible GPUs.
- Multi-GPU launch hangs at startup.

Fix:

- Use a `BertLayer` wrapping config for BERT-style backbones.
- Use an `XLMRobertaLayer` wrapping config for `BAAI/bge-m3`/XLM-RoBERTa-style backbones.
- Match `num_processes` to the number of GPU ids in `CUDA_VISIBLE_DEVICES`.
- Start with a single-node, small-data smoke run before a full multi-GPU launch.

## CUDA Memory Pressure

Symptoms:

- CUDA out-of-memory during forward/backward.
- Memory failure appears after increasing `neg_nums`, `passage_max_len`, or batch size.

Fix:

- Reduce `--batch_size` first.
- Increase `--gradient_accumulation_steps` if the user needs a larger effective batch.
- Reduce `--passage_max_len` or chunk long passages upstream.
- Reduce `--neg_nums` only after considering hard-negative diversity.
- Verify mixed precision settings are compatible with the hardware and accelerate config.

## Saved Model Loading

Symptoms:

- The final model directory lacks `colbert_linear.pt`.
- `ColBERT.from_pretrained` loads the base model but not the projection weights.
- The tokenizer path is missing or inconsistent.

Fix:

- Load from `output_dir/model`, not only from an epoch checkpoint unless that checkpoint includes both transformer files and `colbert_linear.pt`.
- Pass the exact `colbert_dim` used during training.
- Keep tokenizer files with the saved model directory.
- Use the bundled/source-code `rag_retrieval.train.colbert.model.ColBERT` scoring path for saved checkpoints.

## Packaged `Reranker` ColBERT Limitation

Symptoms:

- `Reranker("BAAI/bge-m3", model_type="colbert")` prints a missing dependency message or returns `None`.
- The public model mapping mentions `colbert`, but `AVAILABLE_RANKERS` does not include `ColBERTRanker`.
- A `colbert_ranker.py` file exists but is not registered or is only a placeholder in the current package.

Fix:

- Do not present installed package ColBERT inference as supported.
- Use the bundled/source-code `ColBERT.from_pretrained` scoring workflow for trained checkpoints.
- If packaged inference is required, implement and register a real `ColBERTRanker` first, then verify it with the repo’s inference tests and the saved checkpoint format.
