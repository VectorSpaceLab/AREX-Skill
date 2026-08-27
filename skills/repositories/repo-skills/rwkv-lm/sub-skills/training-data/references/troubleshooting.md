# Training and data troubleshooting

## `AssertionError` in dataset initialization

Likely causes:

- `--data_file` points to a prefix without both `.bin` and `.idx` files.
- `--ctx_len` changed but `--magic_prime` was copied from an older run.
- `magic_prime` is not prime or is not congruent to `2 mod 3`.
- The token count is too small for the requested context length.

Recovery:

1. Run the bundled magic-prime helper on the exact prefix and context length.
2. Confirm `magic_prime / (token_count // ctx_len)` is close to but not above 1.
3. Re-run a tiny data read before restarting the trainer.

## Training resumes from the wrong checkpoint

The trainer searches `proj_dir` for `rwkv-*.pth` and uses the largest numeric
suffix or `rwkv-init.pth` when appropriate. A stale or corrupt high-numbered
file can hijack a resume.

Recovery:

- List `rwkv-*.pth` sorted by suffix and compare timestamps to `train_log.txt`.
- Move stale checkpoints to a quarantine directory outside `proj_dir`.
- Verify the startup line `### Loading <path>... ###` before spending GPU time.
- Do not copy the repository launcher's `rm` commands blindly; they are examples,
  not a safe general cleanup policy.

## CUDA extension build fails

Symptoms include missing `CUDA_HOME`, `nvcc not found`, `no kernel image is
available`, `undefined symbol`, or failures inside `torch.utils.cpp_extension.load`.

Recovery:

- Distinguish PyTorch CUDA runtime from CUDA toolkit. A CUDA tensor allocation
  can pass even when `nvcc` is absent.
- Match the torch CUDA wheel, driver, compute capability, and local toolkit.
- Use the repository's current `cuda/` sources for the selected directory; v5,
  v7 `train_temp`, and v8 toy scripts have different kernels.
- Clear stale files under the configured torch extension cache when a previous
  compile was interrupted.
- If extension compilation is optional for the task, document the limitation and
  use parser/data/reference checks instead of claiming kernel verification.

## Lightning or DeepSpeed argument mismatch

RWKV-v5 and v7 `train_temp` support different stage flag names. The scripts also
branch on PyTorch Lightning version when adding trainer arguments.

Recovery:

- Keep `pytorch-lightning==1.9.5` unless intentionally updating the code path.
- Use `--train_stage` for `RWKV-v7/train_temp/train.py` and `--my_pile_stage`
  for `RWKV-v5/train.py`.
- For a single GPU, reduce DeepSpeed bucket size or use a documented stage-2
  strategy; for consumer GPUs, lower `micro_bsz` first.

## Invalid JSONL or tokenizer roundtrip failure

Symptoms: converter exits on bad JSON, missing `text`, or decode mismatch.

Recovery:

- Remove blank lines only after confirming line numbers.
- Validate every JSON object has a string `text` field.
- Use the same v20230424 vocabulary for encode and decode.
- Normalize or remove invalid Unicode sequences before conversion.

## Loss curve diverges from documented MiniPile run

Check in order:

1. Data prefix and token count match the documented MiniPile files.
2. `ctx_len`, `magic_prime`, `vocab_size`, `n_layer`, and `n_embd` match init and
   training commands.
3. Weight decay and optimizer groups were not simplified.
4. Precision is bf16/tf32 where expected; fp16 can overflow.
5. Resume did not load a stale checkpoint.
