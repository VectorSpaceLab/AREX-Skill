# Instrumentation Catalog

This catalog maps each generated instrumentation distribution to its import module, instrumentor class, entry point, and optional target library. Use it to choose between a direct wrapper and SDK selection, and to spot install-name mismatches before debugging imports.

## Notes

- `opentelemetry_instrumentor` entry-point names are not always the same as the distribution name.
- The `Install extra(s)` column shows the optional target dependency declared by each package.
- If the target client package is missing, some instrumentor modules fail at import time before `.instrument()` can run.
- Exact GenAI attribute names and migration tables live in the semantic-conventions sub-skill; this file stays at the wrapper-selection layer.

## Provider / router

| Distribution | Import module | Instrumentor class | Entry point | Install extra(s) | Important caveat |
| --- | --- | --- | --- | --- | --- |
| opentelemetry-instrumentation-alephalpha | `opentelemetry.instrumentation.alephalpha` | `AlephAlphaInstrumentor` | `aleph_alpha_client = opentelemetry.instrumentation.alephalpha:AlephAlphaInstrumentor` | aleph_alpha_client | Direct provider wrapper; keep the target client installed before importing the instrumentor. |
| opentelemetry-instrumentation-anthropic | `opentelemetry.instrumentation.anthropic` | `AnthropicInstrumentor` | `anthropic = opentelemetry.instrumentation.anthropic:AnthropicInstrumentor` | anthropic | Top-level import reaches anthropic streaming internals; supports messages, completions, and Bedrock paths. |
| opentelemetry-instrumentation-bedrock | `opentelemetry.instrumentation.bedrock` | `BedrockInstrumentor` | `boto3 = opentelemetry.instrumentation.bedrock:BedrockInstrumentor` | boto3; enrichment: anthropic>=0.17.0 | Wraps boto3 Bedrock calls; optional `anthropic` enrichment is declared separately. |
| opentelemetry-instrumentation-cohere | `opentelemetry.instrumentation.cohere` | `CohereInstrumentor` | `cohere = opentelemetry.instrumentation.cohere:CohereInstrumentor` | cohere | Direct provider wrapper; install the Cohere SDK first. |
| opentelemetry-instrumentation-google-generativeai | `opentelemetry.instrumentation.google_generativeai` | `GoogleGenerativeAiInstrumentor` | `google_generativeai = opentelemetry.instrumentation.google_generativeai:GoogleGenerativeAiInstrumentor` | google-genai | Install `google-genai`; the runtime import path is `google.genai` and the entry point key is `google_generativeai`. |
| opentelemetry-instrumentation-groq | `opentelemetry.instrumentation.groq` | `GroqInstrumentor` | `groq = opentelemetry.instrumentation.groq:GroqInstrumentor` | groq | Direct provider wrapper for the Groq SDK. |
| opentelemetry-instrumentation-litellm | `opentelemetry.instrumentation.litellm` | `LiteLLMInstrumentor` | `litellm = opentelemetry.instrumentation.litellm:LiteLLMInstrumentor` | litellm | One wrapper spans normalized LiteLLM backends and custom providers. |
| opentelemetry-instrumentation-mistralai | `opentelemetry.instrumentation.mistralai` | `MistralAiInstrumentor` | `mistralai = opentelemetry.instrumentation.mistralai:MistralAiInstrumentor` | mistralai | Direct provider wrapper for the Mistral AI SDK. |
| opentelemetry-instrumentation-openai | `opentelemetry.instrumentation.openai` | `OpenAIInstrumentor` | `openai = opentelemetry.instrumentation.openai:OpenAIInstrumentor` | openai | Auto-switches between OpenAI v0/v1 wrappers and supports attribute/event content mode. |
| opentelemetry-instrumentation-replicate | `opentelemetry.instrumentation.replicate` | `ReplicateInstrumentor` | `replicate = opentelemetry.instrumentation.replicate:ReplicateInstrumentor` | replicate | Covers prompts and image-generation calls from the Replicate SDK. |
| opentelemetry-instrumentation-sagemaker | `opentelemetry.instrumentation.sagemaker` | `SageMakerInstrumentor` | `sagemaker = opentelemetry.instrumentation.sagemaker:SageMakerInstrumentor` | boto3 | Wraps boto3 SageMaker runtime calls; event mode is opt-in through the instrumentor config. |
| opentelemetry-instrumentation-together | `opentelemetry.instrumentation.together` | `TogetherAiInstrumentor` | `together = opentelemetry.instrumentation.together:TogetherAiInstrumentor` | together | Direct provider wrapper for the Together SDK. |
| opentelemetry-instrumentation-vertexai | `opentelemetry.instrumentation.vertexai` | `VertexAIInstrumentor` | `google_cloud_aiplatform = opentelemetry.instrumentation.vertexai:VertexAIInstrumentor` | google-cloud-aiplatform | Targets the Vertex AI client from Google Cloud. |
| opentelemetry-instrumentation-voyageai | `opentelemetry.instrumentation.voyageai` | `VoyageAIInstrumentor` | `voyageai = opentelemetry.instrumentation.voyageai:VoyageAIInstrumentor` | voyageai | Embeddings/rerank only; suppression and content mode follow the repository-wide GenAI pattern. |
| opentelemetry-instrumentation-watsonx | `opentelemetry.instrumentation.watsonx` | `WatsonxInstrumentor` | `ibm-watson-machine-learning = opentelemetry.instrumentation.watsonx:WatsonxInstrumentor` | ibm-watson-machine-learning | Supports both IBM Watson Machine Learning and watsonx.ai module families; note the SSL/exporter caveat in the package README. |
| opentelemetry-instrumentation-writer | `opentelemetry.instrumentation.writer` | `WriterInstrumentor` | `writer = opentelemetry.instrumentation.writer:WriterInstrumentor` | writer | Direct provider wrapper for the Writer SDK. |

