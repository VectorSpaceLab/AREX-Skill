# Dependencies

## Purpose

Read this when deciding which packages are required for a given OFA workflow.
The package metadata is small, but the public workflows rely on a few optional
helpers that are not always declared together.

## Package groups

| Group | Packages | Why it matters |
| --- | --- | --- |
| Core | `ofa`, `torch`, `torchvision`, `filelock` | Base model zoo, runtime modules, and hub entry points. |
| Inference extras | `gdown`, `tqdm` | Public weight/config downloads and progress bars for evaluation. |
| Search extras | `numpy`, `pyyaml`, `thop`, `matplotlib`, `tqdm` | Latency tables, FLOPs estimates, and notebook-style search plots. |
| Optional GPU backend | CUDA-enabled `torch` / `torchvision` wheels | Needed for realistic specialized-model evaluation and any GPU benchmarking. |

## Notes

- `ofa_net` and the predictor smoke can run on CPU.
- Specialized model evaluation is much more useful on CUDA, because the public workflow is optimized for GPU validation.
- Distributed training is intentionally out of scope for this generated skill, so Horovod and MPI are not part of the selected install set.
- If you only need a smoke check, install the core group first and add the extras only when the workflow needs them.
