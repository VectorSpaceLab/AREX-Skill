# FCOS Training and Evaluation Workflows

## Multi-GPU training

The documented FCOS training command uses `torch.distributed.launch` with eight GPUs:

```bash
python -m torch.distributed.launch --nproc_per_node=8 --master_port=<port> train_net.py --config-file <config> DATALOADER.NUM_WORKERS 2 OUTPUT_DIR <output-dir>
```

Use the bundled command builder to avoid typo-prone manual construction. The total batch size is controlled by `SOLVER.IMS_PER_BATCH` in the config, not automatically by `--nproc_per_node`.

## One-GPU or CPU-constrained training planning

For fewer GPUs, lower `--nproc_per_node`; do not blindly change global batch unless you also adjust solver settings. If memory is limited:

- choose a lighter MobileNet config,
- lower `DATALOADER.NUM_WORKERS`,
- verify dataset layout before launching,
- consider smaller images or batch-size changes only with awareness of benchmark comparability.

## Evaluation on a dataset split

Evaluation requires a config whose `DATASETS.TEST` key exists in `DatasetCatalog`, a matching dataset layout, a compiled FCOS install, and `MODEL.WEIGHT`.

```bash
python sub-skills/training-evaluation/scripts/build_eval_command.py --config-file configs/fcos/fcos_imprv_R_50_FPN_1x.yaml --weights FCOS_imprv_R_50_FPN_1x.pth --ims-per-batch 1 --output-dir eval_out
```

The actual evaluation writes per-dataset outputs under `OUTPUT_DIR/inference/<dataset_name>`.

## Benchmark honesty

The repo reports AP and timing using specific hardware/software stacks and datasets. Treat command construction, config loading, and synthetic checks as workflow validation only. Do not claim AP reproduction unless the full dataset, weights, compiled extension, and GPU run completed.