## Framework / agent / protocol

| Distribution | Import module | Instrumentor class | Entry point | Install extra(s) | Important caveat |
| --- | --- | --- | --- | --- | --- |
| opentelemetry-instrumentation-agno | `opentelemetry.instrumentation.agno` | `AgnoInstrumentor` | `agno = opentelemetry.instrumentation.agno:AgnoInstrumentor` | agno | Wraps the Agno framework and depends on the Agno SDK being present. |
| opentelemetry-instrumentation-crewai | `opentelemetry.instrumentation.crewai` | `CrewAIInstrumentor` | `crewai = opentelemetry.instrumentation.crewai:CrewAIInstrumentor` | crewai>=1.0.0,<2 | Adds workflow, agent, task, and LLM spans; provider name can be inferred from model prefixes. |
| opentelemetry-instrumentation-haystack | `opentelemetry.instrumentation.haystack` | `HaystackInstrumentor` | `haystack-ai = opentelemetry.instrumentation.haystack:HaystackInstrumentor` | haystack-ai | Wraps Haystack generators and pipelines; typically used around OpenAI-backed components. |
| opentelemetry-instrumentation-langchain | `opentelemetry.instrumentation.langchain` | `LangchainInstrumentor` | `langchain = opentelemetry.instrumentation.langchain:LangchainInstrumentor` | langchain | Callback-based wrapper with LangGraph and agent-factory hooks; optional trace propagation toggle. |
| opentelemetry-instrumentation-llamaindex | `opentelemetry.instrumentation.llamaindex` | `LlamaIndexInstrumentor` | `llama-index = opentelemetry.instrumentation.llamaindex:LlamaIndexInstrumentor` | llama-index; llamaparse: llama-parse | Dual legacy/core support plus optional `llamaparse`; import-time dependencies are heavier than the entry point suggests. |
| opentelemetry-instrumentation-mcp | `opentelemetry.instrumentation.mcp` | `McpInstrumentor` | `mcp = opentelemetry.instrumentation.mcp:McpInstrumentor` | mcp | Covers client/server/session spans for MCP and FastMCP, including post-import hooks and tool spans. |
| opentelemetry-instrumentation-openai-agents | `opentelemetry.instrumentation.openai_agents` | `OpenAIAgentsInstrumentor` | `openai_agents = opentelemetry.instrumentation.openai_agents:OpenAIAgentsInstrumentor` | openai_agents | OpenAI Agents has its own processor stack; avoid duplicate processors unless you opt in. |

