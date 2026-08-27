# PandasAI Package Overview

## Purpose

Read this for a shared map of the PandasAI 3.x package surface before choosing a
sub-skill. Deeper recipes live in the owning sub-skill references.

## Core package facts

- Distribution: `pandasai`
- Import: `import pandasai as pai`
- Verified package version for this skill: `3.0.0`
- Supported Python range from package metadata: `>=3.8,<3.12`
- Console entry point: `pai`
- Core runtime dependencies include pandas, DuckDB, sqlglot, pyarrow, matplotlib,
  seaborn, pydantic, requests, openpyxl, python-dotenv, and related scientific
  Python packages.

## Public API map

| Surface | What it does | Owner |
| --- | --- | --- |
| `pai.DataFrame(data, **kwargs)` | Pandas subclass carrying semantic schema metadata and `.chat()` support | `conversational-analysis`, `semantic-layer` |
| `pai.read_csv(filepath)` | Reads a CSV into a PandasAI `DataFrame` with a sanitized table name | `semantic-layer` |
| `pai.read_excel(filepath, sheet_name=0)` | Reads Excel into a `DataFrame`; `sheet_name=None` returns a dict of DataFrames | `semantic-layer` |
| `pai.config.set({...})` | Sets global config such as `llm`, `save_logs`, `verbose`, and `max_retries` | `conversational-analysis` |
| `DataFrame.chat(prompt, sandbox=None)` | Starts or reuses a dataframe-specific `Agent` and returns a response object | `conversational-analysis` |
| `pai.chat(query, *dataframes, sandbox=None)` | Starts a global chat over one or more DataFrames | `conversational-analysis` |
| `pai.follow_up(query)` | Continues the last global chat | `conversational-analysis` |
| `Agent(dfs, config=None, memory_size=10, vectorstore=None, description=None, sandbox=None)` | Multi-turn conversation object | `conversational-analysis` |
| `pai.create(path, df=None, description=None, columns=None, source=None, relations=None, view=False, group_by=None, transformations=None)` | Creates a semantic dataset or view and returns a loadable DataFrame/VirtualDataFrame | `semantic-layer` |
| `pai.load(dataset_path)` | Loads a dataset from the project `datasets/` directory | `semantic-layer` |
| `@pai.skill()` / `pandasai.ee.skills.skill` | Registers custom Python functions for generated code | `custom-skills` |
| `Sandbox` | Abstract execution-isolation interface | `sandbox-and-security` |
| `pai login`, `pai dataset create` | CLI authentication and guided dataset schema creation | `cli-and-project-ops` |

## Optional extension packages

Install optional extensions only when the user needs the corresponding surface:

| Need | Package/examples |
| --- | --- |
| Use OpenAI, Anthropic, Google, local Ollama, or other providers through one wrapper | `pandasai-litellm` |
| Use OpenAI or Azure OpenAI-specific wrapper | `pandasai-openai` |
| Query SQL databases through semantic-layer sources | `pandasai-sql[postgres]`, `pandasai-sql[mysql]`, `pandasai-sql[cockroachdb]`, `pandasai-sql[sqlserver]` |
| Execute generated code in a Docker sandbox | `pandasai-docker` plus a running Docker daemon |
| Use enterprise cloud data connectors or vector-store training | vendor-specific enterprise extensions and an enterprise license |

## Runtime model

1. Data is represented as PandasAI `DataFrame` or `VirtualDataFrame` objects.
2. The chat layer asks the configured LLM to produce Python code, usually with a
   SQL query executed through `execute_sql_query`.
3. Code is cleaned/validated, then executed locally or through a supplied
   `Sandbox`.
4. The response parser expects `result = {"type": ..., "value": ...}` and
   returns a typed response object.
5. Semantic datasets store schema/data under a project `datasets/` directory;
   they can be local files, SQL-backed virtual tables, or views over compatible
   datasets.

## Route ownership

- Put LLM setup, prompt/result handling, generated-code repair, and legacy
  wrapper migration in `conversational-analysis`.
- Put schema/data modeling, `create`/`load`, transformations, SQL/view query
  builders, and Excel/CSV/parquet loaders in `semantic-layer`.
- Put callable custom functions and registry behavior in `custom-skills`.
- Put sandbox selection, Docker extension lifecycle, and security posture in
  `sandbox-and-security`.
- Put command-line interaction, `.env` API-key handling, and contributor commands
  in `cli-and-project-ops`.
