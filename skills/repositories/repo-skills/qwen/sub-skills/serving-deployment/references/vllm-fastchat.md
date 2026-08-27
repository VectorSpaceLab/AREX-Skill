# vLLM and FastChat Serving

## When to choose this route

Use vLLM/FastChat when the user wants throughput, tensor parallelism, an OpenAI-compatible service backed by vLLM, or efficient multi-GPU serving. For plain Python batch generation, use `../inference-model-loading/references/vllm-and-batch-inference.md` instead.

## FastChat + vLLM topology

The repository documents this service topology:

```bash
python -m fastchat.serve.controller
python -m fastchat.serve.vllm_worker --model-path $MODEL_PATH --trust-remote-code --dtype bfloat16
python -m fastchat.serve.openai_api_server --host localhost --port 8000
```

Then optional web UI:

```bash
python -m fastchat.serve.gradio_web_server
```

For multiple GPUs, add tensor parallelism to the worker:

```bash
python -m fastchat.serve.vllm_worker \
  --model-path $MODEL_PATH \
  --trust-remote-code \
  --tensor-parallel-size 4 \
  --dtype bfloat16
```

Use `--dtype float16` for Int4 checkpoints or GPUs where BF16 is not suitable. Keep tensor parallel size aligned with available GPUs and model/quantization constraints.

## Standalone vLLM OpenAI-compatible API

The vLLM recipe also supports standalone serving with a ChatML template:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model $MODEL_PATH \
  --trust-remote-code \
  --dtype bfloat16 \
  --chat-template template_chatml.jinja
```

Use `float16` for Int4 models or older GPU generations when BF16 is not supported.

## Compatibility checklist

- Check Python, vLLM, PyTorch, CUDA, and GPU compute capability compatibility before installing.
- Verify checkpoint directory completeness before service launch.
- For public APIs, add network controls outside the demo server.
- Keep model downloads and service start explicit; these commands are not safe smoke tests.
- If the worker starts but requests hang, inspect controller/worker/API logs separately and confirm the OpenAI server is talking to the right controller.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Worker fails at startup | unsupported dtype, missing checkpoint assets, incompatible vLLM wheel | switch dtype/checkpoint, pin compatible vLLM/PyTorch/CUDA, verify local files |
| Tensor parallel Int4 error | tensor parallel size not supported by quantized weight shape | use one GPU or a supported quantized layout |
| API reachable but no model response | controller/worker registration issue | inspect controller and worker logs before changing model flags |
| Chat formatting wrong | missing or wrong ChatML template | provide the Qwen ChatML template for standalone vLLM API |
