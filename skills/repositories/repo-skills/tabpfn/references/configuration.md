# Configuration and Environment Variables

TabPFN uses a small set of environment variables and settings objects to control
model access, cache location, device selection, and memory behavior.

## High-value environment variables

| Variable | Effect |
| --- | --- |
| `TABPFN_MODEL_CACHE_DIR` | Overrides the directory used for downloaded checkpoints. |
| `TABPFN_MODEL_CACHE_SIZE` | Enables the built-model LRU cache when set to a positive integer. |
| `TABPFN_ALLOW_CPU_LARGE_DATASET` | Allows CPU use on larger datasets instead of raising by default. |
| `TABPFN_MPS_MEMORY_FRACTION` | Controls the per-process memory fraction on Apple Silicon. |
| `TABPFN_MAX_BATCHED_TEST_ROWS` | Controls test-row chunking for cached batched inference. |
| `TABPFN_EXCLUDE_DEVICES` | Excludes devices such as `cuda`, `mps`, or `cpu` from device inference. |
| `TABPFN_TOKEN` | Supplies a headless access token for model access. |
| `TABPFN_NO_BROWSER` | Disables browser login and forces token-based access. |

## Settings objects

- `TabPFNSettings` — model cache, model version, auth, CPU-limit, and MPS memory
  settings.
- `PytorchSettings` — PyTorch memory allocation settings used by the package.
- `TestingSettings` — test-only settings used by the repository test suite.

## Practical notes

- `TABPFN_MODEL_CACHE_DIR` is the safest way to pin a cache directory for a
  project or CI environment.
- `TABPFN_ALLOW_CPU_LARGE_DATASET` only affects the CPU sample guard; it does
  not remove the underlying performance cost.
- `TABPFN_MPS_MEMORY_FRACTION` should be set before import when you want to
  adjust MPS memory limits.
