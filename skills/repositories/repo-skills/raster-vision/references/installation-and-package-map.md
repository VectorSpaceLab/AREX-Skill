# Installation and package map

Use this reference when deciding which Raster Vision packages, plugins, and optional runtime pieces are needed for a task.

## Main install paths

### Pip release install

```bash
pip install rastervision
```

The top-level `rastervision` distribution pulls the standard package family:

- `rastervision_pipeline`
- `rastervision_aws_s3`
- `rastervision_aws_batch`
- `rastervision_core`
- `rastervision_pytorch_learner`
- `rastervision_pytorch_backend`

### Docker image path

Use the published PyTorch Docker image when the task involves realistic training, geospatial compiled dependencies, AWS Batch parity, or GPU setup:

```bash
docker run --rm -it quay.io/azavea/raster-vision:pytorch-0.31 /bin/bash
```

For a safer command-rendering workflow, use the bundled helper in `scripts/check_rastervision_install.py` after installing, and the Docker renderer under `sub-skills/cloud-and-filesystems/scripts/render_docker_run_command.py` before launching containers.

### Optional plugins

| Plugin distribution | Import module | Use when |
| --- | --- | --- |
| `rastervision_aws_sagemaker` | `rastervision.aws_sagemaker` | The pipeline should run as an AWS SageMaker Pipeline. |
| `rastervision_gdal_vsi` | `rastervision.gdal_vsi` | You need GDAL VSI paths such as `/vsicurl/`, `/vsis3/`, `/vsizip/`, or archive-wrapped URIs. |

`rastervision_gdal_vsi` depends on `gdal==3.6.3`; install GDAL with a package manager such as conda-forge when pip wheels are not compatible with the host.

## Import checks

Run this after installation:

```bash
python scripts/check_rastervision_install.py
```

Expected required modules:

- `rastervision.pipeline`
- `rastervision.core`
- `rastervision.pytorch_learner`
- `rastervision.pytorch_backend`
- `rastervision.aws_s3`
- `rastervision.aws_batch`

Expected CLI commands:

- `rastervision run`
- `rastervision run_command`
- `rastervision predict`
- `rastervision predict_scene`

## Python and platform notes

- Python 3.11 is a safe baseline for the current Raster Vision package family and common geospatial/PyTorch wheels.
- Linux is the best-supported platform for realistic training and Docker workflows.
- macOS can work for many workflows, but set PyTorch data loader `num_workers=0` when multiprocessing causes failures.
- Windows is not a primary tested platform and may run into geospatial/PyTorch dependency issues.

## GPU notes

Raster Vision's PyTorch learner can use CUDA when torch can see GPUs. Check:

```python
import torch
print(torch.cuda.is_available())
print(torch.cuda.device_count())
```

A CPU-only environment can still inspect configs, render commands, run CLI help, validate many scene/data objects, and run small CPU smoke tests. Use GPU for realistic training/prediction throughput or when validating CUDA-specific behavior.

## Configuration locations

Raster Vision uses Everett configuration. It checks environment variables, a `.env` file in the working directory, and INI profiles under `${HOME}/.rastervision` by default. Profile options can be selected with `rastervision --profile NAME ...`.

Common environment variables:

- `RV_CONFIG`: explicit configuration file path.
- `RV_CONFIG_DIR`: directory containing profile files.
- `TMPDIR`: root for temporary directories.
- `AWS_S3_REQUESTER_PAYS` or `AWS_REQUEST_PAYER`: requester-pays S3 behavior.
- `AWS_NO_SIGN_REQUEST=yes`: unsigned access for public S3 data.
- `RASTERVISION_USE_DDP`, `RASTERVISION_DDP_BACKEND`, `RASTERVISION_DDP_START_METHOD`: distributed PyTorch training controls.
