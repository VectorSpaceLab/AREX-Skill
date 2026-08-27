# ESPnet2 GPU and Distributed Training

Use `--ngpu N` and `CUDA_VISIBLE_DEVICES` for GPU selection:

```bash
CUDA_VISIBLE_DEVICES=0 python -m espnet2.bin.asr_train --ngpu 1 --config conf/train_asr.yaml ...
CUDA_VISIBLE_DEVICES=0,1 python -m espnet2.bin.asr_train --ngpu 2 --config conf/train_asr.yaml ...
```

Review batching whenever GPU count changes. ESPnet does not prove that a config scales just because `--ngpu` is larger. Check `--batch_size`, `--valid_batch_size`, `--batch_bins`, `--valid_batch_bins`, and `--batch_type`.

## Distributed options

Common distributed flags include `--dist_backend`, `--dist_init_method`, `--dist_world_size`, `--dist_rank`, `--local_rank`, `--dist_launcher`, and `--multiprocessing_distributed`. Recipe cluster behavior also depends on `cmd.sh`, scheduler config files, and the environment in `path.sh`.

## Verification levels

| Evidence | What it proves | What it does not prove |
| --- | --- | --- |
| CPU import and `--help` | Python package import and parser surface | Model construction, CUDA kernels, data loading, memory behavior |
| CPU `--dry_run true --iterator_type none` | Config parser and many model constructors | Real data iterators, training loop performance, GPU OOM behavior |
| Tiny CUDA tensor allocation | Torch can allocate on a visible GPU | ESPnet config trains, distributed/NCCL works, optional kernels work |
| Tiny native GPU training case | Selected config can start on GPU | Recipe-scale convergence or benchmark quality |
| Full recipe | End-to-end reproducibility for that recipe | Broad task-family correctness |

Do not claim full GPU/distributed verification without a backend-specific native case.
