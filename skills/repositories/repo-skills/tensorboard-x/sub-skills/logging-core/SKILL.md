---
name: logging-core
description: "Ordinary TensorBoard scalar logging, writer lifecycle, and
  event-file checks for tensorboardX."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# logging-core

Use this sub-skill for the ordinary tensorboardX event-writing path: creating a writer, logging scalar-like values, managing run directories, and checking that TensorBoard can read the result.

## Use this when

- the user needs `SummaryWriter` setup or logdir naming guidance
- the task is about `add_scalar`, `add_scalars`, hparams, or custom scalar layouts
- the user asks why TensorBoard does not show a run yet
- the code must flush, close, reopen, or resume a writer safely
- the user wants `write_to_disk=False` for dry runs or tests
- a small local event-file smoke check is enough to validate the workflow

## Route out

- Rich media summaries such as images, audio, video, PR curves, mesh, and deeper text handling: [../rich-media-summaries/SKILL.md](../rich-media-summaries/SKILL.md)
- Graph, embedding, ONNX, and OpenVINO logging: [../graph-and-embedding-plugins/SKILL.md](../graph-and-embedding-plugins/SKILL.md)
- Multiprocessing, global writer, S3/GCS, and Comet integrations: [../remote-and-parallel-integrations/SKILL.md](../remote-and-parallel-integrations/SKILL.md)
- Shared install issues before a workflow is selected: [../../references/install-and-routing.md](../../references/install-and-routing.md)

## Operating sequence

1. Choose a writable logdir or let `SummaryWriter()` create one.
2. Use slash-separated tags for related scalar plots.
3. Log scalar-like data with explicit steps whenever reproducibility matters.
4. Use `with writer.use_metadata(global_step=step): ...` when several calls share one step or wall time.
5. Call `flush()` when immediate visibility matters and `close()` when the run is done.
6. Inspect output with `tensorboard --logdir <logdir>` after event files exist.
7. If the run resumed after a crash, use `purge_step` instead of mixing stale and new steps blindly.

## Bundled helpers

- [scripts/tbx_logging_smoke.py](scripts/tbx_logging_smoke.py): writes a tiny scalar, scalar-group, custom-scalar, text, and optional JSON-export run, then reports event-file counts.
- [scripts/tbx_hparams_smoke.py](scripts/tbx_hparams_smoke.py): writes a tiny hparams comparison with distinct trial names.

Run each helper with `--help` first. Both are safe by default and create temporary output when no logdir is supplied.

## References

- [references/api-reference.md](references/api-reference.md): verified method signatures, writer stack, logdir behavior, scalar groups, hparams, and lifecycle details.
- [references/workflows.md](references/workflows.md): short recipes for scalar runs, hparams, metadata defaults, custom scalars, crash recovery, and local event-file sanity checks.
- [references/troubleshooting.md](references/troubleshooting.md): missing event files, delayed flushes, duplicate steps, scalar shape errors, JSON-export surprises, path issues, and memory growth.

## Decision hints

- Use `add_scalar()` for one numeric series and `add_scalars()` for grouped charts.
- Use `add_hparams()` for comparing explicit trial configurations, not as a full hyperparameter search engine.
- Use `write_to_disk=False` only when the absence of event files is intended.
- Prefer context managers in short scripts so event files are closed even on exceptions.
