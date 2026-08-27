# CLI and Serving Workflows

## When to read

Read this when the user wants a local answer from an image, an interactive CLI, or a serving stack with controller, worker, and Gradio.

## One-shot image answer

Use the `run_llava` module when you want a single answer for one image and one prompt.

```bash
python -m llava.eval.run_llava \
  --model-path <checkpoint-or-hub-id> \
  --image-file <path-or-url> \
  --query "<question>" \
  --temperature 0 \
  --num_beams 1
```

Useful options:

- `--model-base` for LoRA-style or base-model-dependent checkpoints
- `--conv-mode` when the auto-selected template is not right for the model family
- `--top_p`, `--num_beams`, `--max_new_tokens` for decode control
- `--temperature 0` for deterministic greedy-style output

## Interactive CLI

```bash
python -m llava.serve.cli \
  --model-path <checkpoint-or-hub-id> \
  --image-file <path-or-url> \
  --device cuda \
  --temperature 0.2
```

Use `--device mps` only on supported macOS Apple Silicon workflows. Avoid 4-bit/8-bit flags on macOS and Windows.

## Serving stack order

1. Start the controller.
2. Start one or more model workers.
3. Start the Gradio web server.
4. Refresh the UI after a worker registers.

Example order:

```bash
python -m llava.serve.controller --host 0.0.0.0 --port 10000
python -m llava.serve.model_worker --host 0.0.0.0 --controller-address http://localhost:10000 --worker-address http://localhost:40000 --port 40000 --model-path <checkpoint>
python -m llava.serve.gradio_web_server --controller-url http://localhost:10000 --host 0.0.0.0 --port 7860 --model-list-mode reload
```

## Worker flags that matter

- `--model-path` names the loaded checkpoint or hub id.
- `--model-base` is required for LoRA/adapter-style loading when the checkpoint does not already contain the merged weights.
- `--device` defaults to CUDA.
- `--load-8bit` and `--load-4bit` reduce memory use when bitsandbytes is installed and the backend supports it.
- `--use-flash-attn` requests FlashAttention 2 if available.
- `--limit-model-concurrency` limits queued generation jobs per worker.

## Optional SGLang path

The package also contains `python -m llava.serve.sglang_worker`, which expects a running SGLang backend endpoint. Treat this as an optional alternative serving stack, not a baseline requirement.

## Deployment notes

- `predict.py` shows a Cog/Replicate-style predictor that downloads weights into a cache and streams one prediction per call.
- `cog.yaml` documents a containerized deployment shape with a GPU build and a fixed Python version. Use it as deployment evidence, not as a general runtime dependency.

## Common operator mistakes

- Starting the Gradio UI without a worker and expecting answers.
- Passing a LoRA checkpoint without `--model-base`.
- Forgetting to update the controller URL/port when multiple workers are launched.
- Using a conv mode that does not match the checkpoint family.
- Combining image tokens and image files incorrectly so the worker sees a count mismatch.
