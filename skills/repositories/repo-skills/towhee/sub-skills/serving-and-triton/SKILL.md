---
name: serving-and-triton
description: "Construct Towhee API services and Triton-serving artifacts while
  avoiding routine side-effectful server, Docker, or GPU execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Towhee Serving and Triton

Use this sub-skill when the task is about exposing Towhee pipelines/functions as
HTTP or gRPC services, shaping `towhee server` commands, planning Triton model
repositories/images, or calling a Towhee Triton pipeline remotely.

## Route first

- For `APIService`, `api_service.build_service`, route registration, HTTP/gRPC
  startup command shapes, and client request expectations, use
  [service workflows](references/service-workflows.md).
- For `AutoConfig.TritonCPUConfig`, `AutoConfig.TritonGPUConfig`,
  `towhee.build_pipeline_model`, `towhee.build_docker_image`, Triton model
  repository layout, Docker/GPU prerequisites, and `triton_client.Client`, use
  [Triton workflows](references/triton-workflows.md).
- For import/dependency failures, schema mistakes, port conflicts, Docker daemon
  issues, GPU/CUDA mismatches, oversized images, or decisions to stop instead of
  launching side-effectful builds, use [troubleshooting](references/troubleshooting.md).
- For routine validation, run [the API service smoke script](scripts/api_service_smoke.py).
  It constructs service objects and an optional tiny local pipeline only; it does
  not start HTTP/gRPC servers, Docker, Triton, or GPU work.

## Operating boundaries

- Keep routine checks local and object-level. Do not start long-lived web
  servers, `docker build`, `docker run`, `tritonserver`, or GPU jobs unless the
  user explicitly asks for deployment and has confirmed the environment.
- Treat pipeline authoring details as owned by the Towhee pipeline-programming
  skill; this sub-skill covers how an already chosen pipeline/service is exposed
  or packaged for serving.
- Prefer explicit route paths, explicit IO models, and a small smoke call of the
  Python route function before advising live HTTP/gRPC or Triton deployment.
