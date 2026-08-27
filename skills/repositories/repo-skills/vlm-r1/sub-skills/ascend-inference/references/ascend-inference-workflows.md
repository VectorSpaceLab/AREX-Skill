# Ascend inference workflows for VLM-R1 OVD

This reference is self-contained operating knowledge for deploying VLM-R1 OVD checkpoints on Huawei Ascend hardware. It distills the repository's Ascend examples into reusable recipes and templates; do not depend on source-tree files at runtime.

## Supported targets

| Target hardware | Engine | Evidence-backed scope | Important settings |
| --- | --- | --- | --- |
| Atlas 800T A2 / 910B | `vllm-ascend` | Docker container, offline vLLM Python inference, OpenAI-compatible server/client, evalscope performance recipe. | Container image tag `quay.io/ascend/vllm-ascend:v0.10.0rc1`; `max_model_len=16384`; `enforce_eager`; multimodal image limit up to 10. |
| Atlas 300I Duo | `vllm-ascend` | Docker container, offline vLLM Python inference, OpenAI-compatible server/client. | Container image tag `quay.io/ascend/vllm-ascend:v0.10.0rc1-310p`; use `dtype=float16`; if model metadata declares bfloat16, update it to float16 for this deployment. |
| Atlas 800T A2 / 910B | XLLM | Build XLLM, run VLM backend server, send OpenAI-compatible client requests, compare performance. | Built XLLM executable; `--backend=vlm`; set `--model`, `--port`, `--model_id`, and `--max_memory_utilization`. |
| Atlas 300I Duo | XLLM | No distilled XLLM recipe. | Use `vllm-ascend` unless the user supplies separate validated XLLM-on-300I evidence. |

Ascend deployment was not executed during skill construction because the construction host had no visible Ascend NPU/runtime. Treat all Ascend operations as hardware-specific recipes until validated on the user's Ascend host.

## Common model and request assumptions

- Default checkpoint id: `omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321`.
- Placeholder local model directory: `VLM-R1-Qwen2.5VL-3B-OVD-0321`.
- Request type: VLM-R1 OVD asks whether an event/object is present and returns a Chinese description plus a JSON answer containing `answer` and `explanations`.
- Online serving endpoint: OpenAI-compatible chat completions at `http://<host>:<port>/v1/chat/completions`.
- Offline request shape: Qwen-VL chat template plus `multi_modal_data={"image": image_inputs}` passed to `vllm.LLM.generate`.

A safe model acquisition command, when a local checkpoint is not already present, is:

```bash
MODEL_ID="omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321"
MODEL_DIR="VLM-R1-Qwen2.5VL-3B-OVD-0321"
huggingface-cli download --resume-download "$MODEL_ID" --local-dir "$MODEL_DIR"
```

## vllm-ascend container recipe

Select the image by hardware:

```bash
# Atlas 800T A2 / 910B
ASCEND_VLLM_IMAGE="quay.io/ascend/vllm-ascend:v0.10.0rc1"

# Atlas 300I Duo
ASCEND_VLLM_IMAGE="quay.io/ascend/vllm-ascend:v0.10.0rc1-310p"
```

A typical container run needs the Ascend device nodes plus host driver/DCMI/npu-smi mounts. Adapt the variables to the target machine's Ascend driver layout before running:

```bash
ASCEND_VLLM_IMAGE="quay.io/ascend/vllm-ascend:v0.10.0rc1"
MODEL_DIR="VLM-R1-Qwen2.5VL-3B-OVD-0321"
HOST_MODEL_PARENT="$(pwd)"
ASCEND_DCMI_DIR="<host-dcmi-dir>"
ASCEND_DRIVER_LIB_DIR="<host-ascend-driver-lib-dir>"
ASCEND_DRIVER_VERSION_FILE="<host-ascend-driver-version-file>"
ASCEND_INSTALL_INFO="<host-ascend-install-info-file>"

# Run only on an Ascend host where the device nodes and driver files exist.
docker run --rm \
  --name vllm-ascend \
  --device /dev/davinci0 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  --mount type=bind,source="${ASCEND_DCMI_DIR}",target=/usr/local/dcmi,readonly \
  --mount type=bind,source="${ASCEND_DRIVER_LIB_DIR}",target=/usr/local/Ascend/driver/lib64,readonly \
  --mount type=bind,source="${ASCEND_DRIVER_VERSION_FILE}",target=/usr/local/Ascend/driver/version.info,readonly \
  --mount type=bind,source="${ASCEND_INSTALL_INFO}",target=/etc/ascend_install.info,readonly \
  --mount type=bind,source="${HOST_MODEL_PARENT}",target=/models \
  -e PYTORCH_NPU_ALLOC_CONF=max_split_size_mb:256 \
  -p 8000:8000 \
  -it "${ASCEND_VLLM_IMAGE}" bash
```

