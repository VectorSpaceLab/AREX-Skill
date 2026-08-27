# Provider Matrix

## Purpose

Use this reference when a task is about choosing exact DeepSearcher provider names, required environment variables, optional package extras, or the default provider stack used by `Configuration()`.

## Default provider stack from the inspected checkout

| Feature | Default provider | Default config |
| --- | --- | --- |
| `llm` | `OpenAI` | `model: o1-mini` |
| `embedding` | `OpenAIEmbedding` | `model: text-embedding-ada-002` |
| `file_loader` | `PDFLoader` | `{}` |
| `web_crawler` | `FireCrawlCrawler` | `{}` |
| `vector_db` | `Milvus` | `default_collection: deepsearcher`, `uri: ./milvus.db`, `token: root:Milvus`, `db: default` |

`init_config(config)` constructs all five feature providers at once. If one default provider is broken, even a workflow that does not plan to use it may still fail during initialization.

## LLM providers

| Provider | Typical env vars | Optional package / note |
| --- | --- | --- |
| `OpenAI` | `OPENAI_API_KEY`, optional `OPENAI_BASE_URL` | `openai` |
| `DeepSeek` | `DEEPSEEK_API_KEY`, optional `DEEPSEEK_BASE_URL` | `openai` compatible client |
| `AzureOpenAI` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY` | `openai` |
| `Anthropic` | `ANTHROPIC_API_KEY` | `anthropic` |
| `Ollama` | local Ollama server, optional `OLLAMA_HOST` / base URL | `ollama` |
| `WatsonX` | `WATSONX_APIKEY`, `WATSONX_URL`, `WATSONX_PROJECT_ID` or `space_id` | `ibm-watsonx-ai` |
| `Bedrock` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_SESSION_TOKEN` | `boto3` |
| `TogetherAI` | `TOGETHER_API_KEY` | `together` |
| `XAI` | `XAI_API_KEY` | `openai` compatible client |
| `Gemini` | `GEMINI_API_KEY` | `google-genai` |
| `GLM` | `GLM_API_KEY` | `zhipuai` |
| `Volcengine` | `VOLCENGINE_API_KEY` | `openai` compatible client |
| `JiekouAI` | `JIEKOU_API_KEY` | `openai` compatible client |
| `Aliyun` | `DASHSCOPE_API_KEY` or `OPENAI_API_KEY` with compatible base URL | `openai` compatible client |
| `PPIO` | `PPIO_API_KEY` | `openai` compatible client |
| `SiliconFlow` | `SILICONFLOW_API_KEY` | `openai` compatible client |
| `Novita` | `NOVITA_API_KEY` | `openai` compatible client |

## Embedding providers

| Provider | Typical env vars | Optional package / note |
| --- | --- | --- |
| `OpenAIEmbedding` | `OPENAI_API_KEY`, optional `OPENAI_BASE_URL` | `openai` |
| `MilvusEmbedding` | depends on chosen Milvus model and `pymilvus` model extras | `pymilvus` |
| `FastEmbedEmbedding` | none for local usage | `fastembed` |
| `SentenceTransformerEmbedding` | none for local usage | `sentence-transformers` |
| `WatsonXEmbedding` | `WATSONX_APIKEY`, `WATSONX_URL`, `WATSONX_PROJECT_ID` or `space_id` | `ibm-watsonx-ai` |
| `VoyageEmbedding` | `VOYAGE_API_KEY` | `voyageai` |
| `OllamaEmbedding` | local Ollama server | `ollama` |
| `GeminiEmbedding` | `GEMINI_API_KEY` | `google-genai` |
| `GLMEmbedding` | `GLM_API_KEY` | `zhipuai` |
| `VolcengineEmbedding` | `VOLCENGINE_API_KEY` | `openai` compatible client |
| `JiekouAIEmbedding` | `JIEKOU_API_KEY` | `requests`-based client |
| `NovitaEmbedding` | `NOVITA_API_KEY` | `requests`-based client |
| `PPIOEmbedding` | `PPIO_API_KEY` | `requests`-based client |
| `SiliconflowEmbedding` | `SILICONFLOW_API_KEY` | `requests`-based client |
| `BedrockEmbedding` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_SESSION_TOKEN` | `boto3` |

## File loaders

| Provider | Typical env vars | Note |
| --- | --- | --- |
| `PDFLoader` | none | Also reads `.md` and `.txt` files in this checkout. |
| `TextLoader` | none | Reads `.txt` and `.md`. |
| `JsonFileLoader` | none | Requires a `text_key` and expects JSON or JSONL records. |
| `UnstructuredLoader` | optional `UNSTRUCTURED_API_KEY`, `UNSTRUCTURED_API_URL` | Local mode works without the API variables but may need `unstructured-ingest` and `unstructured[all-docs]`. |
| `DoclingLoader` | none | Requires `docling` / `docling-core` support for the file type. |

## Web crawlers

| Provider | Typical env vars | Note |
| --- | --- | --- |
| `FireCrawlCrawler` | `FIRECRAWL_API_KEY` | This checkout expects a client that exports `ScrapeOptions`; see troubleshooting for version pins. |
| `Crawl4AICrawler` | none for import, but browser setup may be needed later | Optional browser automation crawler. |
| `JinaCrawler` | `JINA_API_TOKEN` or `JINAAI_API_KEY` | Uses the Jina rendering service. |
| `DoclingCrawler` | none | Uses Docling conversion and chunking. |

## Vector databases

| Provider | Typical env vars | Note |
| --- | --- | --- |
| `Milvus` | none for local Lite; service credentials for remote/Zilliz | Default `uri` is `./milvus.db`. Use unique working directories to avoid local locks. |
| `Qdrant` | optional server auth | Requires a running Qdrant service for non-memory setups. |
| `OracleDB` | Oracle user/password/DSN/wallet configuration | Requires Oracle client and database access. |
| `AzureSearch` | Azure endpoint, API key, index name | Service-backed search index. |

## Provider naming rules

- Provider strings are exact class names, not package names or human labels.
- `JiekouAI` is valid; `Jiekou.AI` is not.
- `SiliconFlow` is the LLM provider name, while `SiliconflowEmbedding` is the embedding provider name.
- `WatsonX` and `WatsonXEmbedding` are distinct classes.

## Suggested safe switches

- For a fully local stack, the inspected compatibility set was `PDFLoader` + `FastEmbedEmbedding` + `Milvus` with local Milvus Lite support.
- For minimal query experiments, keep provider names explicit and update both `llm` and `embedding` before `init_config(config)`.
- For web crawling, confirm both the crawler SDK and its credential variables before enabling the feature in the default config.
