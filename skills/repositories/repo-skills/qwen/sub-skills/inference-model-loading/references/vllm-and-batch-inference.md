# vLLM and Batch Inference Notes

## Batch generation recipe

Qwen chat batch generation is not just ordinary left-padded tokenization. The robust plan is:

1. Use a chat checkpoint and tokenizer with a pad token such as `<|extra_0|>` that differs from the end/control token.
2. Use left padding so the generated positions align across examples.
3. Build each chat prompt with the checkpoint's context construction helper or equivalent ChatML format.
4. Set `pad_token_id` on both model loading and generation config.
5. Track the padding length for each row and decode only the new response span.

Symptoms of a bad batch setup include responses containing the prompt, inconsistent lengths, generation stopping early across the whole batch, or attention-mask warnings.

## vLLM transformer-like wrapper behavior

The repository included a transformer-like vLLM wrapper pattern to expose a `chat(query, history=None, system=..., stop_words_ids=...)` method over vLLM generation. Treat that wrapper as evidence for behavior, not as a runtime dependency of this skill. Key facts to preserve:

- It builds ChatML-style context and stop-word ids from the checkpoint's tokenizer/config.
- It supports multi-turn history in the shape used by Qwen chat examples.
- It is meant for inference and serving; it does not implement fine-tuning or benchmark logic.
- Int4 models or GPUs below BF16-friendly generations may require `dtype="float16"` or equivalent vLLM dtype flags.

For service commands, read `../serving-deployment/references/vllm-fastchat.md`.

## When to choose vLLM

Choose vLLM when the user needs high-throughput serving, tensor parallelism, OpenAI-compatible serving, or efficient multi-GPU inference. Do not choose it merely for a first local import test. Check:

- vLLM wheel compatibility with Python, PyTorch/CUDA, and GPU compute capability.
- Whether the chosen Qwen checkpoint and remote code are supported.
- Tensor parallel size is compatible with available GPUs and quantization shape.
- Dtype is explicit for Int4 or older GPU generations.
- Chat template is supplied when using a standalone OpenAI-compatible vLLM server.

## Batch vs service routing

- If the user wants to generate several prompts inside a Python script, stay in this sub-skill and use the batch inference recipe.
- If the user wants an HTTP API, FastChat controller/worker, standalone vLLM API server, ports, Docker, or logs, route to serving-deployment.
