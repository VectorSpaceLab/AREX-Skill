---
name: prompt-tuning
description: "Run, plan, and diagnose GraphRAG prompt tuning for indexing prompt
  templates, including graphrag prompt-tune and generate_indexing_prompts
  outputs for entity extraction, entity summarization, community report
  summarization, multilingual/domain guidance, and entity-type discovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GraphRAG Prompt Tuning

Use this sub-skill when a task mentions GraphRAG prompt tuning, auto/manual tuning, `graphrag prompt-tune`, `generate_indexing_prompts`, `extract_graph` prompts, entity extraction prompts, entity summarization prompts, community report prompts, multilingual tuning, domain tuning, or discovered entity types.

Do not use this sub-skill for full indexing execution; route that to `../indexing/`. Do not use it for initial workspace setup, config loading, or input data layout except where prompt tuning depends on those fields; route setup work to `../configuration-data/`. Do not cover general query prompts except to explain that this sub-skill only produces indexing prompt templates.

## Prompt Tune Workflow

1. Confirm that the workspace has been initialized and has a valid GraphRAG config plus readable input data.
2. Choose an approach:
   - CLI: `graphrag prompt-tune --root <project> --output prompts` for operator workflows.
   - API: `await generate_indexing_prompts(config, ...)` when embedding prompt tuning in Python automation.
   - Manual: edit plaintext prompt files directly when the user wants precise token placeholders instead of generated templates.
3. Pick sampling settings:
   - `--selection-method random` for the default representative sample.
   - `--selection-method top` for deterministic head-of-corpus inspection.
   - `--selection-method all` only for small corpora.
   - `--selection-method auto --n-subset-max <n> --k <k>` for embedding-based representative selection.
4. Set task guidance explicitly when possible:
   - `--domain "<domain>"` avoids an extra domain inference step.
   - `--language "<target language>"` controls prompt language and can request translated output guidance.
   - `--discover-entity-types` lets the LLM infer entity types; `--no-discover-entity-types` uses untyped extraction templates.
5. Validate the three generated files before wiring them into indexing config.

## CLI Pattern

```bash
graphrag prompt-tune \
  --root <project> \
  --domain "environmental news" \
  --language English \
  --selection-method random \
  --limit 15 \
  --max-tokens 2000 \
  --chunk-size 200 \
  --min-examples-required 2 \
  --output prompts
```

The CLI writes:

- `extract_graph.txt`
- `summarize_descriptions.txt`
- `community_report_graph.txt`

After generation, configure indexing to use those prompt files:

```yaml
extract_graph:
  prompt: "prompts/extract_graph.txt"
summarize_descriptions:
  prompt: "prompts/summarize_descriptions.txt"
community_reports:
  prompt: "prompts/community_report_graph.txt"
```

## API Pattern

```python
from graphrag.api.prompt_tune import generate_indexing_prompts
from graphrag.config.load_config import load_config

config = load_config(root_dir=project_root)
extract_graph, summarize_descriptions, community_report = await generate_indexing_prompts(
    config=config,
    limit=15,
    selection_method="random",
    domain="environmental news",
    language="English",
    max_tokens=2000,
    discover_entity_types=True,
    min_examples_required=2,
    n_subset_max=300,
    k=15,
    verbose=True,
)
```

Persist the tuple using the live CLI filenames when writing files yourself. The API initializes `prompt-tuning.log`, loads/chunks input documents, creates the configured completion model, optionally infers domain/language/entity types, generates entity/relationship examples, and returns the three indexing prompt strings.

## Validation

Use the bundled validator to check generated output directories:

```bash
python sub-skills/prompt-tuning/scripts/validate_prompt_tune_contract.py prompts
python sub-skills/prompt-tuning/scripts/validate_prompt_tune_contract.py prompts --check-placeholders
```

`--check-placeholders` checks for expected indexing template placeholders and suspicious unmatched braces. It is intentionally static and does not call GraphRAG, LLMs, storage, or input readers.

## References

- `references/prompt-tune-api-cli.md` for CLI/API options and behavior.
- `references/prompt-template-outputs.md` for output filenames, config mapping, and placeholders.
- `references/troubleshooting.md` for failures around config/model setup, input loading, chunk sampling, LLM parsing, token budgets, braces, multilingual tuning, and filename drift.
