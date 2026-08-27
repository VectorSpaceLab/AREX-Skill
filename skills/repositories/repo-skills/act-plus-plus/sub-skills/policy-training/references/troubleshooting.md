# Policy-training troubleshooting

## Symptoms and recovery

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: robomimic.algo.diffusion_policy` | The installed robomimic build does not expose the diffusion policy surface expected by `policy.py`. | Install or patch a compatible robomimic build, then re-run the check helper before launching training. |
| `ImportError: cannot import name 'ConditionalUnet1D'` | The robomimic diffusion policy module exists but does not re-export the expected class. | Confirm the installed module exposes `ConditionalUnet1D` and `replace_bn_with_gn`; do not start Diffusion training until that import succeeds. |
| `CUDA out of memory` | Batch size, chunk size, or hidden dimension is too large for the GPU. | Reduce `--batch_size` first, then `--chunk_size`, then the hidden dimensions. |
| Training starts but validation loss never improves | Wrong task name, wrong dataset family, or a checkpoint being resumed from mismatched normalization stats. | Confirm the dataset directory, `task_name`, camera names, and `dataset_stats.pkl` all belong to the same run family. |
| `KeyError` / shape mismatch when loading data | The HDF5 file layout does not match the expected 14-D action/qpos convention or the optional `/base_action` field is missing unexpectedly. | Check [data formats](../../../references/data-formats.md) and regenerate or convert the dataset before training. |
| Evaluation loads the wrong checkpoint | The code path loads `policy_last.ckpt` by default when `--eval` is set. | If you want a different checkpoint, edit the command or patch the source workflow before running. |
| `--load_pretrain` fails immediately | The source path is hard-coded to a particular pretraining directory. | Avoid the flag unless the checkpoint exists on the host or the workflow is patched to accept an explicit path. |

## CLI mismatch notes

- Use `--num_steps` for the current `imitate_episodes.py` step-based trainer.
- Use `--num_epochs` only for `train_latent_model.py`.
- The README examples may be older than the current parser flags.

## Safe recovery order

1. Run the bundled [policy stack checker](../scripts/check_policy_stack.py) to confirm the checkout imports and CUDA path before long runs.
2. Confirm the dataset schema from [data formats](../../../references/data-formats.md).
3. Confirm the policy class and checkpoint family match.
4. Only then start a long train or eval run.
