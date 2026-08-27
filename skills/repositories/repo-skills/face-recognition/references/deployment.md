# Deployment Notes

## When to read

Read this when a task is about deploying an application that imports
`face_recognition`, using Docker or GPU acceleration, or packaging a standalone
binary. For ordinary API/CLI usage, start with [api-reference.md](api-reference.md)
or [cli-reference.md](cli-reference.md).

## Why deployment can be tricky

The package is small, but it depends on `dlib`, a compiled C++/Python package,
and on model files from `face_recognition_models`. Cloud or container failures
often come from one of these layers:

- no compatible wheel for the Python/platform combination;
- missing compiler, CMake, or system libraries when building `dlib`;
- missing `face_recognition_models` package or model data;
- incompatible CUDA/NVIDIA driver/container runtime setup;
- GUI/display assumptions in examples that call OpenCV or Pillow viewers.

Use [troubleshooting.md](troubleshooting.md) for concrete symptoms and fixes.

## CPU Docker pattern

A CPU container should install Python, build/runtime libraries needed by dlib,
and the application requirements. The repository documents CPU images and a
Docker Compose workflow, but future agents should create or inspect the user's
current container files rather than depending on the original checkout.

A minimal application Dockerfile pattern is:

```Dockerfile
FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir face_recognition
COPY my_app /my_app
CMD ["python", "/my_app/app.py"]
```

If dlib wheels are available for the chosen base image, this can be simpler. If
they are not, expect a source build and allocate enough build time/memory.

## GPU/CUDA pattern

GPU acceleration matters mainly for the CNN detector and batch face detection.
It is optional for core correctness.

For GPU containers, the host must have compatible NVIDIA drivers and the NVIDIA
container runtime/toolkit. Inside the environment, verify dlib sees CUDA before
claiming acceleration:

```python
import dlib
print(dlib.DLIB_USE_CUDA)
print(dlib.cuda.get_num_devices())
```

If this reports no CUDA devices, use HOG/CPU routes or rebuild/install dlib with
CUDA support. Do not present a CPU import check as proof of GPU acceleration.

## Docker Compose and cloud hosts

The repository's deployment guidance uses Docker Compose for local testing and
notes that cloud hosts such as Heroku/AWS are easier when the compiled dlib
stack is inside a container. When adapting that pattern:

1. Keep application code and model/input data outside the image when they are
   user-specific.
2. Pin Python and dependency versions that have available wheels or a known
   build path.
3. Run `python -c "import face_recognition; print(face_recognition.__version__)"`
   and `face_detection --help` in the built container.
4. For GPU images, validate the NVIDIA runtime and `dlib.cuda.get_num_devices()`
   in the container, not only on the host.

## PyInstaller or standalone executables

Standalone executables require extra care because dlib binaries and
`face_recognition_models` data files must be collected into the package. If a
user asks for this:

- start from a small API script with one clear image input path;
- verify that the packaged binary can import `face_recognition` without a local
  Python environment;
- include model-data files explicitly if PyInstaller misses them;
- test on a clean machine/container, not only on the build host.

Do not promise PyInstaller support without a concrete build/test loop, because
hidden-import and data-file handling can vary by platform.
