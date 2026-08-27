# Customization and extraction troubleshooting

Use this reference for symptom-driven recovery when prompt output, JSON parsing, DSPy extraction, or entity graph construction fails. If the issue is only credentials, base URLs, provider client setup, or storage service configuration, route to the corresponding sibling sub-skill.

## `Leiden.EmptyNetworkError` during insert

Likely cause: community clustering is being run on an empty graph. In nano-graphrag this usually means entity extraction returned no usable entities/relations, not that graph storage is broken.

Recovery path:

1. Confirm the insert log before the failure. If it shows `Processed ... 0 entities(duplicated), 0 relations(duplicated)` or `No new entities found`, treat extraction as the root cause.
2. Check that the LLM output follows the tuple format, for example:

   ```text
   ("entity"<|>"CRUZ"<|>"person"<|>"Cruz is associated with a vision of control and order.")
   ```

3. Add or strengthen a system instruction in the LLM function so the model returns only the examples' tuple format, with no Markdown/prose wrapper.
4. Use a larger model or a larger context window if the provider truncated the extraction prompt.
5. If the provider repeatedly ignores tuple format, consider a custom `entity_extraction_func` or the DSPy extractor workflow.

Do not start by changing vector or graph storage unless extraction produced nonzero entities and clustering still fails.

## `Processed N chunks, 0 entities / 0 relations` with Ollama or local models

Likely cause: the local model context window is too small for the long entity-extraction prompt plus chunk text. The common Ollama default `num_ctx` of `2048` is often insufficient.

Fix pattern:

1. Create a Modelfile from the current model.
2. Add a larger context parameter, for example:

   ```text
   PARAMETER num_ctx 32000
   ```

3. Create a new model tag from that Modelfile.
4. Point the provider function at the new larger-context model.
5. Re-run a small insert and confirm entity/relation counts become nonzero.

If counts remain zero after increasing context, inspect raw provider output: the model may still be returning prose, JSON, or truncated text instead of tuple records.

## Malformed provider output

There are two distinct output formats:

- Entity extraction expects tuple records, not JSON.
- Community report and global-map prompts expect JSON objects and use `convert_response_to_json_func`.

For entity extraction:

- Enforce the tuple schema in the system prompt.
- Remove extra provider wrappers that add Markdown/code fences around the tuple records.
- Keep delimiters exactly aligned with `PROMPTS["DEFAULT_TUPLE_DELIMITER"]`, `PROMPTS["DEFAULT_RECORD_DELIMITER"]`, and `PROMPTS["DEFAULT_COMPLETION_DELIMITER"]`.
- If a provider cannot follow tuple formatting, switch to a custom extractor or DSPy path.

For JSON report/global-map parsing:

- Run `scripts/json_repair_probe.py` on the raw response to see whether default repair recovers a non-empty dict.
- If parsing succeeds but required keys are missing, tighten the prompt or add validation in a custom `convert_response_to_json_func`.
- If a provider rejects `response_format={"type": "json_object"}`, fix the provider wrapper in the provider integration sub-skill, then return here for repair/validation behavior.

## Compiled DSPy module path missing

Symptom examples:

- The DSPy extraction path fails before processing chunks.
- A config enables compiled DSPy extraction but no compiled module is available.
- A loader error references `entity_relationship_module_path`.

Recovery:

1. If you do not intend to use a compiled DSPy module, set `use_compiled_dspy_entity_relationship` to false or omit it.
2. If you do intend to use one, ensure `global_config` includes both:

   ```python
   {
       "use_compiled_dspy_entity_relationship": True,
       "entity_relationship_module_path": "path/to/compiled/module.json",
   }
   ```

3. Confirm the path points to a compiled DSPy module file created by your training/compile workflow.
4. If using DSPy as `GraphRAG(entity_extraction_func=...)`, ensure the function or adapter accepts the keyword arguments that `GraphRAG.insert` passes.

## DSPy `BadRequestError` returns empty extraction

The DSPy helpers catch provider `BadRequestError` and treat that chunk as `entities=[]` and `relationships=[]`. If every chunk hits this fallback, the final result can look like an ordinary zero-entity extraction.

Common causes:

- Provider rejects the structured output/schema prompt.
- Request exceeds the model/provider context or token limit.
- Provider-specific kwargs are invalid for the selected client.
- The DSPy LM is not configured or is configured for a different provider shape than the model expects.

Recovery:

1. Inspect the log/error body from the provider request.
2. Reduce chunk size or model output budget if the request is too long.
3. Validate provider setup in `provider-and-model-integrations` if the error is about client kwargs, credentials, base URL, or model name.
4. Re-run on one tiny chunk before using a full corpus.
5. If a `ValueError` inside the DSPy prediction is converted to empty lists, reduce schema complexity or test the `TypedEntityRelationshipExtractor` directly on a short sentence.

## Custom prompt makes extraction worse

Likely causes:

- The edit changed field order, delimiters, quote style, or completion delimiter.
- The prompt now requests broad prose before/after records.
- New entity types conflict with the parser's expected tuple fields.
- A long prompt pushes local models over their context window.

Recovery:

1. Restore the default delimiter constants.
2. Add constraints without changing the examples' record format.
3. Test on one short chunk and verify at least one entity and one relationship are parsed.
4. Increase `entity_extract_max_gleaning` only after the first pass produces valid records.
5. For domain-specific entity types, change the entity type list or prompt examples, not the parser field order.

## JSON parse succeeds but downstream report is weak

Parsing a dict is not the same as producing a useful report. Check required semantic keys:

- Community reports should include `title`, `summary`, numeric `rating`, `rating_explanation`, and `findings` with `summary`/`explanation` entries.
- Global map responses should include `points` with positive `score` values and `description` strings.

If keys are missing, wrap `convert_response_to_json` with validation that returns `{}` or repairs defaults, and tighten the relevant prompt.
