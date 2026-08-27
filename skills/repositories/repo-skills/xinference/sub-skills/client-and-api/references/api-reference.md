# API reference

This reference is distilled from the installed Xinference package signatures and the public REST route map.

## Base URL rules

- **Xinference endpoint**: `http://HOST:PORT`
  - Use this with `Client` and `AsyncClient`.
- **OpenAI-compatible base URL**: `http://HOST:PORT/v1`
  - Use this with OpenAI-style SDK calls and raw `/v1/...` HTTP requests.
- If cluster auth is enabled, send `Authorization: Bearer <token-or-api-key>`.
- A launched model UID is required for all request families.

## Installed client signatures

```text
Client(base_url, api_key: Optional[str] = None)
AsyncClient(base_url, api_key: Optional[str] = None)
RESTfulClient = Client
AsyncRESTfulClient = AsyncClient
```

### Model lifecycle

```text
Client.launch_model(
    model_name: str,
    model_type: str = 'LLM',
    model_engine: Optional[str] = None,
    model_uid: Optional[str] = None,
    model_size_in_billions: Union[int, str, float, NoneType] = None,
    model_format: Optional[str] = None,
    quantization: Optional[str] = None,
    replica: int = 1,
    n_worker: int = 1,
    n_gpu: Union[int, str, NoneType] = 'auto',
    peft_model_config: Optional[Dict] = None,
    request_limits: Optional[int] = None,
    worker_ip: Optional[str] = None,
    gpu_idx: Union[int, List[int], NoneType] = None,
    replica_config: Optional[List[Dict]] = None,
    model_path: Optional[str] = None,
    enable_thinking: Optional[bool] = None,
    enable_virtual_env: Optional[bool] = None,
    virtual_env_packages: Optional[List[str]] = None,
    envs: Optional[Dict[str, str]] = None,
    **kwargs,
) -> str

AsyncClient.launch_model(
    model_name: str,
    model_type: str = 'LLM',
    model_engine: Optional[str] = None,
    model_uid: Optional[str] = None,
    model_size_in_billions: Union[int, str, float, NoneType] = None,
    model_format: Optional[str] = None,
    quantization: Optional[str] = None,
    replica: int = 1,
    n_worker: int = 1,
    n_gpu: Union[int, str, NoneType] = 'auto',
    peft_model_config: Optional[Dict] = None,
    request_limits: Optional[int] = None,
    worker_ip: Optional[str] = None,
    gpu_idx: Union[int, List[int], NoneType] = None,
    replica_config: Optional[List[Dict]] = None,
    model_path: Optional[str] = None,
    enable_thinking: Optional[bool] = None,
    **kwargs,
) -> str
```

Notes:
- The sync launcher currently exposes the virtual-env fields; the async launcher in this build does not.
- `Client.list_model_registrations(model_type, detailed=False)` supports a `detailed` toggle; the async wrapper currently exposes `list_model_registrations(model_type)` only.

### Model lookup and teardown

```text
Client.get_model(model_uid: str) -> RESTfulModelHandle
AsyncClient.get_model(model_uid: str) -> AsyncRESTfulModelHandle
Client.list_models() -> Dict[str, Dict[str, Any]]
AsyncClient.list_models() -> Dict[str, Dict[str, Any]]
Client.terminate_model(model_uid: str)
AsyncClient.terminate_model(model_uid: str)
Client.register_model(model_type: str, model: str, persist: bool, worker_ip: Optional[str] = None)
AsyncClient.register_model(model_type: str, model: str, persist: bool, worker_ip: Optional[str] = None)
```

Other useful client methods:
- `describe_model(model_uid)`
- `list_cached_models(...)`
- `list_deletable_models(...)`
- `confirm_and_remove_model(...)`
- `query_engine_by_model_name(...)`
- `login(username, password)`
- `vllm_models()`

## Handle selection

`get_model(model_uid)` first inspects the launched model description and then returns a handle that matches the model type and ability:

- LLM + `chat` ability → chat handle
- LLM + `generate` ability → generate handle
- embedding → embedding handle
- rerank → rerank handle
- image → image handle
- audio → audio handle
- video → video handle
- flexible → flexible handle

If the model UID does not exist or the model is still loading, the lookup raises instead of guessing a handle.

## Request families and endpoints

| Family | Endpoint | Typical client path | Notes |
| --- | --- | --- | --- |
| Chat | `/v1/chat/completions` | `model.chat(...)` or `client.chat.completions.create(...)` | Messages required. Strict system-first models reject misplaced `system` messages. |
| Generate | `/v1/completions` | `model.generate(...)` or `client.completions.create(...)` | Prompt required. Use `stream=True` in the generation config when streaming. |
| Embeddings | `/v1/embeddings` | `model.create_embedding(...)` or `client.embeddings.create(...)` | Accepts `truncate_prompt_tokens`. |
| Token decode | `/v1/convert_ids_to_tokens` | `model.convert_ids_to_tokens(...)` | Useful for token-id inspection. |
| Rerank | `/v1/rerank` | `model.rerank(...)` or direct HTTP | Use JSON `documents` and `query`. |
| Audio transcription | `/v1/audio/transcriptions` | `model.transcriptions(...)` | Multipart upload with audio bytes. |
| Audio translation | `/v1/audio/translations` | `model.translations(...)` | Multipart upload with audio bytes. |
| Audio speech | `/v1/audio/speech` | `model.speech(...)` | Returns binary audio; streaming is supported. |
| Image generation | `/v1/images/generations` | `model.text_to_image(...)` | Text-to-image. |
| Image variation/edit | `/v1/images/variations`, `/v1/images/edits`, `/v1/images/inpainting` | `model.image_to_image(...)`, `model.image_edit(...)`, `model.inpainting(...)` | Multipart image inputs. |
| Image OCR | `/v1/images/ocr` | `model.ocr(...)` | Response is JSON, even when the OCR text is plain text. |
| Video generation | `/v1/video/generations`, `/v1/video/generations/image`, `/v1/video/generations/flf` | `model.text_to_video(...)`, `model.image_to_video(...)`, `model.flf_to_video(...)` | Multipart for image inputs. |
| Flexible infer | `/v1/flexible/infers` | `model.infer(...)` | Pass raw args/kwargs as requested by the model. |

## Validation and behavior notes

- `replica` is validated server-side and must be an integer-like value `>= 1`.
- `replica_config` cannot be combined with `worker_ip`, `n_gpu`, or `gpu_idx`.
- `CreateEmbeddingRequest.input` accepts text, token IDs, token sequences, and prompt-style dict inputs.
- `truncate_prompt_tokens` is optional and is preserved in the embedding request body.
- Some LLMs enforce strict system-message ordering; those requests fail fast with HTTP 400.
- Streaming responses are SSE-style chunks. The helper iterators consume `data:` lines and skip `[DONE]`.
- `Client.login()` and `AsyncClient.login()` only matter when the cluster advertises auth support.
