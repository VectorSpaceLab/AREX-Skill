# Installation and Runtime Selection

## Baseline

DB-GPT is a Python 3.10+ package family. The public application distribution
is `dbgpt-app`; the baseline source snapshot for this skill is 0.8.1. Prefer a
fresh virtual environment and a version-pinned install when reproducing this
skill:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate  # use the platform equivalent on Windows
uv pip install 'dbgpt-app==0.8.1'
dbgpt --version
```

Use `pip install` instead of `uv pip install` when required. Do not install the
repository's development, benchmark, frontend, or every optional provider
requirement merely to answer a focused Researcher task.

## Select extras by workflow

- **OpenAI-compatible or other remote provider:** use the provider extra
  documented by the matching release and keep its key in the provider's
  environment variable.
- **Local documents/RAG:** add the RAG/parser extra required by the file types
  (`pdf`, `docx`, `pptx`, spreadsheet, HTML/Markdown) and the selected vector
  store. A parser import is not proof that an index or embedding model works.
- **External database/vector/graph:** install only the connector/store extra
  for the named service and verify the service separately. SQLite and local
  fixture checks do not prove MySQL, Postgres, Elasticsearch, Milvus, Qdrant,
  Chroma server, Neo4j, TuGraph, or other external integrations.
- **Local model serving:** select one backend (`hf`, `vllm`, `llama.cpp`,
  `llama.cpp.server`, or `mlx`) and match Python, framework, wheel, driver,
  model path, device, and VRAM. Read
  [models-and-serving](../sub-skills/models-and-serving/SKILL.md).
- **Sandbox:** install the package and explicitly choose a supported container
  runtime/image or the weaker opt-in local runtime. Do not infer isolation from
  the Python import.

## First checks

```bash
dbgpt --version
python -c "import dbgpt, dbgpt_app, dbgpt_client, dbgpt_ext; print('imports ok')"
dbgpt --help
dbgpt setup --help
dbgpt start web --help
```

Do not make a live provider call, launch the webserver, or run a model as a
package installation check. Use the route-specific references for the next
validation step. If the CLI imports only partially, inspect which optional
package failed before adding a broad extra.

## Credentials and network

Provider setup may accept `DBGPT_API_KEY` or a provider-specific environment
variable, but exact precedence is release-specific. Use a secret manager or a
process environment, and redact all diagnostics. Review any installer fetched
from the network before running it: clone/update, dependency installation,
config writes, remote repository access, and credential handling are side
 effects, not safe package smoke tests.
