# Container deployment reference

The checked-in `Dockerfile` is a reference image recipe, not a portable proof
of runtime support. It uses `nvidia/vulkan:1.3-470`, Ubuntu 20.04-oriented
packages, downloads CARLA, optionally downloads AdditionalMaps, optionally
installs PyTorch/YOLOv5 and SUMO, then installs OpenCDA. Build arguments are:

- `USER` (default `opencda`);
- `CARLA_VERSION` (default `0.9.12`);
- `ADDITIONAL_MAPS` (default `true`);
- `PERCEPTION` (default `true`);
- `SUMO` (default `true`);
- `OPENCDA_FULL_INSTALL` (default `true`).

Invalid values are rejected by shell branches during the build. `CARLA_HOME`
and `SUMO_HOME` are set inside the image. The Dockerfile's default CARLA
version is 0.9.12, while the CLI defaults to 0.9.11; always align the `-v`
argument, client API, server binary, and image build argument.

## Build and run pattern

From the directory containing the Dockerfile, the upstream usage is:

```bash
docker build -t opencda:local .
docker run --privileged --gpus all --network=host \
  -e DISPLAY="$DISPLAY" \
  -v /usr/share/vulkan/icd.d:/usr/share/vulkan/icd.d \
  -it opencda:local /bin/bash
```

The exact GPU, Vulkan, X11, and Xauthority mounts depend on the host. A
rendered run may additionally need `SDL_VIDEODRIVER=x11`, `XAUTHORITY`, and
`/tmp/.X11-unix`/Xauthority mounts. Granting X access or using `--privileged`
has host security implications; use the least privilege compatible with the
chosen headless/rendered mode.

If `OPENCDA_FULL_INSTALL=false`, the image installs requirements only; mount
the source at runtime and install/configure its CARLA API separately. If true,
the Dockerfile clones the upstream main branch during build, so it is not a
reproducible substitute for this pinned source unless the image recipe is
modified to use the desired source revision. Network access and upstream
release availability are build prerequisites.

The Docker comments note that OpenSCENARIO is not supported in the image.
SUMO and perception are optional build layers, but enabling them does not
prove that their runtime data, model weights, CUDA driver, or maps are
usable. Verify `nvidia-smi`, `vulkaninfo --summary` (if rendered),
`python -c "import carla"`, and the selected external server/map separately.
