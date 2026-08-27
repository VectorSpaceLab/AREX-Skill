---
name: cloud-and-filesystems
description: "Routes Raster Vision Docker, AWS Batch, AWS SageMaker, AWS S3,
  requester-pays/unsigned S3, GDAL VSI, CloudFormation, and bootstrap setup
  tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Cloud, Docker, and Filesystems

Use this sub-skill when a Raster Vision task mentions Docker, AWS Batch, AWS SageMaker, AWS S3, requester-pays buckets, unsigned public S3 access, GDAL VSI, CloudFormation, `~/.rastervision/default`, `RV_CONFIG`, `RV_CONFIG_DIR`, `AWS_REQUEST_PAYER`, `AWS_NO_SIGN_REQUEST`, or new-project bootstrap guidance.

## Owns

- Cloud transport choice and resource settings for Raster Vision runners.
- Remote filesystem behavior and credential boundaries.
- Docker command rendering and runtime flags.
- Bootstrap guidance for image-based project scaffolding.
- Troubleshooting for cloud, storage, GPU, and container setup.

## Routes out

- Pipeline command semantics and runner subcommand parsing -> pipeline-cli.
- Data/model schemas, predictors, and bundles -> data-and-models.
- PyTorch task recipes and example pipelines -> pytorch-workflows.

## Start here

- [AWS runners](references/aws-runners.md)
- [Filesystems](references/filesystems.md)
- [Docker and bootstrap](references/docker-and-bootstrap.md)
- [Troubleshooting](references/troubleshooting.md)
- [Docker command renderer](scripts/render_docker_run_command.py)
- [CloudFormation templates](templates/cloudformation/README.md)