## Vector DB

| Distribution | Import module | Instrumentor class | Entry point | Install extra(s) | Important caveat |
| --- | --- | --- | --- | --- | --- |
| opentelemetry-instrumentation-chromadb | `opentelemetry.instrumentation.chromadb` | `ChromaInstrumentor` | `chromadb = opentelemetry.instrumentation.chromadb:ChromaInstrumentor` | chromadb | Collection CRUD and query wrappers; query results can appear as events. |
| opentelemetry-instrumentation-lancedb | `opentelemetry.instrumentation.lancedb` | `LanceInstrumentor` | `lancedb = opentelemetry.instrumentation.lancedb:LanceInstrumentor` | lancedb | Simple add/search/delete wrapper around LanceDB tables. |
| opentelemetry-instrumentation-marqo | `opentelemetry.instrumentation.marqo` | `MarqoInstrumentor` | `marqo = opentelemetry.instrumentation.marqo:MarqoInstrumentor` | marqo | Direct vector DB wrapper for Marqo. |
| opentelemetry-instrumentation-milvus | `opentelemetry.instrumentation.milvus` | `MilvusInstrumentor` | `milvus = opentelemetry.instrumentation.milvus:MilvusInstrumentor` | pymilvus | Depends on `pymilvus` and can emit metrics as well as spans. |
| opentelemetry-instrumentation-pinecone | `opentelemetry.instrumentation.pinecone` | `PineconeInstrumentor` | `pinecone_client = opentelemetry.instrumentation.pinecone:PineconeInstrumentor` | pinecone>=5.1.0,<9 | Supports both legacy and current Pinecone module paths and records query metrics when enabled. |
| opentelemetry-instrumentation-qdrant | `opentelemetry.instrumentation.qdrant` | `QdrantInstrumentor` | `qdrant_client = opentelemetry.instrumentation.qdrant:QdrantInstrumentor` | qdrant-client | Entry point name is `qdrant_client`; import-time failures usually mean the client package is missing. |
| opentelemetry-instrumentation-weaviate | `opentelemetry.instrumentation.weaviate` | `WeaviateInstrumentor` | `weaviate_client = opentelemetry.instrumentation.weaviate:WeaviateInstrumentor` | weaviate-client | Handles both v3 and v4 Weaviate APIs by probing the installed client modules. |

## Local model / service

| Distribution | Import module | Instrumentor class | Entry point | Install extra(s) | Important caveat |
| --- | --- | --- | --- | --- | --- |
| opentelemetry-instrumentation-ollama | `opentelemetry.instrumentation.ollama` | `OllamaInstrumentor` | `ollama = opentelemetry.instrumentation.ollama:OllamaInstrumentor` | ollama | Targets the Ollama Python client and local daemon-style workflows. |
| opentelemetry-instrumentation-transformers | `opentelemetry.instrumentation.transformers` | `TransformersInstrumentor` | `transformers = opentelemetry.instrumentation.transformers:TransformersInstrumentor` | transformers | Text-generation pipeline only; default content mode is legacy unless you opt into events. |

## SDK-only instrument choices

The SDK exposes additional instrument choices that are not separate `opentelemetry-instrumentation-*` distributions in this subtree:

- `REQUESTS` -> `requests`
- `URLLIB3` -> `urllib3`
- `PYMYSQL` -> `pymysql`
- `REDIS` -> `redis`

Use these through `traceloop.sdk.Instruments` only when the app wants the SDK to select generic HTTP/DB/Redis wrappers as part of a broader tracing setup.

