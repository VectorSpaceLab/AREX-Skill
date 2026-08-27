# Programmatic usage

## Local reasoning loop

`DeepAnalyzeVLLM` is the direct Python wrapper around a vLLM/OpenAI-compatible chat endpoint.

```python
from deepanalyze import DeepAnalyzeVLLM

runner = DeepAnalyzeVLLM(
    model_name="DeepAnalyze-8B",
    api_url="http://localhost:8000/v1/chat/completions",
    max_rounds=30,
)
result = runner.generate(
    prompt="Create a workspace artifact, then give a short final answer.",
    workspace="workspace/my-thread",
    temperature=0.5,
    max_tokens=32768,
    top_p=None,
    top_k=None,
)
print(result["reasoning"])
```

### What `generate()` does

1. Changes into the chosen workspace.
2. Sends the prompt to the model endpoint.
3. Looks for `<Code>` blocks in the model response.
4. Executes the extracted Python code locally.
5. Appends an `<Execute>` block with stdout/stderr.
6. Continues until the model emits `<Answer>` or the round limit is reached.

If a model reply has no `<Code>` and no `<Answer>`, it is treated as an intermediate reasoning step and the loop continues.

### `execute_code(code_str)`

`execute_code(code_str)` runs Python in-process with `exec(code_str, {})` and captures stdout/stderr. It is useful for quick CPU smoke checks, but it is **not** a sandbox. Only run trusted code.

## Tag contract at runtime

| Tag | Runtime meaning |
| --- | --- |
| `<Analyze>` | Planning or decomposition text that explains the next move |
| `<Understand>` | Reflection after execution or a concise interpretation of the result |
| `<Code>` | Python to execute locally or via the API runtime |
| `<Execute>` | Execution output, including stdout, stderr, or timeout text |
| `<File>` | Artifact-aware narrative section used when reporting generated files |
| `<Answer>` | Final answer marker; ends the loop |

The API server's report generator recognizes these tags when it assembles the final conversation report under the thread workspace.

## Workspace behavior

- Use a dedicated workspace per analysis thread.
- Relative paths inside executed code resolve against that workspace.
- The API server copies uploaded files into the thread workspace and preserves it when the same `thread_id` is reused.
- Generated artifacts are collected under the workspace's `generated/` directory and exposed through 8100 download URLs.

## When to use the API server instead

Use the OpenAI-compatible API server when you need:
- file upload/download
- generated file reporting
- multi-turn thread persistence
- safer subprocess-based code execution with a timeout
- streaming responses for client code

## CPU-safe smoke path

1. Start the mock vLLM endpoint with `scripts/mock_vllm_server.py` on port 8000.
2. Start the DeepAnalyze API server on port 8200.
3. Run `scripts/api_client_smoke.py` or `scripts/openai_client_smoke.py`.

That path exercises file upload, chat completions, streaming chunks, thread reuse, and generated file reporting without a real model.
