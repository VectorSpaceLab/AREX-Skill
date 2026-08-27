# Model Workflows

## Choosing the LazyLLM model abstraction

| Task | Prefer | Required evidence before execution |
| --- | --- | --- |
| Online chat/completion provider | `OnlineChatModule` or `OnlineModule` | provider/source, model name, API key or endpoint, timeout/budget, whether streaming/tool-calls are needed |
| Local model inference or serving | `TrainableModule` plus `ServerModule` or deploy CLI | model path/cache, backend extra, GPU/CPU capacity, port/security key, launcher type |
| Deterministic Python action in a graph | `ActionModule` or a plain callable inside flow primitives | input/output shape and side effects |
| Wrap an existing module/function as a service | `ServerModule` | port, launcher, pre/post processors, replicas, security key |
| Fine-tune or distill | `TrainableModule` and selected finetune framework | dataset path/format, framework extra, GPU, time/budget, output target path |
| Multimodal online tasks | online module with model type/category | provider SDK/extra, file formats, credentials, model category |

## Provider-safe planning sequence

1. Identify provider/source and model name.
2. Use model type mapping to classify the name when the task depends on modality.
3. Inspect constructor parameters and message formatting locally.
4. Ask for credentials and budget before making real provider calls.
5. Keep streamed tool-call merging and history-sanitization tests separate from provider execution.

No-network helpers:

```bash
python scripts/model_surface_smoke.py
python ../../scripts/inspect_lazyllm_surface.py --include-optional
```

## Online chat/tool-call utilities

LazyLLM online chat internals include utilities that tests exercise without network:

- specific detection of provider input-inspection failures,
- removal of prior tool traces while preserving current tool observations,
- merging streamed tool-call chunks by `index`,
- preserving list shape when a stream contains one `choice` or one `tool_call`.

Use these checks when a provider response has malformed tool calls or conversation history contains untrusted prior tool payloads.

## Local serving and fine-tuning sequence

1. Confirm the selected backend and extra (`vllm`, `lmdeploy`, `lightllm`, `llama-factory`, `deploy-all`, `finetune-all`, or `standard/full`).
2. Confirm model path/cache and whether `trust_remote_code` is acceptable.
3. Confirm GPU memory, CUDA/runtime compatibility, and service port.
4. Start with a tiny import/signature check before launching the model.
5. For `ServerModule`, decide whether `m` is a module object, function, local path/name, or URL. Set `pre`, `post`, `stream`, `return_trace`, `port`, `launcher`, `url`, `num_replicas`, and `security_key` intentionally.

## Example families distilled from the repo

- Chatbot and online chatbot examples demonstrate basic model wrapping and CLI chatbot modes.
- Multimodal chatbot, painting, OCR, TTS, and STT examples are provider/backend dependent and should be treated as optional execution paths.
- Distillation/fine-tuning examples require local training backends and model/data budget.
- RAG examples combine model modules with document retrieval; route retrieval setup to the RAG sub-skill.
- Story/flow examples combine modules with `pipeline`/`parallel`; route graph semantics to flow-orchestration.

## Validation expectations

Use CPU tests for model helpers when the user asks for guidance or code planning. Only run provider/GPU jobs when explicitly selected:

- Safe native candidates: model type mapping and online chat history/stream utility tests.
- Optional provider candidates: online chatbot and charge tests.
- Optional GPU/model candidates: local `TrainableModule` examples, vLLM deployment, fine-tuning, distillation, multimodal generation.
