# Entity extraction customization

This reference covers nano-graphrag's entity/relation extraction surfaces: the default tuple prompt parser, the gleaning loop, graph merge behavior, and the DSPy-based extractor family.

## Default prompt extractor contract

`GraphRAG` defaults to the async `extract_entities` implementation. During insert it sends each chunk through `PROMPTS["entity_extraction"]` and parses only parenthesized records that match the configured delimiters.

Default constants that matter to the parser:

| Constant | Default | Why it matters |
| --- | --- | --- |
| `PROMPTS["DEFAULT_ENTITY_TYPES"]` | `organization`, `person`, `geo`, `event` | Entity types inserted into the prompt unless you customize the prompt dictionary. |
| `PROMPTS["DEFAULT_TUPLE_DELIMITER"]` | `<|>` | Field separator inside an entity or relationship record. |
| `PROMPTS["DEFAULT_RECORD_DELIMITER"]` | `##` | Separator between records in the model output. |
| `PROMPTS["DEFAULT_COMPLETION_DELIMITER"]` | `<|COMPLETE|>` | Completion marker that also terminates record splitting. |
| `GRAPH_FIELD_SEP` | `<SEP>` | Internal separator for merged descriptions and source ids after extraction. |

The parser accepts records shaped like this:

```text
("entity"<|>"ENTITY NAME"<|>"ENTITY TYPE"<|>"Entity description")
("relationship"<|>"SOURCE ENTITY"<|>"TARGET ENTITY"<|>"Relationship description"<|>7)
```

Important parser details:

- The first tuple field must be exactly `"entity"` or `"relationship"` after delimiter splitting.
- Entity names, entity types, source ids, and target ids are cleaned and uppercased before graph insertion.
- Relationship strength is converted to `float` when possible; otherwise the relationship weight defaults to `1.0`.
- Free-form prose, Markdown tables, JSON objects, or records without parentheses are ignored by the default prompt parser.
- If you change delimiter constants, keep the prompt and parser constants synchronized before the next insert.

## `entity_extract_max_gleaning`

`GraphRAG(entity_extract_max_gleaning=1)` controls how many follow-up extraction turns are attempted after the first entity-extraction response.

The loop uses these prompt dictionary keys:

- `PROMPTS["entiti_continue_extraction"]`: asks the model to add missed entities using the same format.
- `PROMPTS["entiti_if_loop_extraction"]`: asks whether more entities remain; the loop stops when the model answer is not `yes`.

Increasing gleaning can improve recall, but it also increases provider calls and can multiply malformed-output risk. If zero entities are produced, first fix output format/context length; increasing gleaning alone usually will not help a model that cannot follow the tuple schema.

## Merge behavior after parsing

Parsed records are merged before graph/vector upsert:

- Nodes are grouped by normalized `entity_name`.
- Node `entity_type` is chosen by majority vote across duplicate records plus any existing node type.
- Node descriptions and `source_id` values are de-duplicated and joined with `GRAPH_FIELD_SEP` (`<SEP>`).
- Edges are treated as undirected for grouping by sorting the endpoint pair before merge.
- Edge weights are summed across duplicate records and existing edge weight.
- DSPy-style relationship `order` is preserved as the minimum observed order; default prompt relationships have implicit order `1`.
- If an edge endpoint node is missing, an `UNKNOWN` node is inserted so the edge can exist.
- Very long merged entity/relation descriptions are summarized through the configured `cheap_model_func` when they exceed `entity_summary_to_max_tokens`.
- When an entity vector store is enabled, extracted entity records are embedded with content equal to `entity_name + description` and metadata containing `entity_name`.

Because source ids and descriptions are joined with `GRAPH_FIELD_SEP`, avoid changing `GRAPH_FIELD_SEP` after a working directory already contains graph data.

## Custom `entity_extraction_func` wiring

`GraphRAG.insert` calls the configured extraction function with the chunk dict plus keyword arguments for graph storage, entity vector storage, tokenizer wrapper, global config, and the Amazon Bedrock flag. A custom function should either accept those keywords or be wrapped by an adapter that accepts extra keyword arguments and forwards only what it needs.

A safe adapter pattern is:

```python
async def my_entity_extraction_adapter(
    chunks,
    knwoledge_graph_inst,
    entity_vdb,
    tokenizer_wrapper=None,
    global_config=None,
    using_amazon_bedrock=False,
    **_ignored,
):
    # Build maybe_nodes/maybe_edges from chunks, then upsert to graph storage.
    # Return the graph storage when at least one entity is present; return None on no entities.
    ...
```

Return `None` only when extraction truly produced no usable entities. Returning `None` causes insertion to stop before clustering/community reports.

## DSPy extractor workflow

The DSPy path centers on `TypedEntityRelationshipExtractor`, which is a DSPy module with structured outputs:

- `Entity`: `entity_name`, `entity_type`, `description`, `importance_score` in `[0, 1]`.
- `Relationship`: `src_id`, `tgt_id`, `description`, `weight` in `[0, 1]`, and `order` in `{1, 2, 3}`.
- `CombinedExtraction`: extracts entities and relationships from `input_text` using a broad default entity type list.
- Optional self-refine: `CritiqueCombinedExtraction` critiques the first pass, and `RefineCombinedExtraction` updates entities/relationships for `num_refine_turns`.

Two high-level async helpers are available:

- `generate_dataset(chunks, filepath, save_dataset=True, global_config={})` runs the DSPy extractor on chunks, filters out examples with no entities or no relationships, and optionally saves a pickle dataset. Use `save_dataset=False` for inspection without writing a file.
- `extract_entities_dspy(chunks, knwoledge_graph_inst, entity_vdb, global_config)` runs the DSPy extractor and merges the resulting entity/relation dicts into graph/vector storage.

Compiled module loading is controlled by `global_config`:

```python
global_config = {
    "use_compiled_dspy_entity_relationship": True,
    "entity_relationship_module_path": "path/to/compiled/module.json",
}
```

When the flag is true, the extractor calls `.load(global_config["entity_relationship_module_path"])`. If you do not have a compiled module file, leave the flag false.

## DSPy metrics and benchmark guidance

Available metric helpers:

- `entity_recall_metric(gold, pred)`: set-based entity-name recall.
- `relationships_similarity_metric(gold, pred)`: a DSPy Chain-of-Thought scorer that compares matched relationship pairs, descriptions, weights, and order.

Provider-backed DSPy examples, benchmark scripts, and notebooks are reference-only for this sub-skill. They show how DSPy can trade extra runtime/provider cost for different extraction coverage. Do not run them by default: they require credentials, external model calls, and benchmark-scale runtime. Use them only after a user explicitly asks for DSPy training/evaluation and the provider setup has been handled by the provider integration sub-skill.
