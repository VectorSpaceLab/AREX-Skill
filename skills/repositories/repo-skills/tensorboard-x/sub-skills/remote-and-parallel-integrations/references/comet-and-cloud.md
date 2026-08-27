# Comet and Cloud Boundaries

This sub-skill treats credentialed or networked actions as help-only by default.
Use the local filesystem or the bundled mock checks unless the user explicitly
asks for a real remote run.

## Local fallback

When a path has no registered prefix, `RecordWriter` uses a normal local file.
That is the safest path for ordinary development, dry runs, and CI.

## Remote logdir schemes

| Scheme | Backend | Required dependency | Default posture |
| --- | --- | --- | --- |
| `s3://bucket/key` | S3 record writer | `boto3` | Help-only unless the user asks for remote delivery. |
| `gs://bucket/key` | GCS record writer | `google-cloud-storage` | Help-only unless the user asks for remote delivery. |
| Plain path | Local filesystem | none beyond Python | Default fallback. |

### S3 notes

- The writer expects `s3://bucket/key` style paths.
- `S3_ENDPOINT` is honored for S3-compatible endpoints.
- Real uploads require credentials and network access.
- The bundled mock S3 smoke is the preferred non-production check.

### GCS notes

- The writer expects `gs://bucket/key` style paths.
- `google-cloud-storage` must be installed.
- Real uploads require credentials and network access.
- This skill does not bundle a verified GCS mock path; keep it reference-only
  or use your own emulator if you need one.

## Mock-cloud strategy

- Use `scripts/tbx_remote_writer_check.py --mock-s3` when you want to validate
  the S3 prefix path without real cloud credentials.
- Treat GCS as dependency-check only unless the user brings their own emulator.
- Do not claim real cloud verification when only a mock or dependency probe ran.

## Projector and plugin output boundary

Embedding/projector helpers can create local files that are later uploaded when
the save path starts with `s3://` or `gs://`. Route projector data-shape and
metadata questions to [graph-and-embedding-plugins](../../graph-and-embedding-plugins/SKILL.md); keep this page focused on credentials, logdir schemes, and whether a real remote upload is authorized.

## Comet contract

- Default config: `{"disabled": True}`.
- Disabled mode is the safe local default.
- If `disabled` is set to `False` without `comet_ml` and Pillow, the logger
  raises an exception.
- If the process already has a global Comet experiment, the logger warns about
  a possible clash.

Keep Comet forwarding opt-in and keep the disabled default in ordinary workflows.

## GPU telemetry boundary

Any optional telemetry source may produce numbers for logging.
This sub-skill only treats those values as scalars; it does not require a GPU or
sample the device itself.
