# Docker and bootstrap

This reference covers Raster Vision container usage, local launch flags, and the bootstrap path for new project repositories.

## Base container model

- Raster Vision publishes PyTorch images on Quay.
- The bundled Docker command renderer defaults to the `raster-vision-pytorch` image in a CPU runtime.
- A typical container command mounts:
  - `~/.rastervision` to `/root/.rastervision`
  - the current project or source tree to `/opt/src`
  - `RASTER_VISION_DATA_DIR` to `/opt/data`
- `RASTER_VISION_NOTEBOOK_DIR` is only used when a notebook server is requested.

## Common runtime flags

| Flag | Behavior |
| --- | --- |
| `--aws` | Forward AWS credentials by setting `AWS_PROFILE` and mounting `~/.aws` read-only |
| `--gpu` | Request GPU access for the container runtime |
| `--jupyter` | Expose a notebook server on port 8888 and mount the notebook directory |
| `--jupyter-lab` | Expose Jupyter Lab on port 8888 and mount the notebook directory |
| `--tensorboard` | Expose TensorBoard on port 6006 |
| `--name` | Set the container name |
| `--docs` | Run the docs server and expose port 8000 |
| `--debug` | Expose the remote-debug mapping from 3003 to 3000 |
| `--arm64` | Use the arm64 image variant |

Docker on modern hosts can use `--gpus=all`; older setups may still need the NVIDIA runtime.

## Environment knobs

- `RASTER_VISION_DATA_DIR` points to the host directory that becomes `/opt/data`.
- `RASTER_VISION_NOTEBOOK_DIR` points to the host notebook directory that becomes `/opt/notebooks`.
- `AWS_PROFILE` is forwarded when AWS credentials are mounted.
- On WSL2, avoid shell wrapper variable collisions by rendering an explicit command with `scripts/render_docker_run_command.py` and running the printed `docker run ...` command directly.

## Bootstrap new projects

Raster Vision documents a cookiecutter-based bootstrap pattern for starting a new Raster Vision project with its own Docker image.

The generated project skeleton normally contains:

- a `Dockerfile`
- build/run/publish Docker helper scripts
- `requirements.txt`
- `setup.py` or package metadata
- a plugin package skeleton with tests and config stubs

Typical flow:

1. Create the project from a Raster Vision-compatible cookiecutter template.
2. Build the project image with the generated build helper or an equivalent `docker build` command.
3. Publish the image to ECR only when the project uses AWS Batch job definitions.
4. Update the project-specific Batch profile or CloudFormation job definitions to point at the new image tag.

The publish flow expects an `RV_ECR_IMAGE=<repo>:<tag>` style value when you build a custom image flow.

## Helper script

`scripts/render_docker_run_command.py` prints a Docker command line instead of running Docker. It is useful when you want to inspect or share the command before execution.
