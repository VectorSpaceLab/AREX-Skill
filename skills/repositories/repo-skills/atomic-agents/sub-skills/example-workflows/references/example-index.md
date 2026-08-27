# Example Index

| Example | What it demonstrates | Dependencies / keys | Use when | Avoid when |
| --- | --- | --- | --- | --- |
| `quickstart` | the smallest agent, custom schema, streaming, async, and provider switching | provider SDKs; often an API key | you need the first successful Atomic Agent or a basic chatbot recipe | you need a tool, RAG, or server architecture |
| `basic-multimodal` | image + text analysis of nutrition labels | vision-capable provider SDK and API key | the user asks about image understanding or multimodal extraction | you need OCR-heavy PDF extraction or a non-vision flow |
| `nested-multimodal` | multimodal content nested inside Pydantic schemas | vision-capable provider SDK and API key | multimodal content is not only top-level but embedded in nested objects | you only need a flat image-to-text demo |
| `basic-pdf-analysis` | PDF analysis with multimodal model support | Google generative AI / multimodal provider and a PDF fixture | you need to inspect or summarize a PDF with structured output | you need offline PDF text extraction only |
| `deep-research` | multi-step research pipeline | network, search backends, provider key | the task is a research workflow with decomposition and synthesis | you only need one-shot question answering |
| `rag-chatbot` | retrieval-augmented chat with a vector store | vector store dependency such as ChromaDB or Qdrant plus provider key | the user wants document Q&A or retrieval-backed chat | you only need plain chat or a simple tool |
| `web-search-agent` | web search plus answer synthesis | search provider / provider key | the task requires current web information | you need fully offline behavior |
| `orchestration-agent` | tool-routing orchestrator using union outputs | provider key, tool dependencies | the user wants the model to choose between calculator/search style tools | the workflow is fixed and no routing is needed |
| `hooks-example` | Instructor hook system, retry / monitoring / error handling | provider key | the request is about observability or intelligent retries | you only need the core agent API |
| `mcp-agent` | MCP client/server transports and dynamic tool discovery | MCP runtime plus example-specific dependencies | the user wants MCP client/server integration or transport comparison | you need only the raw MCP connector internals |
| `progressive-disclosure` | 3-server / 24-tool MCP progressive disclosure | OpenAI key plus three MCP servers | the user wants a worked example of limiting tool-surface size | you only need the connector API or a single server |
| `persistent-memory` | cross-process memory backend | provider key | the task needs conversation recall across process runs | you only need in-memory `ChatHistory` |
| `fastapi-memory` | multi-user / multi-session API with memory | FastAPI plus provider key | the user wants an HTTP service with persistent conversation state | you only need a CLI chatbot or local script |
| `dspy-integration` | DSPy + Atomic Agents integration | DSPy and provider key | the task is hybrid optimization or prompt-programming integration | you only need the core framework |
| `youtube-summarizer` | transcript extraction and summarization | YouTube transcript support and provider key | the task is summarizing a public video | you need local file analysis or non-YouTube media |
| `youtube-to-recipe` | structured recipe extraction from cooking videos | YouTube transcript support and provider key | the user wants to transform cooking videos into recipe data | you only need general transcript summarization |

## Usage notes

- Treat this index as a routing aid, not as a claim that every example is safe to run offline.
- Quickstart and the memory examples are the best first choices for core agent behavior.
- The MCP examples are the best first choices for multi-server / progressive disclosure questions.
- Search and research examples usually need network access and a provider key.
