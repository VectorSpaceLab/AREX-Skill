# Installing GenAI Processors

## Core install

Use Python 3.11+ for this snapshot. The package metadata supports the current
CI range of Python 3.11, 3.12, and 3.13.

```bash
python -m pip install genai-processors
python -c "import genai_processors; print(genai_processors.__version__)"
```

The import package is `genai_processors`. The public package is often referred
to as `genai-processors`; Python packaging treats `-` and `_` as equivalent in
many contexts.

## Optional install families

Choose only the optional pieces needed for the task:

| Need | Install / prepare |
| --- | --- |
| LangChain and OpenRouter wrappers | `python -m pip install "genai-processors[contrib]"` |
| ADK example / `adk.ProcessorAgent` bridge | `python -m pip install google-adk` |
| Audio CLI and live audio I/O | install `pyaudio`; on Linux this may require PortAudio headers or a Conda package from conda-forge |
| Video capture/extraction | install `av` and `opencv-python` if they are not already present |
| Local Transformers backend | install `transformers` plus PyTorch (`torch`) for actual model execution |
| Ollama backend | install/run Ollama separately and pull a model such as `gemma3` |
| Speech-to-text / text-to-speech | configure Google Cloud credentials and `GOOGLE_PROJECT_ID` |
| Gemini / Live API examples | set `GOOGLE_API_KEY` with a Gemini API key |

The repo CI installs the base package, `[contrib]`, and `[dev]`, then runs
`pytest`. Do not use `[dev]` as a default runtime install unless you actually
need test/lint/local-model packages such as `torch`, `transformers`, `av`,
`google-adk`, or pytest.

## Smoke checks

From an environment where the package is installed:

```bash
python -c "import genai_processors; print(genai_processors.__version__)"
python scripts/check_install.py
python scripts/check_install.py --optional
```

`--optional` only imports optional modules. It does not call remote APIs, open
microphones/cameras, download models, fetch URLs, or start services.

## Environment variables used by examples

| Variable | Used by |
| --- | --- |
| `GOOGLE_API_KEY` | Gemini model calls, Live API, image-generation examples, many CLIs |
| `GOOGLE_PROJECT_ID` | Google Cloud Speech-to-Text and Text-to-Speech processors |
| custom API headers | remote MCP examples and OpenRouter-style integrations |
| Ollama host / service | `OllamaModel` when the default local server is not appropriate |

Many examples read environment variables at module import time. If a future
agent only needs to inspect a file or run `--help`, avoid importing the example
module unless the required dummy or real environment variable is set.