Inside the container, reference the model under `/models/${MODEL_DIR}` or another container-visible path. If the target is Atlas 300I Duo, use float16-serving settings and ensure the model metadata does not force bfloat16.

## vllm-ascend offline inference

Use `scripts/ascend_offline_request_template.py` to render a request-only JSON scaffold or a full vLLM Python skeleton. The renderer does not import `vllm` or execute inference.

Examples:

```bash
# Render a JSON message scaffold for review.
scripts/ascend_offline_request_template.py \
  --hardware a2 \
  --model-path "VLM-R1-Qwen2.5VL-3B-OVD-0321" \
  --image "resources/test.jpg" \
  --describe "杯子在哪个位置？请输出杯子的bbox坐标。" \
  --event "杯子" \
  --format messages

# Render a vLLM offline Python template for Atlas 300I Duo with float16.
scripts/ascend_offline_request_template.py \
  --hardware 300iduo \
  --model-path "VLM-R1-Qwen2.5VL-3B-OVD-0321" \
  --image "resources/test.jpg" \
  --format vllm-python \
  --output "rendered_ascend_offline_request.py"
```

The generated vLLM skeleton follows this pattern:

- `AutoProcessor.from_pretrained(MODEL_PATH)` applies the Qwen-VL chat template.
- `process_vision_info(messages, return_video_kwargs=True)` extracts image tensors.
- `LLM(model=MODEL_PATH, max_model_len=16384, limit_mm_per_prompt={"image": 10}, enforce_eager=True, dtype="float16" for 300I Duo)` creates the Ascend vLLM runtime.
- `SamplingParams(max_tokens=512)` bounds generation.
- `llm.generate([{"prompt": prompt, "multi_modal_data": {"image": image_inputs}}], sampling_params=...)` returns generated text.

## vllm-ascend online server and client

Render commands with `scripts/ascend_server_client_templates.sh` instead of editing hard-coded examples.

```bash
# Atlas 800T A2 / 910B vllm-ascend server.
scripts/ascend_server_client_templates.sh \
  --engine vllm \
  --action server \
  --hardware a2 \
  --model-path "VLM-R1-Qwen2.5VL-3B-OVD-0321" \
  --port 8000

# Atlas 300I Duo vllm-ascend server; renderer adds float16 unless overridden.
scripts/ascend_server_client_templates.sh \
  --engine vllm \
  --action server \
  --hardware 300iduo \
  --model-path "VLM-R1-Qwen2.5VL-3B-OVD-0321" \
  --port 8000

# OpenAI-compatible client request.
scripts/ascend_server_client_templates.sh \
  --engine vllm \
  --action client \
  --client-host localhost \
  --port 8000 \
  --model-id "VLM-R1-Qwen2.5VL-3B-OVD-0321" \
  --image-url "https://example.invalid/image.jpg" \
  --describe "杯子在哪个位置？请输出杯子的bbox坐标。" \
  --event "杯子"
```

The vllm-ascend server command should include:

```bash
vllm serve "${MODEL_PATH}" \
  --max-model-len 16384 \
  --limit-mm-per-prompt '{"image": 10}' \
  --enforce-eager \
  --port 8000 \
  --host 0.0.0.0 \
  --trust-remote-code
```

For Atlas 300I Duo, add `--dtype float16`.

## XLLM build and online inference

XLLM support is distilled for Atlas 800T A2 / 910B. It is not a drop-in replacement for the vllm-ascend container; it must be built before serving.

Build flow:

