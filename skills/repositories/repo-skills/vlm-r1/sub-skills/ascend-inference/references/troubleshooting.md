# Ascend inference troubleshooting

Use this checklist when VLM-R1 OVD deployment on Ascend fails. These are hardware-specific recipes; the construction host did not run Ascend NPU verification.

## Device initialization failure

Common symptoms:

- The server exits while initializing NPU context.
- `torch_npu` or ACL reports a device-selection failure.
- `npu-smi` is not found or shows no usable device.
- A container starts but cannot see `davinci` devices.

Triage:

1. On the Ascend host, run `npu-smi info` before starting a container or XLLM server. If it fails, fix the host driver/runtime first.
2. Confirm the selected device is exposed to the runtime. A single-device vllm-ascend container normally needs `davinci0`, `davinci_manager`, `devmm_svm`, and `hisi_hdc` device nodes.
3. Confirm CANN/driver/DCMI/npu-smi files are mounted into the container according to the local Ascend installation layout. Do not assume one host's driver directories match another host.
4. Set or keep `PYTORCH_NPU_ALLOC_CONF=max_split_size_mb:256` when using the vllm-ascend recipe.
5. For XLLM or bare Python environments, test explicit NPU selection:

   ```bash
   python3 -c "import torch; import torch_npu; torch_npu.npu.set_device('npu:0'); print('npu:0 selected')"
   ```

6. If multi-device visibility is restricted by site policy, set the site-approved Ascend visible-device environment variable before server launch.
7. If the failure persists only in Docker, compare host versus container visibility for `npu-smi` and the device nodes; it is usually a bind-mount/device-pass-through problem rather than a VLM-R1 prompt problem.

## Wrong hardware/image combination

- Atlas 800T A2 / 910B vllm-ascend evidence uses image tag `v0.10.0rc1`.
- Atlas 300I Duo vllm-ascend evidence uses image tag `v0.10.0rc1-310p`.
- XLLM evidence is for Atlas 800T A2 / 910B only.

If a server fails before model loading, verify that the container or XLLM build matches the accelerator generation.

## dtype or model metadata errors

Symptoms include unsupported dtype messages, NPU kernel errors early in model load, or repeated failures on Atlas 300I Duo.

Actions:

- For Atlas 300I Duo, use `--dtype float16` in vllm-ascend server commands and `dtype="float16"` in offline vLLM scripts.
- If the downloaded model metadata forces bfloat16, adjust it to float16 for the 300I Duo deployment copy.
- For Atlas 800T A2 / 910B, the distilled vllm-ascend recipe does not require an explicit dtype, but adding `--dtype float16` can be a reasonable diagnostic if bf16 kernels are unavailable in the user's image.
- Keep `--max-model-len 16384` as the starting point. If memory errors appear, reduce model length, generation tokens, or image count before changing the prompt.

## vllm-ascend server starts but client fails

Checklist:

1. Confirm the server log says it is listening on the expected host and port.
2. Confirm the client uses `http://<host>:<port>/v1/chat/completions`.
3. Confirm the payload `model` value matches the served model id/path expected by the server.
4. Use `image_url` content for online chat requests. Use `image` content only for offline local-image chat-template scaffolds.
5. Keep the content list multimodal: one image item followed by one text prompt item.
6. If the error is a request-size or image-processing error, try a smaller image or lower the offline `max_pixels` before changing engine settings.

## XLLM build or startup failures

Build-time issues:

- Missing submodules: initialize and update XLLM submodules before installing requirements.
- Missing vcpkg: let the build fetch it or set `VCPKG_ROOT` to a prepared vcpkg checkout.
- Triton ARM package missing: build/install Triton from source before compiling XLLM.
- Missing headers under XLLM kernels: copy the required `xllm_kernels` include subfolders into the XLLM project kernel directory and reset `XLLM_KERNELS_PATH` to that directory.
- Missing pre-commit: install `pre-commit` in the build environment if setup requires it.

Server-start issues:

- Render the command with `scripts/ascend_server_client_templates.sh --engine xllm --action server ...` so `--backend=vlm`, `--model`, `--port`, `--max_memory_utilization`, and `--model_id` are all present.
- If memory pressure appears, lower `--max_memory_utilization`, reduce concurrent clients, or shorten generation length.
- If the client receives `model not found`, align the JSON `model` field with XLLM's `--model_id`.

## Prompt or JSON-answer quality problems

The normalized OVD prompt expects:

```json
{
  "answer": "yes or no",
  "explanations": [
    {"bbox_2d": [0, 0, 10, 10], "label": "object-label"}
  ]
}
```

Troubleshooting steps:

- Preserve the Chinese instruction that asks for a short `<description>...</description>` plus a final JSON object.
- If no object is relevant, instruct the model that `explanations` may be `None`.
- Keep bounding boxes as `[x1, y1, x2, y2]` numbers in image coordinates. Do not mix normalized and pixel coordinates unless the downstream evaluator expects it.
- Source examples used function-call sentinels inconsistently. Prefer the normalized prompt generated by the bundled scripts; only add function-call sentinels if the downstream service requires them.
- If output includes fenced JSON, strip the fence before scoring or parsing.

## evalscope and performance diagnosis

- For XLLM's VLM backend, do not use pure text load-generation as a substitute for multimodal traffic. The source performance note requires evalscope request construction to send a text-image multimodal message.
- Keep `random_vl`, one image per request, and the same token bounds when comparing against the distilled numbers.
- Compare generated tokens/second, TTFT, TPOT, latency percentiles, and success rate together; a higher concurrency throughput number can hide worse first-token latency.
- Start with concurrency 1 and a small request count before running the full sweep.
- If success rate drops below 100%, collect server logs before tuning performance flags.

## What not to diagnose here

- CUDA GRPO training, DeepSpeed, LoRA, JSONL reward methods, and CUDA REC/OVD evaluation are outside this sub-skill.
- Full model accuracy problems should route to the evaluation sub-skill after inference outputs are saved.
- Missing local datasets or VLM-R1 training image folders are not part of Ascend serving setup.
