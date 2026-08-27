# Workflows

These workflows are safe by default. They avoid real cloud uploads unless the
user explicitly asks for them and has the required credentials.

## 1) Shared global writer across modules

Use one writer instance in the owning process, then let imported helpers fetch
it from the package singleton.

1. Create the writer once.
2. Install it before worker processes start.
3. Let helper functions call `GlobalSummaryWriter.getSummaryWriter()`.
4. Log a few text/scalar/image values.
5. Close the writer in the parent after workers join.

Example smoke run:

```bash
python scripts/tbx_global_writer_smoke.py --logdir "$(mktemp -d)"
```

If you need multiprocessing, use the same script with the fork-oriented smoke
mode:

```bash
python scripts/tbx_global_writer_smoke.py --logdir "$(mktemp -d)" --multiprocess --workers 4 --steps 5
```

If separate event files appear, the writer was created too late or more than one
process created its own instance.

## 2) Local and remote record writers

Prefer the local filesystem unless the user explicitly wants remote delivery.

- Plain paths use the local file backend.
- `s3://bucket/key` routes to the S3 writer when `boto3` is installed.
- `gs://bucket/key` routes to the GCS writer when `google-cloud-storage` is
  installed.
- `register_writer_factory` is for custom backends that follow the same prefix
  routing rule.

Inspect the safe dependency snapshot first:

```bash
python scripts/tbx_remote_writer_check.py --check-deps
```

Use the bundled mock S3 check when you want route validation without a real AWS
account:

```bash
python scripts/tbx_remote_writer_check.py --mock-s3
```

## 3) Comet forwarding

Keep Comet disabled for local work.

- Default: `comet_config={"disabled": True}`.
- Enable only when the user provides credentials and wants a networked run.
- If a global Comet experiment already exists in the process, expect a warning
  about possible clashes.
- Always close the writer so the Comet experiment can end cleanly.

The generated skill does not promise live Comet verification. Treat that path as
reference-only unless the user explicitly requests an external run.

## 4) Optional telemetry values

GPU telemetry is just another source of scalar values.

- Sample the number with your own monitoring tool.
- Pass the number to `add_scalar`.
- Skip the path if the collector or GPU is missing.

This sub-skill only explains how to log the value, not how to provision the
hardware.
