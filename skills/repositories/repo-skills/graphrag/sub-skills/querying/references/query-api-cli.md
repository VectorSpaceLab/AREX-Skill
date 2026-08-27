# Query API and CLI

## CLI Pattern

Use `graphrag query QUERY --root PROJECT_ROOT --method METHOD` after an index exists. The command loads `settings.yaml`, reads output parquet tables via the configured table provider, and dispatches to the matching Python API.

Common flags:

- `--root`, `-r`: project root containing GraphRAG settings and prompt/config files.
- `--method`, `-m`: one of `global`, `local`, `drift`, or `basic`; default is global.
- `--data`, `-d`: alternate index output directory containing the parquet tables.
- `--community-level`: hierarchy level for global/local/DRIFT; higher values are smaller communities.
- `--dynamic-community-selection/--no-dynamic-selection`: global search can ask the LLM to select relevant communities instead of using all reports at a fixed roll-up.
- `--response-type`: free-form desired answer shape such as `Multiple Paragraphs` or `List of 3-7 Points`.
- `--streaming/--no-streaming`: print chunks as the search engine streams them.
- `--verbose`, `-v`: write more query diagnostics.

Examples:

```bash
graphrag query "What are the top themes?" --root . --method global --community-level 2
graphrag query "How is Contoso related to Fabrikam?" --root . --method local --response-type "Single Paragraph"
graphrag query "What should I investigate next?" --root . --method drift --streaming
graphrag query "Find chunks about retention policy" --root . --method basic --data output
```

## Python API Pattern

Import from `graphrag.api` and pass a loaded `GraphRagConfig` plus pandas DataFrames. Non-streaming calls are async and return `(response, context_data)`. Streaming variants return an async generator of response chunks; use `QueryCallbacks` such as `NoopQueryCallbacks.on_context` if the caller needs final context data.

```python
import asyncio
import pandas as pd
from graphrag.api import local_search
from graphrag.config.load_config import load_config

config = load_config(root_dir=".")
entities = pd.read_parquet("output/entities.parquet")
communities = pd.read_parquet("output/communities.parquet")
community_reports = pd.read_parquet("output/community_reports.parquet")
text_units = pd.read_parquet("output/text_units.parquet")
relationships = pd.read_parquet("output/relationships.parquet")

response, context = asyncio.run(local_search(
    config=config,
    entities=entities,
    communities=communities,
    community_reports=community_reports,
    text_units=text_units,
    relationships=relationships,
    covariates=None,
    community_level=2,
    response_type="Multiple Paragraphs",
    query="How is entity X used?",
))
```

## API Inputs by Method

- `global_search(config, entities, communities, community_reports, community_level, dynamic_community_selection, response_type, query, callbacks=None, verbose=False)`.
- `local_search(config, entities, communities, community_reports, text_units, relationships, covariates, community_level, response_type, query, callbacks=None, verbose=False)`.
- `drift_search(config, entities, communities, community_reports, text_units, relationships, community_level, response_type, query, callbacks=None, verbose=False)`.
- `basic_search(config, text_units, response_type, query, callbacks=None, verbose=False)`.

Each has a matching `*_streaming` function with the same required inputs. The query API is marked under development, so prefer checking installed signatures when writing durable integration code.

## Question Generation

GraphRAG question generation lives under the query package and uses local-search style context: entities, relationships, covariates, community reports, text units, an entity-description vector store, a chat model, an embedding model, and a question-generation prompt. Use it when the user asks for follow-up questions or investigation prompts rather than a direct answer. If no CLI is exposed for question generation in the installed version, build it through the Python context-builder/question-generation classes using the same data checks as local search.
