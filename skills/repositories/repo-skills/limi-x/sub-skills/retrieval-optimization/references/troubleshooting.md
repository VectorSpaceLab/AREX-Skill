# Troubleshooting

## OOM or CUDA allocation failure

Likely causes:
- attention-map generation on a large train/test split
- `use_type="mixed"` multiplying sample and feature attention
- clustering over a large top-k set
- too many Optuna trials for the available GPU memory budget

What to try:
- Lower `retrieval_len` or switch from `"dynamic"` to a fixed smaller value.
- Disable `use_cluster` first, then `use_threshold` if needed.
- Prefer `use_type="only_sample"` before attempting mixed attention.
- Reduce `cluster_num`.
- Use the smaller checkpoint family if you have it locally.
- If the task does not require retrieval, switch to a non-retrieval config.

Source behavior to remember:
- The attention code has chunked fallbacks, but the retrieval workflow can still exceed memory.
- Mixed sample+feature subsampling may fall back to CPU for one multiplication step, yet the overall trial can still be too heavy.

## Missing attention score

Symptoms:
- assertions about sample attention or feature attention
- `None` returned from the attention helper when the retrieval path expects a score

Likely causes:
- `subsample_type="sample"` without `calculate_sample_attention=true`
- `use_type="mixed"` without `calculate_feature_attention=true`
- `subsample_type="feature"` without `calculate_feature_attention=true`
- `retrieval_before_preprocessing=true` with the wrong attention flags

What to try:
- Keep sample retrieval aligned with `calculate_sample_attention=true`.
- Enable `calculate_feature_attention=true` only when you truly need mixed or feature retrieval.
- Recheck that `subsample_type` and `use_type` match the attention flags.

Note:
- The search helper accepts an `attention_score` argument, but the current search path does not consume it directly.

## CPU / retrieval mismatch

Symptom:
- retrieval-related error on a CPU device

Cause:
- the predictor explicitly rejects `use_retrieval: true` on CPU.

Fix:
- Use a non-retrieval config when running on CPU.
- Move retrieval runs to CUDA.

## Too many trials or very slow tuning

Cause:
- the default search count is large, and each trial loads the checkpoint and runs inference.

Fix:
- Start with `n_trials=1` to validate the pipeline.
- Move to 5–20 trials for smoke testing.
- Only scale up when the config and GPU budget are stable.

Do not confuse this workflow with benchmark CLI sampling. If you need repeated benchmark-side search-space sampling, use `../benchmark-cli/SKILL.md`.

## Non-retrieval config passed to search

Symptom:
- search runs but retrieval does not seem to change, or the config shape is invalid

Likely causes:
- `retrieval_config` is missing from one or more pipelines
- `use_retrieval` is `false`
- the config list was not deep-copied and got mutated in place across trials

Fix:
- Start from a retrieval-enabled config list.
- Keep one `retrieval_config` per pipeline.
- Deep-copy the list before search.

## Cluster / threshold edge cases

### Cluster count issues
- `cluster_num` is clamped to the number of selected top-k samples.
- If `cluster_num` is larger than the candidate set, it shrinks automatically.

### Threshold issues
- `threshold` should stay in `[0, 1]`.
- A zero-sum row selects one sample.
- `mixed_method="max"` enforces at least `retrieval_len` and caps at 2000.
- `mixed_method="min"` caps at `retrieval_len`.

### Dynamic retrieval issues
- `retrieval_len="dynamic"` depends on `dynamic_ratio`.
- A fixed `retrieval_len` ignores `dynamic_ratio`.
- The search helper does not rewrite `use_dynamic`, so a base config with the wrong flag can make the tuned value ineffective.

## CUDA / flash-attn notes

- The model path prefers flash-attn when CUDA is available and compatible wheels are installed.
- If flash-attn is missing, the code falls back to a standard attention path and chunked fallback logic, but retrieval inference is still GPU-oriented.
- Keep the local checkpoint ready before you start; this skill does not download or validate a model weight by itself.

## When to route away

- Need config generation or schema validation? Use `../configuration-preprocessing/SKILL.md`.
- Need predictor setup, batch shapes, or output handling? Use `../predictor-inference/SKILL.md`.
- Need benchmark dataset loops or search-space sampling flags? Use `../benchmark-cli/SKILL.md`.
