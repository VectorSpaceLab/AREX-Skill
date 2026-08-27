# Workflows

## Prerequisites
- Convert Meta's released LLaMA checkpoint to Hugging Face format first.
- Keep the released Alpaca weight diff in a local directory.
- Check the non-commercial license context before using or sharing outputs.
- Use a fresh writable output directory for recovery; `save_pretrained()` writes files there and stale extras can remain in an existing directory.

## Path roles

| role | recover | make_diff | notes |
| --- | --- | --- | --- |
| `path_raw` | input | input | Hugging Face-converted base model directory |
| `path_diff` | input | output | released diff directory, or the output dir for a new diff |
| `path_tuned` | output, optional | input | recovery destination or tuned checkpoint input |

## diff-plus-raw: recover
1. Use `scripts/build_weight_diff_command.py recover ...` to confirm the roles and print a safe dry-run command.
2. If executing, load `path_raw` and `path_diff` on the chosen device in float32 with `low_cpu_mem_usage=True`.
3. If the raw tokenizer has no pad token, resize embeddings before adding weights.
4. Add the diff tensors to the raw tensors.
5. If `check_integrity_naively` is on, sum all recovered tensor values and compare to `50637.1836`.
6. If `path_tuned` is given, save the recovered model/tokenizer there; if it is omitted, recovery stays in memory only.
7. Optionally run a short inference smoke prompt only after the model loads.

## diff-minus-raw: make_diff
1. Use `scripts/build_weight_diff_command.py make_diff ...` for a safe dry-run command.
2. Load the raw checkpoint and tuned checkpoint on the chosen device in float32.
3. If the raw tokenizer has no pad token, resize embeddings before subtracting.
4. Subtract the raw tensors from the tuned tensors.
5. Save the resulting diff model/tokenizer to `path_diff`.

## Dry-run planning
- Omit a path in the command builder to keep a placeholder when you are still planning.
- Use `--strict` when you already have concrete local directories and want the builder to fail on aliasing or obvious local-path mistakes.
- Dry-run mode should never load checkpoints; it only validates roles and prints the shell command you can copy into a real run.

## Device choice
- `cpu`: safest for planning and path inspection.
- `cuda`: faster for actual arithmetic, but only when the checkpoint fits and the device is visible.
- Because the source loads float32 weights, both RAM and VRAM requirements are high.
