# Troubleshooting

## Common failure modes

### A new task or criterion is not being registered

- Make sure the module is imported by `ofa_module/__init__.py` or an equivalent entry point.
- Confirm the decorator name matches the task or criterion you expect.
- Run `scripts/inspect_ofa_registration.py` before assuming the code path is broken.

### A prompt / adapter / bitfit command fails because the flag is wrong

- Re-check the exact flag spelling.
- Avoid copying shell fragments with line-continuation mistakes.
- Validate the command shape with the setup sub-skill before launching a long job.

### A checkpoint load complains about heads or shape mismatch

- Confirm that the checkpoint and the target architecture match.
- Check whether the task needs a classification head or a different dictionary size.
- If the model evolved, do not assume the old checkpoint head layout will still fit.

### Encouraging-loss training becomes unstable

- Lower `--log-end` first.
- Compare the run against the baseline cross-entropy setup.
- Treat larger gradient norms as a real signal, not just noise.

## Recovery order

1. Inspect the registry.
2. Confirm the command flags.
3. Check checkpoint compatibility.
4. Then try the modified run.
