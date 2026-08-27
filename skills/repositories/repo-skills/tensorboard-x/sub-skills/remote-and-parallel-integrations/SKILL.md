---
name: remote-and-parallel-integrations
description: "Use for GlobalSummaryWriter, multiprocessing/global writer
  patterns, remote RecordWriter factories, Comet forwarding, and credential-safe
  cloud or telemetry integration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Remote and Parallel Integrations

Use this sub-skill for logging surfaces that cross process, module, credential,
or service boundaries.

## Use this when
- one logger must be shared across imported modules
- worker processes need to append to one event stream
- a log target may be local, `s3://...`, or `gs://...`
- Comet forwarding is optional and must stay disabled by default
- GPU telemetry values exist only as optional scalar inputs

## Route elsewhere when
- scalar, writer-lifecycle, or event-file detail is the main task → [logging-core](../logging-core/SKILL.md)
- image, audio, video, text, mesh, or histogram payload detail is the main task → [rich-media-summaries](../rich-media-summaries/SKILL.md)
- graph, embedding, or projector payload detail is the main task → [graph-and-embedding-plugins](../graph-and-embedding-plugins/SKILL.md)

## Safe defaults
- Prefer a local logdir unless the user explicitly asks for remote delivery.
- Treat Comet as disabled unless `comet_config` enables it.
- Treat `s3://` and `gs://` as credentialed boundaries, not default runtime targets.
- Create one writer in the owning process, then close it after workers finish.
- Use the bundled smoke helpers in this skill tree instead of ad hoc checks.

## Bundled helpers
- [scripts/tbx_global_writer_smoke.py](scripts/tbx_global_writer_smoke.py)
- [scripts/tbx_remote_writer_check.py](scripts/tbx_remote_writer_check.py)

## Cross-links
- Shared install/routing notes: [../../references/install-and-routing.md](../../references/install-and-routing.md)
- Shared troubleshooting: [../../references/troubleshooting.md](../../references/troubleshooting.md)
- Global writer API details: [references/api-reference.md](references/api-reference.md)
- Cloud/Comet workflow notes: [references/comet-and-cloud.md](references/comet-and-cloud.md)
