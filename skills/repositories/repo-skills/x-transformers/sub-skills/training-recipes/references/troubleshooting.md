# Training recipe troubleshooting

Use this table before adapting or running native training recipes. The safest recovery is often to switch back to `scripts/copy_task_smoke.py` and verify the base package first.

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| `ModuleNotFoundError: No module named 'x_transformers'` | The package is not installed in the active Python environment. | Install the package in the environment that will run the recipe. Re-run `python -c "import x_transformers"` before launching training. |
| `ModuleNotFoundError` for `accelerate`, `fire`, `wandb`, or `tqdm` | Many recipe scripts depend on extras that are not part of the minimal package install. | Install only the extras needed by the chosen script. For the safe smoke, do not install these; it does not need them. |
| `ModuleNotFoundError` for `lion_pytorch` | `train_parity.py` uses `lion_pytorch.cautious_lion.Lion`. | Install the examples dependency set or install `lion-pytorch` directly, then ensure CUDA behavior is acceptable because the native parity script hard-codes `.cuda()`. |
| `ModuleNotFoundError` for `adam_atan2_pytorch` | `train_with_muon.py` uses `MuonAdamAtan2`. | Install `adam-atan2-pytorch` only if intentionally adapting the Muon optimizer recipe. Keep it reference-only for ordinary smoke tests. |
| `ModuleNotFoundError` for `ema_pytorch` or `x_mlps_pytorch` | `train_self_masked_repr.py` contains self-distillation wrappers that require EMA and MLP helper packages. | Install both packages before importing the script, or avoid this recipe unless you are specifically studying self-masked representation training. |
| `FileNotFoundError: data/enwik8.gz` | The enwik8 recipes expect a local gzip file in the current working directory. | Acquire enwik8 separately from the documented Hutter Prize source, place it at `data/enwik8.gz`, and re-run with tiny batch/length settings first. Do not make enwik8 a prerequisite for the bundled smoke. |
| CUDA error, `Torch not compiled with CUDA enabled`, or no NVIDIA driver | Several hard-coded recipes call `.cuda()` even when CPU is desired. | Use the bundled CPU smoke, or edit the native recipe to use `device = torch.device(...)` and `.to(device)` everywhere before running. Fire scripts with `--cpu=True` still require their import-time extras. |
| W&B prompts, network calls, or permission errors | Recipes importing W&B may initialize online logging. `train_path_star.py` initializes W&B unconditionally. | Set `WANDB_MODE=disabled` in the environment and pass any script-level flag such as `--track_experiment_online=False` where available. Avoid running logging recipes in hermetic CI unless W&B is disabled. |
| Script appears to hang after starting | Default recipe loops are intentionally long (`1e5` batches or many epochs), and generation/validation may run at step 0. | Interrupt, reduce `num_batches`/`epochs` to 1, `batch_size` to 1-2, `seq_len` to 16-64, and generation length to a small value. Prefer the bundled smoke for readiness checks. |
| Out-of-memory on GPU or CPU | Defaults use dimensions near 512, long sequences, gradient accumulation, or Transformer-XL memory. | Lower `dim`, `depth`, `heads`, sequence lengths, batch size, and gradient accumulation. Disable optional latent/TTT wrappers unless they are the target. |
| Importing a recipe starts training immediately | Hard-coded top-level scripts define the model and loop at module scope. | Do not import native recipe files as libraries. Copy the specific idea into a small helper with an `if __name__ == "__main__"` guard, as done by `scripts/copy_task_smoke.py`. |
| Copy-task smoke runs but reports many mismatches | One to three gradient steps are not enough for convergence. | Treat mismatches as informational. The smoke only asserts that training loss is finite and `generate` returns the expected shape. Increase steps outside CI only if you intentionally want a learning demonstration. |
| `flash_attn` missing | The optional `flash-pack-seq` extra is not installed. | Ignore for the safe smoke and most basic recipes. Install `flash-attn` only for an explicit flash-attention or packed-sequence adaptation, and verify hardware/compiler compatibility first. |
| Fire CLI rejects an argument or parses booleans unexpectedly | Fire maps CLI values directly to Python function signatures and may differ from argparse habits. | Check the recipe's `train(...)` signature in the catalog, use `--flag=True` / `--flag=False` style for booleans, and start with a one-step command. |
| `generate` output shape differs from expectations | Prompt rank or requested generation length does not match the wrapper's expected API. | For the copy smoke, use a batch dimension for the encoder source and a `(batch, 1)` start-token tensor. Assert only shape for tiny non-converged runs. |

## Minimal health checks

From inside this sub-skill directory or another directory that can see the bundled script:

```bash
python scripts/copy_task_smoke.py --help
python scripts/copy_task_smoke.py --steps 1 --device cpu
```

If these pass, the base `torch` + `x_transformers` path is working. Failures in enwik8, W&B, optimizer, or self-distillation scripts should then be diagnosed as recipe-specific dependency/data/hardware issues rather than package-wide failure.