1. Clone the XLLM project and initialize submodules.
2. Ensure vcpkg is available; if it is pre-downloaded, set `VCPKG_ROOT` to that checkout.
3. Build/install Triton's ARM Python package from source before building XLLM.
4. Install XLLM development requirements and current `setuptools`/`wheel`.
5. Set `XLLM_KERNELS_PATH` to the directory containing the XLLM kernel files.
6. Install `pre-commit` if the build requires it.
7. Run either `python setup.py build` for an executable or `python setup.py bdist_wheel` for a wheel.

If compilation reports missing header files, copy the `xllm_kernels` include subfolders into the XLLM project's kernel directory and reset `XLLM_KERNELS_PATH` to the copied kernel directory. This is an XLLM build-environment issue, not a VLM-R1 model issue.

Render an XLLM server command:

```bash
scripts/ascend_server_client_templates.sh \
  --engine xllm \
  --action server \
  --xllm-binary "./build/xllm/core/server/xllm" \
  --model-path "VLM-R1-Qwen2.5VL-3B-OVD-0321" \
  --model-id "VLM-R1-Qwen2.5VL-3B-OVD-0321" \
  --port 8000 \
  --max-memory-utilization 0.90
```

The rendered server command should have the shape:

```bash
./build/xllm/core/server/xllm \
  --model="${MODEL_PATH}" \
  --backend=vlm \
  --port=8000 \
  --max_memory_utilization 0.90 \
  --model_id="${MODEL_ID}"
```

The XLLM client request uses the same OpenAI-compatible multimodal chat JSON as vllm-ascend; only the target port/host and `model` field must match the server.

## Chinese OVD prompt and JSON response format

The deployment examples ask the model to answer a Chinese object/event query in a structured format. Use this normalized prompt pattern unless the user supplies a task-specific prompt:

````text
请分析图像并回答以下问题。您的回答应包含对图像内容的简要描述和最终答案。描述使用 `<description></description>` 标签包裹。答案必须以 JSON 格式输出，包含 "answer"（"yes" 或 "no"），并提供相关物体的边界框坐标作为解释。如果没有涉及具体物体，则将 "explanations" 设为 "None"。输出格式如下：

<description>对图像内容的简要描述写在这里</description>

```json
{"answer": "yes or no", "explanations": [{"bbox_2d": [xx, xx, xx, xx], "label": "xxx"}]}
```

具体问题:根据规则或识别要求，{describe}。图中是否出现{event}？
````

Request payload shape for online serving:

```json
{
  "model": "VLM-R1-Qwen2.5VL-3B-OVD-0321",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "https://example.invalid/image.jpg"}},
        {"type": "text", "text": "<Chinese OVD prompt>"}
      ]
    }
  ]
}
```

Offline vLLM uses `{"type": "image", "image": "resources/test.jpg", "min_pixels": 50176, "max_pixels": 1003520}` in the message content before applying the chat template.

## evalscope performance caveat

The distilled performance evidence used evalscope with `random_vl` multimodal traffic, 512 generated tokens, one image per request, and concurrency/number sweeps of `1 2 4 8 16 32` and `4 8 16 32 64 128`.

A template benchmark command is:

```bash
MODEL_ID="VLM-R1-Qwen2.5VL-3B-OVD-0321"
MODEL_DIR="VLM-R1-Qwen2.5VL-3B-OVD-0321"
PORT=8000

evalscope perf \
  --parallel 1 2 4 8 16 32 \
  --number 4 8 16 32 64 128 \
  --model "$MODEL_ID" \
  --url "http://127.0.0.1:${PORT}/v1/chat/completions" \
  --api openai \
  --dataset random_vl \
  --max-tokens 512 \
  --min-tokens 512 \
  --prefix-length 0 \
  --min-prompt-length 100 \
  --max-prompt-length 100 \
  --image-width 640 \
  --image-height 640 \
  --image-format RGB \
  --image-num 1 \
  --tokenizer-path "$MODEL_DIR" \
  --extra-args '{"ignore_eos": true}'
```

For XLLM's VLM backend, the source performance note says pure text stress testing is not supported by that path; evalscope's connection/request construction must use a text-image multimodal message. Preserve this caveat in user-facing plans. Do not compare engines with text-only traffic.

Reported source-side highlights were that XLLM improved generated-token throughput versus vllm-ascend, including about 227% higher generated-token throughput at single concurrency and about 127% higher generated-token throughput at 32 concurrency. Treat those as source benchmark observations, not guaranteed numbers for a user's hardware or software stack.
