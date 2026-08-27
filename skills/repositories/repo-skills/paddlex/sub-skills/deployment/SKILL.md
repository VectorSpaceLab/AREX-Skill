---
name: deployment
description: "Deploy PaddleX pipelines and models with high-performance
  inference, serving, Paddle2ONNX, GenAI client/server, backend plugins, and
  hardware-specific runtime caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PaddleX deployment

Use this sub-skill when the user wants to deploy, accelerate, serve, convert, or host PaddleX outputs. Typical requests mention high-performance inference (HPI), `use_hpip`, serving, high-stability serving, Paddle2ONNX, ONNX/TensorRT/OpenVINO, `paddlex --install`, `paddlex_genai_server`, GenAI client/server, or hardware-specific runtime setup.

Route away from this sub-skill when the task is:

- ordinary pre-trained pipeline prediction or pipeline config export — use `../pipelines/` first.
- dataset checking, training, evaluation, export from a module config, or `create_model` prediction — use `../modules/` first.

## Start here

1. Identify the deployment family: HPI, serving, high-stability serving, Paddle2ONNX, GenAI client/server, or on-device/accelerator-specific packaging.
2. Confirm the source artifact: built-in pipeline name/YAML, exported module inference directory, or GenAI model/backend config.
3. Confirm plugins and backends before running deployment commands. PaddleX separates the base package from deployment plugins.
4. Keep GPU/TensorRT/vendor-accelerator claims conditional on the installed PaddlePaddle/backend stack.

Read `references/deployment-overview.md` for command patterns and backend boundaries. Read `references/deployment-troubleshooting.md` for plugin, HPI, server, GenAI, Paddle2ONNX, and hardware failures.

## Common plugin installs

```bash
paddlex --install serving
paddlex --install paddle2onnx
paddlex --install hpi-cpu
paddlex --install hpi-gpu
paddlex --install genai-client
paddlex --install genai-vllm-server
paddlex --install genai-sglang-server
```

Install only the plugin needed for the selected workflow. Do not install GPU/HPI/GenAI server stacks merely for a CPU pipeline smoke.

## Minimal command patterns

```bash
# Pipeline serving.
paddlex --serve --pipeline image_classification --host 0.0.0.0 --port 8080

# Pipeline prediction with HPI enabled when the environment supports it.
paddlex --pipeline image_classification --input demo.jpg --save_path output --use_hpip

# Paddle2ONNX conversion of an exported Paddle model directory.
paddlex --paddle2onnx --paddle_model_dir ./inference_model --onnx_model_dir ./onnx --opset_version 7

# GenAI server entry point for supported backends/models.
paddlex_genai_server --help
```

## Bundled helper

Use `scripts/check_deployment_options.py` to inspect installed plugin/import availability and print the deployment commands this skill expects.

```bash
python scripts/check_deployment_options.py
```

This helper is read-only; it does not install plugins or start servers.

## Boundary reminders

- HPI and serving are pipeline/runtime deployment concerns; they do not replace module training or export.
- Paddle2ONNX expects an exported Paddle inference model directory, not an arbitrary training checkpoint.
- GenAI client pipelines need a server URL or equivalent backend configuration when using remote/server-backed models.
- On-device and vendor accelerator paths require platform-specific SDK/toolchain prerequisites and are reference/advanced workflows unless explicitly prepared.
