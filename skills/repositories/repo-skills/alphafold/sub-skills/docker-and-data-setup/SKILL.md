---
name: docker-and-data-setup
description: "Plan AlphaFold Docker execution, database/model-parameter
  acquisition, update flows, and safe dry-run command construction without
  starting containers or downloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Docker and Data Setup

Use this sub-skill when an AlphaFold task is about installation prerequisites, Docker image/run planning, GPU runtime checks, database and model-parameter layout, full-vs-reduced database choices, data updates, or safe construction of setup commands.

Do not run Docker builds, Docker containers, database downloads, or model-parameter downloads automatically. AlphaFold setup commonly requires hundreds of GB to multiple TB of storage, network transfer, a Docker daemon, and GPU/container runtime access; treat those operations as user-supervised external work.

## Fast Routing

- For Docker prerequisites, image build planning, GPU runtime signals, mount mapping, and dry-run launcher command construction, read [references/docker-workflow.md](references/docker-workflow.md) and use [scripts/plan_docker_command.py](scripts/plan_docker_command.py).
- For database/model-parameter acquisition, expected data directory layout, full vs reduced mode, and incremental update ordering, read [references/data-layout.md](references/data-layout.md) and use [scripts/plan_data_downloads.py](scripts/plan_data_downloads.py).
- For setup failures such as repo-nested data directories, missing `aria2c`/`rsync`, missing NVIDIA runtime, permissions, database-preset mismatches, and GPU relax instability, read [references/troubleshooting.md](references/troubleshooting.md).
- For FASTA content/schema validation, route to `input-data-and-formats`; this sub-skill only checks filesystem path and basename constraints needed for Docker planning.
- For prediction flag semantics, model-output files, confidence interpretation, or direct `run_alphafold` execution, route to `prediction-cli` and `outputs-and-confidence`.

## Safe Helper Usage

Run only the bundled helpers below during agent-driven setup planning:

```bash
python sub-skills/docker-and-data-setup/scripts/plan_docker_command.py --help
python sub-skills/docker-and-data-setup/scripts/plan_data_downloads.py --help
```

The helpers only inspect local paths and print plans. Any Docker build/run command or official downloader command they describe is a user-supervised external operation, not an agent-run validation step.

## Minimum Public Facts

- Public package/distribution version covered here: `alphafold` `2.3.2`.
- Public Python requirement from package metadata: Python `>=3.10`.
- Docker launcher dependencies are `absl-py==1.0.0` and `docker==5.0.0`, but the bundled command planner does not import `docker`.
- Full prediction setups require external genetic databases, model parameters, HMMER/HH-suite/Kalign tooling inside the runtime environment, and typically a Linux host with NVIDIA GPU/container runtime support.
