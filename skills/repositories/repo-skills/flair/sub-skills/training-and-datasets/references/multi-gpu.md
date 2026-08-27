# Optional Multi-GPU Training

Multi-GPU Flair training is optional and unverified in the CPU baseline. Do not present it as available unless the active environment proves CUDA, at least two visible GPUs, a compatible PyTorch CUDA build, enough device memory, shared access to the same corpus files, and a working distributed launch. ONNX/provider runtimes are separate optional acceleration paths and do not prove multi-GPU training.

## Required conditions before use

Verify all of the following before enabling `multi_gpu=True`:

1. `torch.cuda.is_available()` returns `True`.
2. `torch.cuda.device_count()` is at least `2`.
3. Every worker can import the same public pip-installed `flair` package.
4. Every worker can read the same local corpus files and write to the intended output area without clobbering unrelated runs.
5. Corpus construction is deterministic across workers. Use explicit split files and fixed seeds before sampling or downsampling.
6. Public model or dataset downloads are already cached or explicitly allowed for every worker.
7. The training entry point is wrapped with `flair.distributed_utils.launch_distributed(...)`.

If any condition is missing, keep the run single-process on CPU or a separately verified single GPU.

## Required Flair pattern

The installed API includes `flair.distributed_utils.launch_distributed(fn, *args, **kwargs)` and trainer methods with `multi_gpu=False` by default. `multi_gpu=True` belongs inside the distributed launcher.

```python
import torch
import flair
from flair.distributed_utils import launch_distributed
from flair.trainers import ModelTrainer


def main(multi_gpu: bool):
    flair.set_seed(42)

    corpus = build_corpus_with_explicit_splits()
    label_dictionary = corpus.make_label_dictionary("topic")
    model = build_model(label_dictionary)

    mini_batch_chunk_size = 16
    device_count = max(torch.cuda.device_count(), 1)
    mini_batch_size = mini_batch_chunk_size if multi_gpu else mini_batch_chunk_size * device_count

    trainer = ModelTrainer(model, corpus)
    trainer.fine_tune(
        "outputs/multi-gpu-run",
        multi_gpu=multi_gpu,
        mini_batch_size=mini_batch_size,
        mini_batch_chunk_size=mini_batch_chunk_size,
        embeddings_storage_mode="none",
        max_epochs=2,
    )


if __name__ == "__main__":
    launch_distributed(main, True)
```

Why both pieces matter:

- `launch_distributed(...)` starts one worker process per participating GPU.
- `multi_gpu=True` tells `ModelTrainer` to use distributed data parallel behavior and distributed sampling.
- If `multi_gpu=True` is set without the launcher, Flair can fail because the distributed process group was not initialized.

## Batch-size accounting

Distributed training changes how many examples are processed before an optimizer step. A fair comparison uses `mini_batch_chunk_size` as the per-device forward-pass size:

- Multi-GPU: `mini_batch_size = mini_batch_chunk_size` per worker.
- Single-process comparison: `mini_batch_size = mini_batch_chunk_size * number_of_devices`.

This keeps effective examples per optimizer step comparable while each GPU processes the same chunk size.

## Corpus determinism

The same corpus must appear in the same order on every worker before distributed sampling. Practical rules:

- Set `flair.set_seed(seed)` at the beginning of the launched function.
- Avoid non-deterministic file discovery; pass explicit split files when possible.
- If calling `downsample(...)`, pass a fixed `random_seed` or set Flair's seed first.
- Do not let each worker independently download and transform a dataset unless that workflow is proven safe and idempotent.
- Prefer preparing local corpus files and model/cache entries before launch.

## Resource caveats

- CUDA and two-or-more GPUs are not verified by the CPU baseline.
- `embeddings_storage_mode="gpu"` multiplies GPU memory pressure and is not recommended unless memory headroom is measured.
- Transformer fine-tuning is usually memory-bound. Start with `embeddings_storage_mode="none"`, small `mini_batch_chunk_size`, and explicit `mini_batch_size`.
- AMP (`use_amp=True`) is a separate optional path requiring compatible CUDA behavior and numeric validation.
- If one worker fails because of missing cache, authentication, network, or optional dependencies, the distributed run can hang or fail noisily. Preflight the worker environment first.

## Debug sequence

1. Run the same corpus/model code with `multi_gpu=False` on CPU or one verified GPU and a tiny downsample.
2. Verify corpus loading and label dictionary creation outside the launcher.
3. Verify `torch.cuda.device_count()` and a minimal distributed launch that only prints worker identity.
4. Enable `launch_distributed(main, True)` and `trainer.fine_tune(..., multi_gpu=True)` on a tiny run.
5. Scale corpus size, batch size, and epochs only after the tiny run writes expected trainer outputs.
