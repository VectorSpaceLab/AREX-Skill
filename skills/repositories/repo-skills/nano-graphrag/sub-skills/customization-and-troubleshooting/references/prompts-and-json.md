# Prompts and JSON repair

This reference explains how to customize nano-graphrag's prompt dictionary and how the default JSON repair function behaves when provider output is malformed.

## Prompt dictionary customization

nano-graphrag keeps prompts and prompt constants in the mutable dictionary `nano_graphrag.prompt.PROMPTS`. Import and edit the dictionary before running insert/query work that depends on the prompt.

Common keys:

| Key | Used for |
| --- | --- |
| `entity_extraction` | Extracting entity and relationship tuple records from chunks. |
| `entiti_continue_extraction` | Follow-up extraction turn for missed entities. The misspelling is the actual key. |
| `entiti_if_loop_extraction` | Stop/continue decision for additional gleaning turns. The misspelling is the actual key. |
| `summarize_entity_descriptions` | Summarizing merged long node/edge descriptions. |
| `community_report` | Asking the LLM to generate a JSON report for one graph community. |
| `global_map_rag_points` | Asking the LLM for JSON points during global search map stage. |
| `global_reduce_rag_response` | Final global answer synthesis prompt. |
| `local_rag_response` | Local query answer prompt using graph context tables. |
| `naive_rag_response` | Naive RAG answer prompt using retrieved chunks. |
| `fail_response` | Fallback text when retrieval finds no usable context. |
| `default_text_separator` | Separator list used by separator-based chunking. |

Core constants:

```python
GRAPH_FIELD_SEP = "<SEP>"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["DEFAULT_ENTITY_TYPES"] = ["organization", "person", "geo", "event"]
```

Minimal prompt edit pattern:

```python
from nano_graphrag.prompt import PROMPTS

PROMPTS["entity_extraction"] = PROMPTS["entity_extraction"] + """

Important: Return only tuple records in the exact examples' format. Do not add prose.
"""
```

Keep prompt edits narrow. The parser is strict about tuple records for entity extraction, while JSON parsing is only used for report/global-map responses.

## Entity extraction output is not JSON

The default entity extractor expects records like:

```text
("entity"<|>"ALICE"<|>"person"<|>"Alice is described in the chunk.")##
("relationship"<|>"ALICE"<|>"BOB"<|>"Alice works with Bob."<|>7)<|COMPLETE|>
```

`convert_response_to_json_func` does not repair this tuple output. If a provider returns JSON or Markdown for entity extraction, fix the extraction prompt/system instruction or use a custom/DSPy extraction function.

## Community report JSON shape

`generate_community_report` calls the configured `best_model_func` with `PROMPTS["community_report"]`, then converts the raw response with `convert_response_to_json_func`. The expected JSON object is:

```json
{
  "title": "Community title",
  "summary": "Executive summary of the community",
  "rating": 5.0,
  "rating_explanation": "One sentence explaining the rating",
  "findings": [
    {
      "summary": "Finding title",
      "explanation": "Grounded explanation using only provided evidence"
    }
  ]
}
```

Downstream behavior:

- The report-to-Markdown converter uses `title`, `summary`, and `findings`.
- `rating` is used for ranking/filtering communities in global query flows.
- Missing keys may not raise immediately, but they produce weak reports and poor global search behavior.
- The prompt's grounding rule says not to include information unsupported by the community text.

## Global map JSON shape

The global-map stage also uses `convert_response_to_json_func`. It expects:

```json
{
  "points": [
    {"description": "Relevant point", "score": 100}
  ]
}
```

Only points with a `description` and positive `score` become support for the final global answer.

## Default `convert_response_to_json` behavior

The default parser is `nano_graphrag._utils.convert_response_to_json(response: str) -> dict`.

It works in two passes:

1. `extract_first_complete_json` scans for the first balanced `{...}` object and tries `json.loads` after removing newlines.
2. If no complete valid object is parsed, `extract_values_from_json` uses a permissive key/value regex and converts values such as integers, floats, `true`, `false`, and `null`.

Behavior to expect:

- Valid JSON objects with prose before/after them are usually recovered because the first complete object is extracted.
- Valid nested JSON is handled by the strict first-pass parser.
- Incomplete JSON can sometimes be partially recovered by fallback key/value extraction.
- Non-standard unquoted nested keys can be recovered in simple cases.
- The function returns an empty dict when it cannot recover meaningful key/value data.
- It does not validate that recovered data matches the community-report or global-map schema.

Use the bundled probe from the sub-skill root:

```bash
python scripts/json_repair_probe.py --text '{"title":"Ok","summary":"..."}' --pretty
```

or pipe raw model output:

```bash
cat response.txt | python scripts/json_repair_probe.py --pretty
```

## Malformed JSON gotchas

- Top-level arrays are not the expected shape; wrap them in an object if the prompt target is report/global-map JSON.
- Multiple JSON objects in one response: only the first complete object is used.
- Missing `findings`, `title`, or `points` may still parse successfully but fail semantically downstream.
- Heavily malformed nested structures may be partially recovered with strings where dicts were expected.
- Provider wrappers that reject `response_format={"type": "json_object"}` should strip that unsupported kwarg in provider code, then rely on stricter prompts and/or a custom `convert_response_to_json_func`.

A custom parser can be passed as:

```python
from nano_graphrag import GraphRAG
from nano_graphrag._utils import convert_response_to_json

def my_report_json(response: str) -> dict:
    data = convert_response_to_json(response)
    if not isinstance(data, dict):
        return {}
    # Add project-specific validation or repair here.
    return data

rag = GraphRAG(convert_response_to_json_func=my_report_json)
```
