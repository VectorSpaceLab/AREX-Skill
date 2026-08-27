# Cloud Training

## Purpose

Read this when the user wants to submit a Luminoth run to Google Cloud ML
Engine instead of running locally.

## Prerequisites

You need all of the following before the cloud commands will work:

- a Google Cloud project,
- Google Cloud SDK installed locally,
- `gcloud auth login` completed,
- Compute Engine, Cloud ML Engine, and Cloud Storage APIs enabled,
- a service account JSON file pointed to by `GOOGLE_APPLICATION_CREDENTIALS`,
- dataset TFRecords uploaded to a Cloud Storage bucket,
- and the `luminoth[gcloud]` dependency group installed.

## Command family

- `lumi cloud gc train` submits a training job.
- `lumi cloud gc evaluate` submits an evaluation job.
- `lumi cloud gc jobs` lists jobs in the project.
- `lumi cloud gc logs` streams logs for a job id.

## Important behavior

- The cloud trainer packages the installed Luminoth version into a source
  tarball and uploads it to Cloud Storage.
- The cloud trainer injects the job directory as `gs://<bucket>/lumi_<job_id>`.
- The cloud evaluator can rebuild the package or reuse the one written by the
  training job.
- Cloud jobs write their artifacts under `lumi_<job_id>` in the bucket.

## Common flags

### `lumi cloud gc train`

- `--config`: required YAML config file.
- `--dataset`: Cloud Storage path to TFRecords.
- `--bucket`: bucket used to store job artifacts.
- `--resume`: previous job id to resume from.
- `--region`: compute region.
- `--scale-tier`, `--master-type`, `--worker-type`, `--worker-count`,
  `--parameter-server-type`, and `--parameter-server-count` adjust the cluster.

### `lumi cloud gc evaluate`

- `--train-folder`: bucket path containing the training job artifacts.
- `--split`: dataset split to evaluate.
- `--bucket`: bucket for the evaluation run.
- `--rebuild`: rebuild the package instead of reusing the training tarball.

## Recovery hints

- If the command says the gcloud extras are missing, install `luminoth[gcloud]`.
- If access is forbidden, confirm the project APIs and service account roles.
- If the region is unknown, choose a valid Google Cloud region.
- If the bucket or dataset path is wrong, the command will fail before job
  submission or before evaluation can start.

## What to read next

- `references/troubleshooting.md` for a compact failure table.
- `references/workflows.md` for the local train/eval context.
