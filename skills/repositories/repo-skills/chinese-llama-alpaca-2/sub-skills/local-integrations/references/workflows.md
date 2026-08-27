# Local integration workflows

## llama.cpp chat wrapper

Bundled script: `scripts/llama-cpp/chat.sh`

Expected inputs:

1. path to a compatible GGUF model
2. first user instruction

The wrapper uses the Alpaca-2 prompt shape:

```text
[INST] <<SYS>>
You are a helpful assistant. 你是一个乐于助人的助手。
<</SYS>>

<instruction> [/INST]
```

The script assumes the llama.cpp `main` binary is in the current directory when the wrapper runs.

## llama.cpp server curl example

Bundled script: `scripts/llama-cpp/server_curl_example.sh`

Expected input:

1. user instruction

The script sends a prompt to a llama.cpp server endpoint at `http://localhost:8080/completion`. Start the llama.cpp server separately before running it.

## LangChain example notes

The source repository includes examples for retrieval QA and summarization built around LangChain, FAISS, Hugging Face embeddings, and HF model pipelines. These are not bundled as runnable code in this skill because they depend on external package APIs and model/embedding paths that are outside the repo's minimum runtime contract.

Use the repo-specific details from those examples when adapting a downstream project:

- wrap context and question in the Alpaca-2 `[INST]` template
- use the bilingual default system prompt
- keep chunk sizes and retrieval depth explicit
- validate that the external LangChain version still exposes the import paths used by the target project

## privateGPT example notes

The source repository includes privateGPT adaptation snippets, including a `refine` prompt variant. They are reference-only here because they depend on an external privateGPT scaffold and a `constants.py` module that is not part of this self-contained skill tree.

Use the prompt templates as guidance, but rebuild the integration inside the actual privateGPT project rather than copying stale code blindly.
