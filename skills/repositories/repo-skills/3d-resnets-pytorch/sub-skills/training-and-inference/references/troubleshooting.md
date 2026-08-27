# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AttributeError` or import failure mentioning `Scale` | modern `torchvision` removed `transforms.Scale` | add the temporary alias `torchvision.transforms.transforms.Scale = torchvision.transforms.Resize` before importing `main.py`, or pin to a legacy torchvision that still ships `Scale` |
| `assert arch == checkpoint['arch']` when resuming | `--resume_path` does not match the current `--model` / `--model_depth` pair | resume only from the exact architecture, or treat the file as a pretrained checkpoint instead |
| classifier weight size mismatch during `--pretrain_path` load | `--n_pretrain_classes` does not match the checkpoint source label count | set the source class count correctly; the new dataset class count belongs in `--n_classes` |
| optimizer has no useful trainable parameters after fine-tuning setup | `--ft_begin_module` did not match a real top-level module name | use `fc` for ResNet-style models, `classifier` for DenseNet, or a known block such as `layer4` |
| `KeyError: 'OMPI_COMM_WORLD_RANK'` or DDP startup hangs | distributed launch did not provide the expected OpenMPI-style environment | use the matching multi-process launcher and one process per GPU |
| `SyncBatchNorm only supports DistributedDataParallel` | `--batchnorm_sync` was set without `--distributed` | enable distributed training first or remove `--batchnorm_sync` |
| `FileNotFoundError` for `opts.json`, `train.log`, or checkpoints | `result_path` does not exist yet | create the directory before launch; the code writes into it immediately |
| `flow input is supported only when input type is hdf5` | flow mode was selected with JPG inputs | keep `--input_type rgb --file_type jpg`, or convert the dataset to HDF5 for flow |
| `evaluate_results.py` fails on the JSON from `--inference_no_average` | the JSON uses segment-level `segment` / `result` entries instead of per-video `label` / `score` entries | rerun inference without `--inference_no_average`, or aggregate the segment outputs first |
| `evaluate_results.py` returns zero or fewer matches than expected | `--subset` does not match the annotation JSON or the result keys do not line up with the ground truth | use the exact subset string from the annotation file and keep video ids consistent |
| checkpoint keys still include `module.` after cleanup | the file was already bare, or the script was run twice | only strip `DataParallel` prefixes once, and inspect the first few keys before rewriting |
| CPU runs are slow but otherwise work | `--no_cuda` is for debugging only | keep the batch size small, lower `n_threads`, and do not expect GPU throughput on CPU |

## Quick recovery checklist

1. Confirm the model family, depth, and class-count pair in `references/model-catalog.md`.
2. If the issue is a file-format or split mismatch, switch to `../data-preparation/SKILL.md`.
3. Re-run the root helper with a smaller, explicit command.
4. If the result JSON came from no-average inference, regenerate averaged output before scoring.
5. For old checkpoints, strip `module.` prefixes before handing them to bare-state-dict tooling.
