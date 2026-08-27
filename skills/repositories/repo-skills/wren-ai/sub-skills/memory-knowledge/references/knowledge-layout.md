# Knowledge Layout

## When to read

Read this before adding a business rule, glossary item, metric explanation, or
accepted NL→SQL pair.

## Version-5 layout

```text
project/
  knowledge/
    knowledge.yml
    rules/
    glossary/
    metrics/
    caveats/
    sql/
  instructions.md       # legacy, still read
  queries.yml           # legacy, still read for transition
  .wren/memory/         # derived optional index
```

`knowledge/rules/` stores free-form operational/business rules. `knowledge/sql/`
stores one accepted NL→SQL pair per markdown file. The index is derived from
these durable artifacts, not the reverse.

## What belongs where

| Information | Destination |
| --- | --- |
| Business default filter, naming convention, currency, canonical table | `knowledge/rules/` |
| Definition that belongs to a named business concept | `knowledge/glossary/` or `knowledge/metrics/` |
| Data-quality caveat | `knowledge/caveats/` |
| Confirmed user question and working SQL | `knowledge/sql/` via `wren memory store` |
| Model/column/relationship shape | MDL source, not knowledge files |

## Rule examples

Use explicit, reviewable language:

```markdown
## Default filters
- Revenue reporting excludes rows where `is_internal = true`.

## Naming conventions
- "active customer" means a customer with an order in the past 90 days.
```

Rules are for agents and reviewers. Do not write credentials, access tokens, or
private customer data into knowledge files.

## Query pair contract

Store accepted pairs through the CLI so Wren creates the expected metadata:

```bash
wren memory store \
  --nl "top customers by revenue" \
  --sql "SELECT customer_id, SUM(total) FROM orders GROUP BY 1" \
  --datasource postgres
```

Do not store failed, known-wrong, or purely exploratory queries. Keep the
natural-language question faithful to what the user asked; it becomes a future
retrieval signal.
