# Troubleshooting

## Missing T5 cache
**Symptoms**
- File-not-found or cache download errors from `language/t5.py` or `extract_t5_feature.py`.

**Likely causes**
- Wrong `--t5-feat-path` or `--t5-path`.
- Cache directory was never populated.
- Wrong `--t5-model-type`.

**Recovery**
- Re-run `data-preparation` for the stage you need.
- Verify the cache tree before launching training or sampling.

## Left-padding confusion
**Symptoms**
- Sampling gives unexpected conditioning behavior or prompt layout mismatch.

**Likely causes**
- The prompt embeddings were rearranged for the default left-padding flow.
- `--no-left-padding` was set when the downstream recipe expected the default.

**Recovery**
- Match the flag to the recipe.
- Compare the prompt tensor layout against the workflow notes in `references/t5.md`.

## Prompt file problems
**Symptoms**
- `KeyError`, `pandas` parsing errors, or strange sampling batches.

**Likely causes**
- The prompt file is missing the `Prompt` column.
- The wrong delimiter was used for COCO vs Parti.

**Recovery**
- Use the bundled prompt files as the layout reference.
- Check the file with a tiny slice before running a large sample job.

## Checkpoint format mismatches
**Symptoms**
- `load_state_dict` failures or unexpected missing keys.

**Likely causes**
- The checkpoint is from DDP, FSDP, or a different model family.
- `--from-fsdp` was omitted for raw FSDP weights.

**Recovery**
- Confirm whether the checkpoint contains `model`, `module`, `state_dict`, or raw FSDP shards.
- Use the matching wrapper and model family.

## Evaluation dependency drift
**Symptoms**
- TensorFlow / CLIP / clean-fid import problems during t2i evaluation.

**Likely causes**
- Missing evaluation dependencies.
- The environment was created for training only.

**Recovery**
- Use the verified environment check script before evaluation.
- Install the evaluation dependencies that the selected run actually needs.

## Bad sample directory layout
**Symptoms**
- Evaluation cannot find images or captions.

**Likely causes**
- The DDP sampler was not allowed to finish.
- `images/`, `result.jsonl`, or `captions.txt` is missing.

**Recovery**
- Re-run the sampler or package the batch again.
- Ensure the evaluator receives the directory, not an individual image file.
