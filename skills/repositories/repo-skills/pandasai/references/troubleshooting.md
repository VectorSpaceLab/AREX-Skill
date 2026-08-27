# Cross-cutting PandasAI Troubleshooting

## When to read

Read this when a PandasAI task fails before it clearly belongs to one sub-skill,
or when multiple surfaces are involved: installation, imports, LLM setup,
optional extensions, generated-code execution, project roots, and credentials.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pandasai'` | Package is not installed in the active Python environment | Install `pandasai` into the exact environment used by the application. Verify with `python -c "import pandasai as pai; print(pai)"`. |
| `ModuleNotFoundError` for `pandas`, `duckdb`, `sqlglot`, `pyarrow`, `matplotlib`, or `pydantic` | Incomplete package install or environment mismatch | Run `python -m pip check`; reinstall the package in the active environment. Avoid mixing system Python and virtualenvs. |
| `pai` command not found | Console scripts are not on `PATH` or package was installed without exposing scripts | Run `python -m pip show pandasai`, then try `python -m pandasai.cli.main --help` if packaging allows. Reinstall in an activated environment whose `bin/` or `Scripts/` is on `PATH`. |
| `ModuleNotFoundError: No module named 'click'` when importing CLI | CLI uses Click but the environment lacks it | Install `click` in the same environment or reinstall with the dependency set used by the package release. |
| Python version resolver fails | PandasAI metadata supports Python `>=3.8,<3.12` | Use Python 3.8-3.11. Prefer 3.11 when preparing a fresh environment for v3.0.0. |

## LLM and credential failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `.chat()` raises `PandasAI API key does not include LLM credits... configure an OpenAI or LiteLLM key` | No LLM object set in `pai.config` | Install an LLM extension such as `pandasai-litellm` or `pandasai-openai`, instantiate its LLM class with provider credentials, then call `pai.config.set({"llm": llm})`. |
| Provider authentication error | Provider API key or environment variable is missing/invalid | Keep provider keys out of code; read them from environment variables or a secret manager and pass them to the provider extension. |
| Need offline deterministic tests | Real LLMs are non-deterministic or require network/credentials | Use `pandasai.llm.fake.FakeLLM` with generated code that calls `execute_sql_query` and returns a valid `result` dictionary. See `sub-skills/conversational-analysis/scripts/offline_chat_smoke.py`. |

## Generated-code and response failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ExecuteSQLQueryNotUsed` | Generated code did not call `execute_sql_query` | Regenerate or edit the code so data access goes through `execute_sql_query(...)`, then assign `result = {"type": ..., "value": ...}`. |
| `InvalidOutputValueMismatch` about response format | `result` is missing, has wrong keys, or mismatches the declared type | Use `number` for int/float, `string` for str, `dataframe` for DataFrame/Series/dict, and `plot` for chart path/base64. |
| `NoResultFoundError` | Executed code never assigned `result` | Add a final `result = {"type": ..., "value": ...}` statement. |
| `MaliciousQueryError` or unauthorized table error | SQL sanitizer rejected non-SELECT/dangerous SQL, or generated SQL names a table not registered in the agent state | Keep queries read-only and use the exact `df.schema.name` table names. For file-based datasets created from hyphenated paths, the schema name uses underscores. |
| Chart response opens a viewer unexpectedly | `ChartResponse.__str__()` calls `show()` | Use `response.save("chart.png")` or inspect `response.value` instead of printing when running in headless automation. |

## Optional extension failures

| Surface | Optional dependency | Common failure | Recovery |
| --- | --- | --- | --- |
| LLM providers | `pandasai-litellm`, `pandasai-openai` | Import error or provider auth error | Install only the chosen extension and configure credentials through environment/secret management. |
| SQL sources | `pandasai-sql[...]` | `Connector not found` or database driver error | Install the specific SQL extra for the source type and verify connection settings. Do not hardcode passwords. |
| Docker sandbox | `pandasai-docker`, Docker daemon | Import error, daemon unavailable, container startup failure | Install the extension, confirm Docker is running, and route to `sandbox-and-security` before running untrusted code. |
| Enterprise cloud connectors/vector stores | vendor-specific packages and license | Import/license/credential errors | Treat as optional enterprise features; document required credentials and do not assume availability in base workflows. |

## Project-root and dataset layout surprises

PandasAI's default local file manager stores datasets under a `datasets/`
directory located relative to the project root. Project-root discovery walks up
from the current working directory until it finds a package marker such as
`pyproject.toml`, `setup.py`, or `requirements.txt`; otherwise it falls back to
the current working directory.

Recovery steps:

1. Run from the intended project directory before calling `pai.create`,
   `pai.load`, or the `pai` CLI.
2. Confirm `datasets/<organization>/<dataset>/schema.yaml` exists for semantic
   datasets.
3. Use lowercase hyphenated `organization/dataset` paths in public APIs; expect
   schema names and SQL table names to be sanitized to underscores.
4. If `.env` appears in an unexpected parent directory after `pai login`, rerun
   from the intended project root or use explicit project setup.

## Where to go next

- Chat/code/response errors: `sub-skills/conversational-analysis/references/troubleshooting.md`
- Schema/load/view errors: `sub-skills/semantic-layer/references/troubleshooting.md`
- Custom function/registry errors: `sub-skills/custom-skills/references/troubleshooting.md`
- Sandbox/security errors: `sub-skills/sandbox-and-security/references/troubleshooting.md`
- CLI/project-root errors: `sub-skills/cli-and-project-ops/references/troubleshooting.md`
