# Memory and Performance

## `fit_mode`

| Mode | Behavior | Typical use |
| --- | --- | --- |
| `low_memory` | Preprocesses on demand during inference. | Lowest memory footprint, slower prediction. |
| `fit_preprocessors` | Preprocesses and caches once during fit. | General default for ordinary prediction. |
| `fit_with_cache` | Builds a trainset cache during fit for faster repeated prediction. | Repeated inference, CV, server-like reuse. |
| `batched` | Internal mode used by batched workflows. | Not usually set directly by users. |

## Cache options

- `keep_cache_on_device=True` keeps cached train representations on the active device.
- `kv_cache_precision` controls the precision of the cached KV representation when cache mode is used.
- `TABPFN_MAX_BATCHED_TEST_ROWS` controls how many test rows are processed in one chunk during cached batched inference.

## Practical tradeoffs

- `fit_with_cache` spends more memory and fit time to make repeated prediction faster.
- `low_memory` is preferable when the user can tolerate slower prediction but must conserve memory.
- `fit_preprocessors` is the best default when the user wants normal single-dataset inference.
- Multiple GPUs are only used for some fit modes; do not assume every mode parallelizes across all devices.

## Performance advice

- Use batched inference only when many datasets share shape and class constraints.
- Use the largest safe test-row chunking value for your hardware.
- If OOM happens in cached inference, reduce `TABPFN_MAX_BATCHED_TEST_ROWS` before changing the core workflow.
