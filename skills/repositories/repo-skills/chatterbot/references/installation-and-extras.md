# Installation and Optional Extras

## When to read

Read this when a ChatterBot task begins with installation, import errors, optional backend selection, or deciding which dependencies are necessary for a workflow.

## Base install

ChatterBot metadata declares Python `>=3.10,<3.15` and the distribution name `ChatterBot`. The normal public install is:

```bash
python -m pip install chatterbot
```

For source checkouts, use:

```bash
python -m pip install .
```

The base package depends on:

- `mathparse` for mathematical expression parsing;
- `python-dateutil` for datetime parsing and statement timestamps;
- `sqlalchemy` for default SQL storage;
- `spacy` for default text tagging and comparisons;
- `tqdm` for training progress.

A minimal metadata/import check is:

```bash
python - <<'PY'
from importlib.metadata import version
import chatterbot
from chatterbot import ChatBot
print(version("ChatterBot"))
print(chatterbot.__version__)
print(ChatBot)
PY
```

## spaCy language models

The default `ChatBot` path uses `PosLemmaTagger`, which loads a spaCy model based on `tagger_language`. English uses `en_core_web_sm`. If the model is missing, ChatterBot raises a setup error with a command like:

```bash
python -m spacy download en_core_web_sm
```

Other mapped language models include German `de_core_news_sm`, Spanish `es_core_news_sm`, French `fr_core_news_sm`, and the other models listed in ChatterBot's language-to-spaCy mapping. Only install language models that the task needs.

For lightweight tests or vector storage workflows, a custom tagger such as `NoOpTagger` can avoid spaCy model loading, but do not claim default indexed SQL matching was verified unless the real tagger/search path has been checked.

## Optional dependency groups

The repo declares these optional groups:

| Extra | Use when | Main dependencies |
| --- | --- | --- |
| `test` | running the repo's tests or docs checks | `flake8`, `coverage`, `sphinx`, `huggingface_hub`, `django`, `click` |
| `dev` | development features and examples | `pint`, `pyyaml`, `chatterbot-corpus`, `ollama`, `openai` |
| `redis` | Redis vector storage and embeddings | `redis[hiredis]`, `langchain-redis`, `langchain-huggingface`, `accelerate`, `sentence-transformers` |
| `mongodb` | MongoDB storage adapter | `pymongo` |

Install only the group needed for the selected workflow:

```bash
python -m pip install "chatterbot[dev]"      # corpus, Pint, Ollama/OpenAI clients
python -m pip install "chatterbot[redis]"    # Redis vector storage dependencies
python -m pip install "chatterbot[mongodb]"  # PyMongo
python -m pip install django                 # Django integration if not using broad extras
```

The documentation mentions `chatterbot[dev] python-dotenv` for the OpenAI example because that example loads an API key from a `.env` file.

## Service prerequisites

Optional storage and LLM adapters often need more than Python packages:

| Feature | Python packages | External prerequisite |
| --- | --- | --- |
| SQL storage | base package | SQLite works out of the box; other databases need a SQLAlchemy-supported driver and URI |
| Mongo storage | `chatterbot[mongodb]` or `pymongo` | reachable MongoDB service and valid URI; TLS kwargs may be needed for Atlas/DocumentDB |
| Redis vector storage | `chatterbot[redis]` | Redis Stack/vector-search capable Redis service and embedding model/provider access |
| Ollama LLM adapter | `ollama` client, available through `dev` extra | local/remote Ollama server and a pulled model |
| OpenAI LLM adapter | `openai` client, available through `dev` extra | `OPENAI_API_KEY` or compatible base URL credentials |
| Django integration | `django` | Django settings configured, app installed, migrations applied |

## Safe smoke commands

Use these before deeper debugging:

```bash
python -m chatterbot --version
python -m chatterbot --help
python scripts/check_chatterbot_environment.py --check-spacy-model en_core_web_sm
```

For a no-file SQL smoke:

```bash
python - <<'PY'
from chatterbot import ChatBot
bot = ChatBot("Smoke", database_uri=None, read_only=True)
print(bot.get_response("Hello"))
PY
```

If this fails with a spaCy model error, fix the model first. If it fails with an optional dependency error, install only the dependency for the feature being used.
