# DeepVariant Install and Runtime Guidance

Use this reference before recommending any DeepVariant command that runs a binary, container, GPU workload, or source build. The generated helpers in this skill are safe command planners; production DeepVariant execution has heavier runtime requirements.

## Runtime Surfaces

| Surface | Use when | Notes |
| --- | --- | --- |
| Released Docker image | Most official DeepVariant, DeepTrio, and pangenome-aware workflows. | Commands normally call `/opt/deepvariant/bin/run_deepvariant`, `/opt/deepvariant/bin/deeptrio/run_deeptrio`, or `/opt/deepvariant/bin/run_pangenome_aware_deepvariant` inside the image. |
| Singularity/Apptainer | HPC environments where Docker is unavailable. | Preserve the same container-visible paths used by the Docker command; bind every input, output, model, region, and log directory. |
| Bazel/source-built binaries | Development or environments with a checked-out source tree and compiled dependencies. | Requires a full build toolchain and is not implied by Python package import success. Ask before host mutation or long builds. |
| Lightweight Python package import | Skill generation, metadata inspection, and static helper use. | Confirms package metadata and import roots only; it does not prove TensorFlow, compiled Nucleus/DeepVariant modules, or container binaries are runnable. |

## Minimal Runtime Review

Before execution, confirm:

- DeepVariant version or image tag matches the intended workflow and model documentation.
- The selected image includes the desired runner: standard DeepVariant, DeepTrio, or pangenome-aware DeepVariant.
- The host has Docker or Singularity privileges and enough CPU, memory, disk, and temporary space for selected shards.
- GPU use is explicitly requested and the selected image/runtime can see compatible NVIDIA devices; CPU-only commands remain valid unless the user needs acceleration.
- Every host path is mounted into the container at exactly the path used in flags.
- Output parents, logging directories, intermediate directories, and custom model directories are writable inside the container.
- Network downloads, image pulls, truth-set downloads, GLnexus, hap.py, Beam/Dataflow, and cloud bucket access are approved before running.

## Docker Mount Pattern

Prefer stable container paths:

```bash
docker run \
  -v /host/input:/input \
  -v /host/output:/output \
  google/deepvariant:1.10.0 \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/input/ref.fa \
  --reads=/input/sample.bam \
  --output_vcf=/output/sample.vcf.gz \
  --num_shards=16
```

Rules:

- Do not mix host paths and container paths in one command.
- Mount parent directories, not individual files, when several index companions must be visible.
- For CRAM input, mount both the CRAM/CRAI and the FASTA/FAI used for decoding.
- For custom models, mount the model directory containing checkpoint or SavedModel files and matching metadata.
- For pangenome-aware runs, mount the GBZ path and ensure shared-memory needs are reviewed separately.

## GPU Notes

DeepVariant can use CPU-only workflows, and GPU acceleration is workflow/image dependent. Before adding GPU flags:

- Confirm the user asked for GPU and the image supports the intended GPU path.
- Confirm `nvidia-smi` works on the host if the user expects NVIDIA runtime support.
- Use Docker GPU flags only when the host has NVIDIA container runtime configured.
- Do not install or upgrade GPU drivers, CUDA, TensorFlow wheels, or container runtimes without explicit approval.

## Source Build and Python Package Caveats

The repository exposes a Python package named `deepvariant` with version `1.10.0`, but the official user entry points are packaged binaries/wrappers rather than console scripts. Python import success is useful for static inspection and metadata, not for production execution. Full stage execution can require TensorFlow, compiled C++/pybind modules, Nucleus genomics IO, Bazel-built binaries, and user data.

If a user asks to build from source:

1. Confirm they need a source build instead of a released container.
2. Check whether the request is repository-maintenance work or workflow usage.
3. Ask before installing system packages, Bazel, TensorFlow, Docker, CUDA, or other broad dependencies.
4. Treat build and environment failures as host-specific; keep public workflow advice separate from private setup details.

## When to Stop

Stop and ask for confirmation before:

- Pulling large images or datasets.
- Running Docker/Singularity, GLnexus, hap.py, TensorFlow training, Beam/Dataflow, or full DeepVariant stages.
- Mutating host runtime packages, GPU drivers, Docker configuration, or user environments.
- Running commands that write outside approved output directories.
