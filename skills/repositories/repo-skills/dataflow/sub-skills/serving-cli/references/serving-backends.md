# Serving backend reference

## Credential map

- `DF_API_KEY`
  - `APILLMServing_request`
  - `LiteLLMServing`
  - `APIVLMServing_openai`
  - `LightRAGServing`
- `GOOGLE_API_KEY`
  - `PerspectiveAPIServing`
- `GOOGLE_APPLICATION_CREDENTIALS`
  - `APIGoogleVertexAIServing`
- `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_GENAI_USE_VERTEXAI`
  - optional Vertex AI overrides

## Backend matrix

| Backend | Main use | Constructor facts | Start / cleanup behavior | Common warnings |
| --- | --- | --- | --- | --- |
| `APILLMServing_request` | Direct OpenAI-style chat and embeddings over HTTP | `api_url`, `key_name_of_api_key="DF_API_KEY"`, `model_name="gpt-4o"`, `temperature=0.0`, `max_workers=10`, `max_retries=5`, `connect_timeout=10.0`, `read_timeout=120.0`; deprecated `timeout` is still accepted | `start_serving()` is a no-op; `cleanup()` closes the `requests.Session` | Connect timeout raises `RuntimeError`; read timeout is downgraded to a warning and `None`; repeated keepalive bytes are fine as long as the final JSON arrives |
| `LiteLLMServing` | Multi-provider chat or embedding through LiteLLM | `serving_type="chat"|"embedding"`, `validate_on_init=True`, `api_url`, `key_name_of_api_key="DF_API_KEY"`, `model_name`, `api_version`, `temperature`, `max_tokens`, `top_p`, `timeout`, `custom_llm_provider` | `start_serving()` is a no-op; `cleanup()` clears references | Requires `litellm`; `validate_on_init=True` makes construction fail early if the backend is not usable |
| `LocalModelLLMServing_vllm` | Local text generation or embeddings with vLLM | `hf_model_name_or_path`, `hf_cache_dir`, `hf_local_dir`, `vllm_tensor_parallel_size`, `vllm_temperature`, `vllm_top_p`, `vllm_max_tokens`, `vllm_top_k`, `vllm_repetition_penalty`, `vllm_seed`, `vllm_max_model_len`, `vllm_gpu_memory_utilization` | Downloads from Hugging Face when the path is not local; `start_serving()` initializes vLLM; `cleanup()` tears down vLLM and CUDA state | Needs `vllm`; the implementation sets `VLLM_WORKER_MULTIPROC_METHOD=spawn`; `json_schema` uses guided decoding |
| `LocalModelLLMServing_sglang` | Local text generation with SGLang | `hf_model_name_or_path`, `hf_cache_dir`, `hf_local_dir`, `sgl_tp_size`, `sgl_dp_size`, `sgl_mem_fraction_static`, `sgl_max_new_tokens`, stop / regex / EBNF / structural tag options, `sgl_custom_params`, `sgl_stream_interval`, `sgl_logit_bias` | Downloads from Hugging Face when needed; `start_serving()` builds `sglang.Engine`; `cleanup()` shuts it down | Needs `sglang`; no embedding path is implemented |
| `LocalHostLLMAPIServing_vllm` | Local OpenAI-compatible vLLM subprocess server | `hf_model_name_or_path`, `hf_cache_dir`, `max_workers`, `vllm_server_port=12345`, `vllm_server_host="127.0.0.1"`, `vllm_tensor_parallel_size`, `vllm_temperature`, `vllm_top_p`, `vllm_max_tokens`, `vllm_top_k`, `vllm_max_model_len`, `vllm_gpu_memory_utilization`, `vllm_server_start_timeout=120` | `start_serving()` launches `python -m vllm.entrypoints.openai.api_server`; `cleanup()` kills the process group | Good when a separate API server is preferred over in-process generation |
| `LocalVLMServing_vllm` | Local vision-language generation with vLLM | `hf_model_name_or_path`, `vllm_tensor_parallel_size`, `vllm_temperature`, `vllm_top_p`, `vllm_max_tokens`, `vllm_max_model_len`, `vllm_top_k`, `vllm_repetition_penalty`, `vllm_seed`, `vllm_gpu_memory_utilization`, `vllm_limit_mm_per_prompt=1`, `trust_remote_code=True`, `enable_thinking=True`, `batch_size=128` | Downloads or loads a local VLM; `cleanup()` clears vLLM, distributed state, and GPU memory | Primarily tested with Qwen-VL family models; too many images per prompt can exceed `vllm_limit_mm_per_prompt` |
| `LocalModelLALMServing_vllm` | Local audio-language generation with vLLM | `hf_model_name_or_path`, `hf_cache_dir`, `hf_local_dir`, `vllm_tensor_parallel_size`, `vllm_temperature`, `vllm_top_p`, `vllm_max_tokens`, `vllm_top_k`, `vllm_repetition_penalty`, `vllm_seed=42`, `vllm_max_model_len`, `vllm_gpu_memory_utilization` | Downloads or loads a model; `cleanup()` deletes the model and empties CUDA cache | Needs `librosa`, `requests`, `numpy`, and `AutoProcessor`; audio inputs may be local files, URLs, base64, or bytes |
| `APIVLMServing_openai` | OpenAI-style vision-language API client | `api_url="https://api.openai.com/v1"`, `key_name_of_api_key="DF_API_KEY"`, `model_name="o4-mini"`, `max_workers=10`, `timeout=1800`, `temperature=0.0` | No local service to start; `cleanup()` closes the OpenAI client | Requires `openai`; supports single-image, multi-image, and JSON schema requests |
| `PerspectiveAPIServing` | Toxicity scoring through Google Perspective API | `max_workers=10` only; uses `GOOGLE_API_KEY` from the environment | No local service to start; `cleanup()` is a no-op | Requires Google API key and the `google-api-python-client` stack |
| `APIGoogleVertexAIServing` | Gemini / Vertex AI chat, function calling, and batch jobs | `model_name="gemini-2.5-flash"`, `project=None`, `location="us-central1"`, `max_workers=10`, `max_retries=5`, `temperature=0.0`, `max_tokens=4096`, `use_function_call=True`, `use_batch=False`, `batch_wait=True`, `batch_dataset="dataflow_batch"`, `csv_filename=None`, `bq_csv_filename=None` | No local service to start; batch mode may write temp CSV files, upload to BigQuery, and return a batch job name or wait for results | Requires `GOOGLE_APPLICATION_CREDENTIALS`; batch mode also needs BigQuery and Google GenAI clients |
| `LocalEmbeddingServing` | Local sentence-transformer embeddings | `model_name='all-MiniLM-L6-v2'`, `device=None`, `max_workers=2`, `max_retries=3` | Lazy model initialization; `cleanup()` clears the model and CUDA cache | Needs `torch` and `sentence_transformers`; on CPU, `max_workers>1` turns on a parallel code path that can use all available cores |
| `LightRAGServing` | Local LightRAG retrieval with OpenAI-compatible LLM and embeddings | `api_url="https://api.openai.com/v1"`, `key_name_of_api_key="DF_API_KEY"`, `llm_model_name="gpt-4o"`, `embed_model_name="bge-m3:latest"`, `embed_binding_host="http://localhost:11434"`, `embedding_dim=1024`, `max_embed_tokens=8192`, `document_list=[]` | Use `await LightRAGServing.create(...)` to initialize and load documents; `cleanup()` drops storages and finalizes | Requires `lightrag-hku`; this is a serving backend, but deeper document workflow design belongs to `document-vision-rag` |

## Selection hints

- Use `APILLMServing_request` when you already have an OpenAI-compatible HTTP server and want explicit timeout / retry control.
- Use `LiteLLMServing` when you want provider abstraction and optional embeddings in one interface.
- Use `LocalModelLLMServing_vllm` or `LocalModelLLMServing_sglang` for local text generation.
- Use `LocalVLMServing_vllm` or `APIVLMServing_openai` for image workflows.
- Use `LocalEmbeddingServing` for offline embeddings.
- Use `APIGoogleVertexAIServing` only when the Vertex AI / BigQuery credentials and client stack are present.
