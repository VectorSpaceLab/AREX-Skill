# Setup Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for repo modules | The repo root is not on the import path or the wrong directory is active. | Re-run the preflight from the AnyDoor root. |
| `torch.cuda.is_available() == False` on a GPU host | CPU-only torch or a backend mismatch. | Install a CUDA-capable torch build and rerun the smoke check. |
| `No module named xformers` | Optional wheel missing. | Continue unless the user explicitly needs the memory-saving path. |
| `share==1.0.4` is unavailable | Source helper dependency not present on the index. | Treat it as a conversion-helper limitation, not a repo-wide failure. |
| Demo refinement toggle fails to load | `iseg/coarse_mask_refine.pth` is missing or the toggle is enabled without the weight. | Disable the toggle or supply the weight. |
| `path/epoch=...ckpt` still appears in configs | Placeholder path was not patched. | Use the bundled config patcher and retry. |
| DINOv2 encoder path still points at `path/dinov2_vitg14_pretrain.pth` | Placeholder weight path was not replaced. | Patch `configs/anydoor.yaml`. |

## Notes

- The attention code can proceed without xformers.
- The repo is not a single installable package; import checks should still verify
  the local modules.
- Generation readiness is not the same as import readiness.
