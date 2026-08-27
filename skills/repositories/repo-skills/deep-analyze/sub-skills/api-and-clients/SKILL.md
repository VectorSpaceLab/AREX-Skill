---
name: "api-and-clients"
description: "Use DeepAnalyze from Python, OpenAI-style clients, and the API server."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# api-and-clients

Use this sub-skill when the task is about:
- `DeepAnalyzeVLLM(model_name, api_url='http://localhost:8000/v1/chat/completions', max_rounds=30)` and `generate(prompt, workspace, temperature=0.5, max_tokens=32768, top_p=None, top_k=None)`
- `execute_code(code_str)` and the `<Analyze>`, `<Understand>`, `<Code>`, `<Execute>`, `<File>`, and `<Answer>` runtime contract
- `POST /v1/files`, `GET /v1/files/{file_id}`, `GET /v1/files/{file_id}/content`, `DELETE /v1/files/{file_id}`, `POST /v1/chat/completions`, `/v1/models`, `/health`, and `/v1/admin/*`
- requests and OpenAI client flows that place `file_ids` on the latest user message and `thread_id` on the latest user message when continuing a conversation
- streaming chunks, generated file reporting, and persistent thread workspaces

Start with these local references:
- `references/api-reference.md`
- `references/programmatic-usage.md`
- `references/case-study-patterns.md`
- `references/troubleshooting.md`

Use these bundled scripts:
- `scripts/deepanalyze_vllm_smoke.py`
- `scripts/api_client_smoke.py`
- `scripts/openai_client_smoke.py`
- `scripts/mock_vllm_server.py`

Route away when the task is mainly:
- browser UI, Jupyter, or CLI navigation -> `interactive-frontends`
- vLLM launch, model download, memory, or quantization -> `model-serving`
- SFT, RL, benchmarks, or other training/evaluation -> `training-and-evaluation`
