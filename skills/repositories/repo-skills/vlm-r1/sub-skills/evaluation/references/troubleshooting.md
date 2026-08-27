# Evaluation Troubleshooting

Use this guide when REC/OVD evaluation commands fail, saved outputs score unexpectedly, or bbox JSON cannot be parsed. Keep fixes parameterized and self-contained; do not depend on checkout-specific paths.

## Full REC/OVD evaluation does not start

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Checkpoint path is empty or not found | Native recipes used hard-coded model directories. | Replace with a user-supplied `model_dir` and verify the directory has model weights, config, tokenizer/processor files, and any required remote-code files. |
| Annotation file is missing | `data_root` does not contain `{dataset}.json` or dataset names are wrong. | Check dataset names and file suffix; REC eval consumes JSON annotation arrays, while training consumes JSONL. |
| Images are missing | Row `image` is relative and must be joined to `image_root`. | Print a few resolved image paths before generation; route broad data-format issues to `../../data-and-rewards/SKILL.md`. |
| `qwen_vl_utils` import fails | Qwen evaluation requires the Qwen vision utility package. | Install the Qwen-VL utility dependency in the evaluation environment, or use an already prepared VLM-R1 environment. |
| `trust_remote_code`/InternVL load fails | InternVL checkpoints need remote-code model classes and module-specific preparation. | Use the InternVL-specific flow in `evaluation-workflows.md`; do not load InternVL with the Qwen processor path. |

## Distributed REC failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `LOCAL_RANK` missing or all workers use one GPU | Script was launched with plain `python` instead of `torchrun`. | Use `torchrun --nproc_per_node <gpu_count> ...` and derive device from `LOCAL_RANK`. |
| NCCL init timeout | Wrong process count, unavailable GPU, blocked rendezvous, or multi-node address mismatch. | Start with single-node; verify visible GPUs and ports; for multi-node command construction route to `../../training-workflows/SKILL.md`. |
| Gather assertion fails at the end | Rank splitting/gather order was changed or a worker returned fewer outputs than assigned rows. | Preserve `(global_index, output)` pairs and reconstruct by index on rank 0; handle empty shards explicitly for tiny datasets. |
| Only rank 0 has progress | This is expected in the native-style recipe. | Keep non-main ranks quiet unless debugging. |

## CUDA memory and generation issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CUDA OOM during REC/OVD eval | Batch too large, high-resolution images, flash attention unavailable, or too many processes per node. | Reduce `batch_size`, reduce `nproc_per_node`, use bfloat16, enable flash attention only when installed, or cap sample size for a smoke run. |
| Generation is slow or memory spikes | Qwen image processing can create large visual token grids. | Record `input_size` from Qwen `image_grid_thw` and inspect outlier image sizes; consider lower batch size. |
| Output includes the prompt | Generated IDs were decoded without trimming input IDs. | Trim generated IDs with `out_ids[len(in_ids):]` before batch decode. |
| InternVL output is garbled or padded strangely | Tokenizer/model pad token not aligned. | Set tokenizer pad token to EOS when missing and update the model generation config before generation. |

## Bbox extraction problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| REC R1 rows all score zero | Model output lacks `<answer>...</answer>` or final answer is not JSON-like. | Check prompt template and parse only the final answer block; if scoring saved outputs, pass `--prediction-key model_output` to the offline scorer. |
| Baseline rows parse a wrong bbox | Baseline parser accepts the first bracketed four-number list anywhere. | Prefer an adapted parser that looks in the answer text first, or store a clean `extracted_answer` field during generation. |
| InternVL rows need resize but none is applied | The native InternVL recipe scores boxes directly. | Only add resize if your adapted InternVL data pipeline explicitly produces input-coordinate boxes; document the coordinate space. |
| OVD rows with fenced JSON fail | Malformed JSON fence, single quotes, missing list wrapper, or missing `bbox_2d`. | The offline scorer reports row warnings and continues. Fix the row or regenerate with stricter JSON instructions. |
| Labels mismatch in OVD arrays | Multi-object reward-style scoring may require label agreement. | Use `--require-label` in the offline scorer when labels should gate matches; otherwise IoU alone determines matches. |

## Resize and coordinate-space errors

Qwen REC generated text is usually in processor input coordinates. The native recipe resizes parsed predictions to original image coordinates before IoU using `(input_height, input_width)` and `(image_height, image_width)` metadata.

Common mistakes:

- **Double resize**: saved native-style `extracted_answer` may already be in image coordinates. Do not run resize again unless the prediction came from raw text or known input-coordinate fields.
- **Swapped size order**: VLM-R1 saved sizes are `(height, width)`. If another pipeline stores `(width, height)`, use the offline scorer's `--size-order width-height` option.
- **Missing input/image sizes**: raw Qwen text cannot be faithfully resized without both input and original image sizes. The offline scorer will warn and score unresized if `--resize-mode auto` or `on` lacks metadata.
- **Invalid boxes**: zero-area or inverted boxes produce IoU 0. Normalize or filter predictions before reporting accuracy.

## Offline scorer failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No records found` | Input JSON/JSONL is empty or uses an unexpected wrapper. | Use a JSON list, a JSON object with `results`, a single JSON object row, or JSONL with one object per line. |
| Ground truth missing | The scorer did not find `ground_truth`, `solution`, `gt_bbox`, `bbox`, or the specified key. | Pass `--ground-truth-key <field>` or normalize rows before scoring. |
| Predictions missing | The scorer did not find direct bbox fields or text fields such as `model_output`. | Pass `--prediction-key <field>`; for native outputs, `extracted_answer` is usually preferred. |
| Malformed JSONL line | A line is not valid JSON. | The scorer records a row-level parse error and continues; repair the line for final reporting. |
| Accuracy denominator looks wrong | Some rows lacked ground truth and were not scored. | Inspect `summary.scored`, `summary.missing_ground_truth`, and row warnings. |
| OVD multi-box score is stricter than expected | `--strict-extra-boxes` or `--require-label` may be enabled. | Disable strict options for native single-box-style comparisons; enable them only for reward-style multi-object audits. |

## Output-path and schema issues

- Native REC/OVD recipes report `accuracy` as a percentage, not a 0-1 ratio.
- Offline scorer summaries include both `accuracy` (ratio) and `accuracy_percent`.
- Include `model_output` in saved outputs when future parser debugging is likely.
- Include `input_size` and `image_size` for any Qwen REC output that has not already been resized.
- Prefer stable per-row identifiers (`id`, `image`, or `question`) so rank-gather and offline scoring mismatches can be diagnosed.
