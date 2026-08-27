---
name: pandasai
description: "Routes PandasAI tasks for conversational dataframe analysis,
  semantic data layers, custom skills, sandboxed execution, CLI usage, and repo
  maintenance guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PandasAI Repo Skill

Use this skill when a task involves the PandasAI Python package (`pandasai`),
especially natural-language analysis over pandas dataframes, semantic dataset
schemas, PandasAI custom skills, sandboxed code execution, or the `pai` CLI.

PandasAI 3.x turns dataframes and semantic datasets into conversational analysis
surfaces. It uses an LLM to generate Python/SQL code, executes that code locally
or through an optional sandbox, and returns typed response objects.

## First checks

For a fresh environment, install the core package and the LLM/provider extension
that matches the user's provider:

```bash
pip install pandasai
pip install pandasai-litellm        # common provider bridge
# or: pip install pandasai-openai   # OpenAI/Azure extension
```

Minimum import check:

```bash
python - <<'PY'
import pandasai as pai
from pandasai import Agent, DataFrame
print("pandasai import ok", pai)
print("DataFrame", DataFrame)
print("Agent", Agent)
PY
```

For local deterministic smoke checks without real LLM credentials, run the
bundled diagnostic:

```bash
python scripts/check_pandasai_environment.py --chat-smoke
```

Read [`references/repo-provenance.md`](references/repo-provenance.md) before
refreshing this skill or comparing it against a checkout. Read
[`references/package-overview.md`](references/package-overview.md) for the
shared public API map and [`references/troubleshooting.md`](references/troubleshooting.md)
for cross-cutting install/import/optional-dependency issues.

## Route map

| User task | Read next |
| --- | --- |
| Configure an LLM, ask questions against a DataFrame, inspect response objects, use `Agent`, debug generated code, or migrate from `SmartDataframe`/`SmartDatalake` | [`sub-skills/conversational-analysis/SKILL.md`](sub-skills/conversational-analysis/SKILL.md) |
| Create/load semantic datasets, validate `schema.yaml`, define CSV/parquet/SQL/view sources, transformations, `group_by`, or relation rules | [`sub-skills/semantic-layer/SKILL.md`](sub-skills/semantic-layer/SKILL.md) |
| Add custom callable functions to PandasAI with `@pai.skill`, inspect `SkillType`, or manage the global skills registry | [`sub-skills/custom-skills/SKILL.md`](sub-skills/custom-skills/SKILL.md) |
| Decide whether to sandbox generated code, use the optional Docker sandbox, or implement/check a custom `Sandbox` subclass | [`sub-skills/sandbox-and-security/SKILL.md`](sub-skills/sandbox-and-security/SKILL.md) |
| Use the `pai` CLI, validate/login with a PandaBI API key, run guided dataset creation, or follow repo maintainer commands | [`sub-skills/cli-and-project-ops/SKILL.md`](sub-skills/cli-and-project-ops/SKILL.md) |

## Common workflow skeleton

1. Identify whether the user is using raw pandas data, a PandasAI `DataFrame`, or
   a semantic dataset path.
2. If the task calls `.chat()` or `pai.chat()`, make sure an LLM is configured
   with `pai.config.set({"llm": llm})` unless the user is deliberately running a
   `FakeLLM` smoke test.
3. If the task writes datasets, confirm the dataset path is `organization/dataset`
   with lowercase hyphenated segments and that generated files belong under a
   project `datasets/` directory.
4. If prompts, data, or generated code are untrusted, route to sandbox guidance
   before running code.
5. If optional extensions are missing, install only the needed package:
   `pandasai-litellm`, `pandasai-openai`, `pandasai-sql[...]`, or
   `pandasai-docker`.

## Important constraints

- PandasAI executes LLM-generated code. Treat generated code as unsafe unless it
  is reviewed or executed inside an appropriate sandbox.
- Core chat code generation expects use of an `execute_sql_query(...)` function
  and a `result = {"type": ..., "value": ...}` dictionary.
- Chart responses use the `plot` result type internally and return a chart
  response object; save or show charts through response methods.
- SQL connector, Docker sandbox, external LLM provider, cloud connector, and
  enterprise vector-store features are optional and should not be assumed in a
  base environment.
- `SmartDataframe` and `SmartDatalake` are compatibility wrappers that emit
  deprecation warnings; prefer `pai.DataFrame`, `pai.chat`, and `Agent` for new
  code.

## Shared references and scripts

- [`references/package-overview.md`](references/package-overview.md) summarizes
  the package surface, optional extensions, and route ownership.
- [`references/troubleshooting.md`](references/troubleshooting.md) lists
  cross-cutting install, import, LLM, SQL, sandbox, and project-root issues.
- [`references/maintainer-notes.md`](references/maintainer-notes.md) captures
  contributor-oriented test/lint/package guidance without requiring full extras
  for ordinary package use.
- [`scripts/check_pandasai_environment.py`](scripts/check_pandasai_environment.py)
  checks imports, version metadata, CLI availability, optional extensions, and a
  deterministic offline chat smoke.

## Avoid when

Use a generic pandas/data-science skill instead if the user only needs standard
pandas operations without PandasAI APIs. Use an LLM provider-specific or gateway
skill when the problem is provider routing, billing, or model hosting outside
PandasAI's configuration surface. Use a Docker or security-hardening skill when
the task is container infrastructure rather than PandasAI sandbox integration.
