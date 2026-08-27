# Troubleshooting

This file collects cross-cutting failure modes for Raster Vision cloud, storage, GPU, and container setup.

## Quick symptom table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| GPU not visible in Docker | Container runtime is missing GPU support | Install the NVIDIA container toolkit and use `--gpus=all` or the legacy NVIDIA runtime |
| Training is extremely slow on a multi-GPU host | GPU was not actually enabled | Check `torch.cuda.is_available()`, `torch.cuda.device_count()`, and `nvidia-smi` |
| Public S3 access fails | Unsigned S3 requests are not enabled | Set `AWS_NO_SIGN_REQUEST=yes` |
| Requester-pays S3 access fails | Requester-pays is not enabled | Set `AWS_REQUEST_PAYER=requester` or configure `[AWS_S3] requester_pays=True` |
| Batch jobs are submitted but fail quickly | Wrong queue/job-definition names or transient Batch failure | Verify the `[BATCH]` config and raise `attempts` above 1 |
| SageMaker pipeline build fails | Role, quota, instance type, or S3 root is wrong | Verify the IAM role, instance quotas, image URIs, and `train_uri` |
| GDAL VSI import fails | GDAL is missing or the wrong version is installed | Install GDAL 3.6.3 to match the plugin |
| Docker wrapper behavior is odd on WSL2 | `NAME` can collide with shell-wrapper variables | Render an explicit command with `scripts/render_docker_run_command.py` and run the printed `docker run ...` command directly |
| macOS workers hang or crash | Python multiprocessing with nonzero loader workers | Set `num_workers=0` |
| Config profile is not found | Wrong RV profile path | Check `RV_PROFILE`, `RV_CONFIG`, and `RV_CONFIG_DIR` |
| Remote jobs cannot see local data | Remote runners do not use the local filesystem | Stage data in S3 or a remote filesystem |

## Cloud and runner fixes

- Batch needs the CloudFormation stack, the right queue and job-definition names, and usable instance capacity.
- SageMaker needs an IAM role with SageMaker permissions, a valid image URI, enough quota for the chosen instance types, and S3 roots for training.
- If Batch uses split commands, confirm that `AWS_BATCH_JOB_ARRAY_INDEX` is present in the job environment.
- If SageMaker training is spot-backed, remember that `spot_instance_max_wait_time` must be at least `max_run_time`.

## Filesystem fixes

- When `sync_*` helpers fail with AWS S3, confirm that the AWS CLI is installed because those helpers call `aws s3 sync`.
- When `read_*` or `write_*` helpers fail for S3, check whether the bucket is requester-pays or unsigned and set the matching env var.
- If cached downloads appear stale, clear the RV cache directory under the configured temp root and retry.
- If `rasterio` cannot find GDAL data, set `GDAL_DATA` from the installed rasterio package path.

## Docker fixes

- If the generated Docker command uses the wrong path, pass an explicit `--source-dir` or `--data-dir`.
- If a notebook or docs port is already taken, change the port mapping in the printed command before running it.
- If the container cannot see the GPU, make sure the host runtime supports NVIDIA GPUs and that the container was launched with the GPU flag.

## What to escalate to other sub-skills

- Pipeline command syntax and `rastervision run ...` subcommands -> pipeline-cli.
- Data-source, label-source, and model-bundle questions -> data-and-models.
- Recipe-specific training or example questions -> pytorch-workflows.
