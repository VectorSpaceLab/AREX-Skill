# Evaluation and Benchmark Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `subject_mapping.json not found` | Running an unadapted script or wrong mapping path. | Use the bundled `scripts/ceval/eval.py`, which defaults to its neighboring `subject_mapping.json`, or pass `--subject_mapping`. |
| `C-Eval val directory not found` | `--data_dir` does not point to a root with `val/`. | Run `python scripts/validate_ceval_layout.py --data-dir <ceval-root>` before evaluation. |
| Missing `dev`, `val`, or `test` files | Incomplete C-Eval download/extraction or wrong subject names. | Fix the data layout; do not run scoring with partial subjects unless intentionally doing a subset and documenting it. |
| CSV missing `question`, `A`, `B`, `C`, `D`, or `answer` | Wrong dataset format or preprocessing changed headers. | Restore the C-Eval CSV schema. Test files may omit `answer`; dev/val should include it. |
| `--model_path` load failure | Model path is not a HF-format loadable model, or only a LoRA adapter was provided. | Route to model reconstruction or provide base+merged HF model. The C-Eval script expects a direct model path. |
| CUDA out of memory | Model size too large or too many processes/other allocations. | Use a smaller model, free GPU memory, or adjust environment. C-Eval generation for 7B+ models is not a CPU-equivalent quick check. |
| `pandas`, `numpy`, `tqdm`, `torch`, or `transformers` missing | Evaluation dependencies missing. | Install the required evaluation/runtime packages in the approved environment. |
| Scores vary between runs | Sampling randomness or non-constrained decoding. | Use `--constrained_decoding True` for A-D next-token scoring and record decoding settings. |
| Answers become random-looking | Non-constrained regex extraction failed and fell back to a random A-D choice. | Prefer constrained decoding or inspect prompts/responses for answer format issues. |
| `--do_test True` produces no accuracy | Test split has no public answers. | Treat `submission.json` as prediction output; use val split for measured accuracy. |
| Example benchmark scores are treated as absolute accuracy | Misinterpretation of paired score tables. | Use `example-benchmarks.md`: report them as comparative prompt-set demonstrations. |
| User wants a public leaderboard claim | Current environment lacks benchmark controls or official submission. | State limitations and recommend a controlled, documented evaluation run with fixed model, dataset, decoding, hardware, and seed policy. |

## Safe Evaluation Checklist

1. Validate C-Eval data layout and columns.
2. Confirm model is HF-loadable and matches tokenizer/model family.
3. Record zero/few-shot, `ntrain`, prompt wrapping, constrained decoding, temperature, and output directory.
4. Run a very small subject subset first if possible.
5. Report skipped/failed subjects separately from measured accuracy.
