# C-Eval Troubleshooting

- **No files found:** confirm the processed data is under the expected
  `evaluation/CEval/<split>/` tree and that files end in `.jsonl`. Run the
  bundled layout validator with `--root` pointing at the data directory.
- **Missing `inputs_pretokenized`:** the source cannot construct prompts. Fix
  the preprocessing export or map the correct question field before running.
- **Label mismatch:** the source compares an integer prediction index to the
  record label. Normalize `A`–`D` to `0`–`3` explicitly and keep a record of
  the conversion; use `--strict-label-type` to reject non-integer labels when
  matching the original script exactly.
- **Tokenizer/model class failure:** make the model id, tokenizer, revision,
  and `trust_remote_code=True` consistent; verify the full model cache before
  starting a long evaluation.
- **CUDA out of memory:** lower DataLoader batch size, reduce generation/token
  limits, close other GPU processes, or use a supported quantized evaluation
  plan. A CPU-only run is not equivalent for the repository's CUDA BF16
  benchmark.
- **Unexpected score drift:** compare split, prompt construction, model
  revision, label encoding, generation parameters, and per-file denominators;
  the repository itself notes small result variation.
- **Test-set submission uncertainty:** preserve the source's subject/result
  mapping, then follow C-Eval's current official submission format rather than
  inventing a local JSON schema.
