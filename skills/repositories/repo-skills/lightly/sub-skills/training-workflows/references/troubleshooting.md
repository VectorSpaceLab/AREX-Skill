# Troubleshooting

Use this matrix when a Lightly training recipe, Lightning module, or distributed run does not behave as expected.

| Symptom | Likely cause | Quick fix |
|---|---|---|
| Training tries to download CIFAR-10 or pretrained weights | the recipe still uses a download-ready source example | swap in a local image folder dataset or the bundled synthetic helper; keep the same model and loss wiring |
| GPU is requested but nothing runs on the GPU | `cuda` was selected on a CPU-only host, or Lightning was pointed at the wrong accelerator | use `--device auto` for the helper or `accelerator="cpu"` / `"gpu"` in Lightning, then gate GPU-only runs explicitly |
| Forward or loss shape mismatch | the backbone output dimension no longer matches the projection head input dimension | print the feature tensor shape, update the head, and rerun the synthetic step before touching the real data pipeline |
| Loss is unstable or the last batch is odd-sized | batch size is too small for the recipe, or `drop_last=False` is letting the final batch break batch-norm / contrastive assumptions | raise the batch size if possible and keep `drop_last=True` for SimCLR-style and batch-norm-heavy recipes |
| A checkpoint file never appears | no checkpoint callback was configured, the output directory is unwritable, or the writing rank is wrong | set an explicit `ModelCheckpoint` or `default_root_dir`, and make sure only the main rank writes the final file |
| DDP hangs before the first step | local port collision, stale workers, or sampler/process-group setup problems | pick a free port, restart the process group cleanly, lower `num_workers`, and keep the distributed sampler flag enabled |
| A Lightning example still uses an old sampler argument | Lightning version drift between older docs and the installed release | prefer `use_distributed_sampler=True` on Lightning 2.x instead of older `replace_sampler_ddp=True` |
| A local folder seems empty or is skipped | the path is wrong, or the directory does not contain supported image files | verify the local path and confirm the folder tree already contains images before starting training |
| A distributed run is slower than expected | batch norm synchronization or feature gathering adds communication overhead | disable the distributed extras when they are not required by the method, or narrow the run to the exact recipe that needs them |

## Fast diagnosis order

1. Confirm the data source is local and the recipe is not still downloading.
2. Confirm the device choice matches the host.
3. Confirm the feature dimension and projection head agree.
4. Confirm batch size and `drop_last` match the recipe family.
5. If DDP is involved, confirm the port, sampler, and worker count.
