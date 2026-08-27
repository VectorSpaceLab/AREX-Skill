# Training and data troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Training hangs before first iteration | Dataset indices being built by one rank while others wait, or distributed launch/rendezvous issue. | If logs mention dataset/cache work, prebuild cache and enable fast cache flags. If NCCL/rendezvous appears, inspect launch topology and rank logs. |
| Later NCCL timeout on many ranks | One rank crashed earlier with a Python traceback. | Search every rank stderr; fix the first non-NCCL exception. |
| Shape/divisibility assertion | TP/PP/CP/EP sizes incompatible with heads/layers/experts/batch. | Recompute topology using core-models-and-parallelism before relaunch. |
| `CUDA_DEVICE_MAX_CONNECTIONS` assertion or slowdown | Env var set wrong for TP/CP/FSDP/overlap mode. | Apply the parallelism sub-skill decision table; do not blindly export `1`. |
| `FileNotFoundError` for tokenizer/vocab/merge | Tokenizer args are incomplete or paths are not mounted in container/SLURM job. | Verify tokenizer mode and mount/shared paths; for smoke use `NullTokenizer` only with numeric-token rows. |
| `ValueError: invalid literal for int()` during `NullTokenizer` preprocessing | The fixture contains natural-language text, but `NullTokenizer` converts whitespace-separated items to integer ids. | Use numeric smoke rows such as `{"text":"1 2 3 4"}` or switch to a real tokenizer with local tokenizer files. |
| Preprocessing downloads NLTK/tokenizer data unexpectedly | Sentence splitting or tokenizer path requires external resources. | Provide local tokenizer/NLTK data or avoid sentence splitting for bounded smoke. |
| Data loader slow during training | Too many small files, mmap behavior, object storage without fast path, or excessive workers. | Merge datasets, prebuild cache, use per-dataset sequence JSON, test `--no-mmap-bin-files`, tune workers. |
| Mock-data run is fast but real-data run is slow | Data pipeline bottleneck rather than model compute. | Use mock-data throughput as ceiling; optimize data cache/storage path. |
| Checkpoint save fails | Output path not shared/writable or checkpoint format incompatible. | Verify shared storage and route format/resharding details to checkpointing-and-conversion. |
| OOM in forward/backward | Model size, micro-batch, sequence length, precision, recompute, or sharding choice too aggressive. | Reduce micro-batch/sequence, add recompute or FSDP, adjust TP/PP/CP, check precision/kernels. |

## Debug sequence

1. Capture command, environment, nodes/GPUs, and exact rank logs.
2. Find the earliest Python traceback, not the loudest NCCL timeout.
3. Check topology and data path before changing optimizer or model code.
4. Reproduce with `--mock-data` when diagnosing environment/topology independent of data.
5. Reproduce with a tiny preprocessed fixture when diagnosing tokenizer/data path independent of model scale.
