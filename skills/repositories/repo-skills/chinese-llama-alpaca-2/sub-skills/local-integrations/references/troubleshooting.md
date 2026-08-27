# Local integration troubleshooting

## llama.cpp wrappers

- `chat.sh` expects an executable llama.cpp `main` binary in the current directory.
- `server_curl_example.sh` expects a llama.cpp server listening on `localhost:8080`.
- Both wrappers require a compatible GGUF model; this skill does not bundle model weights.
- If the model responds poorly, check that the Alpaca-2 prompt wrapper was preserved.

## LangChain notes

- LangChain APIs move frequently. Verify the target project's installed version before copying old import paths.
- Retrieval QA examples require an embedding model path and a vector store backend such as FAISS.
- Summarization examples require a model path and a prompt chain compatible with the chosen LangChain version.

## privateGPT notes

- The privateGPT snippets depend on a project-local `constants.py`; missing that file is not a Chinese-LLaMA-Alpaca-2 skill bug.
- Validate `.env` settings, Chroma persistence paths, and model-type names inside the actual privateGPT checkout.
- Use the bundled prompt assets from the root skill when reconstructing the privateGPT prompt templates.
