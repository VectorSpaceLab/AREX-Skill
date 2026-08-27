# Log and Model Analysis

The repository log analyzer reads line-delimited JSON records and groups scalar
fields by epoch. Real logs may contain non-JSON lines, missing metrics, changing
keys, or validation records. Parse defensively and report skipped lines.

Useful summaries include latest/min/max/mean for loss and learning rate,
elapsed time per step/epoch, validation metric peaks, and the exact record count.
Do not average categorical fields, timestamps, nested objects, or metrics with
different semantics. Compare runs only when config, dataset split, batch size,
metric version, and evaluation cadence agree.

FLOPs analysis builds a model from the config and therefore inherits `spconv`,
custom-op, CUDA, and input-shape constraints. Treat the reported count as
configuration-specific; sparse operations may not be represented faithfully by
generic counters.
