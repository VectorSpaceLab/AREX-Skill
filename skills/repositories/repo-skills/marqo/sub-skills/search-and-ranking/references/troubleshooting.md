# Search and Ranking Troubleshooting

Use this file when a Marqo search or recommend payload is syntactically valid JSON but rejected, returns unexpected ranking metadata, or produces empty results.

## Fast triage flow

1. Confirm `searchMethod` and `q` shape match the matrix in `ranking-parameters.md`.
2. Remove advanced features and retry the minimal payload: `q`, `searchMethod`, `limit`, `filter`.
3. Add back one group at a time: searchable attributes → score modifiers → hybrid parameters → facets/sort/collapse/recency/relevance cutoff.
4. If the error names an index field or schema support, route index setup to `../index-and-vespa/`.
5. If the error names model loading, vectorisation, media download, or embedding dimensions, route backend diagnosis to `../inference-and-models/`.

## Symptom-to-fix table

| Symptom or error fragment | Likely cause | Recovery |
|---|---|---|
| `Query(q) is required for lexical search` | Lexical search was called with `q: null`. | Supply a string `q` or switch to tensor/hybrid with `context`. |
| `Multi-term query is not supported for search_method="LEXICAL"` | Lexical `q` is a weighted dict. | Convert to a string lexical query, or switch to tensor search. |
| `To use multi-term query with search_method="HYBRID", use hybrid_parameters.queryTensor` | Hybrid top-level `q` is a dict. | Set `q: null`, move the dict to `hybridParameters.queryTensor`, and provide `queryLexical` if lexical text differs. |
| `Custom vector search is only supported...` | `customVector` used with lexical search. | Use `TENSOR` or `HYBRID`; for hybrid include `customVector.content` if lexical ranking should use text. |
| `Cannot use 'context' for a search with a string 'q'` | Tensor search has a string query and `context.tensor`/documents. | Use a weighted dict query, `customVector`, or `q: null` with `context`. |
| `Context is not supported for lexical search` | `context.documents` or tensor context used with lexical search. | Remove context, or switch to tensor/hybrid. |
| `language parameter is not supported for TENSOR` | `language` provided on tensor search. | Use lexical or hybrid search, or remove `language`. |
| `efSearch is not a valid argument for lexical search` | HNSW tensor parameter used on lexical search. | Remove `efSearch`, or switch to tensor/hybrid. |
| `approximate is not a valid argument for lexical search` | Tensor approximate search flag used on lexical search. | Remove `approximate`, or switch to tensor/hybrid. |
| `approximateThreshold` errors | Threshold is on lexical search, outside 0..1, or set while `approximate` is false. | Use only tensor/hybrid approximate search; keep threshold in 0..1; omit it when exact search is requested. |
| `rerankDepth` errors | `rerankDepth` on lexical search, negative value, or hybrid ranking not RRF. | Use tensor search, or hybrid `rankingMethod: rrf`; keep value non-negative. |
| `alpha can only be defined for 'rrf'` | `alpha` set with tensor/lexical ranking. | Remove `alpha` or use `rankingMethod: rrf`. |
| `rrfK can only be defined for 'rrf'` | `rrfK` set with non-RRF ranking. | Remove `rrfK` or use RRF. |
| `weakAndParameters can only be set when rerankDepthLexical is set` | Weak-and tuning without lexical candidate depth. | Add `hybridParameters.rerankDepthLexical` >= 1, or remove `weakAndParameters`. |
| `secondPhaseModifier` errors | Second-phase lexical modifiers used on an unsupported retrieval/ranking mode, unsupported schema, or collapse sort-by pass. | Use disjunction or lexical/lexical hybrid on supported semi-structured indexes; do not combine with collapse sort-by execution. |
| `searchableAttributes cannot be used for hybrid search` | Top-level `searchableAttributes` sent with hybrid. | Move values to `hybridParameters.searchableAttributesTensor` and/or `searchableAttributesLexical`. |
| `searchableAttributesTensor` / `searchableAttributesLexical` compatibility errors | Attribute list placed on a leg that is not retrieved or ranked. | Match tensor attributes with tensor retrieval/ranking; match lexical attributes with lexical retrieval/ranking. |
| `Hybrid search ... unstructured indexes ... searchableAttributes...` | Legacy unstructured index does not support hybrid searchable-attribute narrowing. | Remove hybrid searchable attributes, or use a semi-structured index with compatible schema. |
| `Facets can only be provided for 'HYBRID' search` | `facets` on tensor/lexical search. | Switch to hybrid search or remove `facets`. |
| `trackTotalHits can only be provided for 'HYBRID' search` | `trackTotalHits` on tensor/lexical search. | Switch to hybrid search or remove `trackTotalHits`. |
| `Recency parameters can only be provided for 'HYBRID' search` | `recencyParameters` on tensor/lexical search. | Switch to hybrid search or remove recency. |
| `Recency scoring is only supported...` | Recency on structured/old index schema or old schema for additive/grow/center/subquery options. | Use a compatible semi-structured/unstructured index; remove unsupported recency sub-options. |
| `sortBy can only be provided for 'HYBRID' search` | `sortBy` on tensor/lexical search. | Switch to hybrid search or remove `sortBy`. |
| `sortBy cannot be used with scoreModifiers` | Global hybrid score modifiers and sort both operate in the global rerank phase. | Choose `sortBy` or global `scoreModifiers`; leg-specific score modifiers may be a better fit. |
| `sortBy cannot be used with recencyParameters...` | Sort bypasses global relevance scoring while recency wants global-phase rerank. | Set `recencyParameters.applyInRankingPhase: exclude-global`, or remove one feature. |
| `relevanceCutoff can only be provided for 'HYBRID' search` | Relevance cutoff on tensor/lexical search. | Switch to hybrid search or remove cutoff. |
| `applyInRetrieval can only be set when retrievalMethod is 'disjunction'` | Relevance cutoff retrieval-leg targeting without disjunction. | Use `hybridParameters.retrievalMethod: disjunction`, or omit `applyInRetrieval`. |
| `applyInRetrieval='lexical' is not currently supported` | Relevance cutoff targets lexical-only leg. | Use `tensor` or `both`. |
| `Exactly one collapse field must be provided` | `collapseFields` list is empty or has more than one entry. | Provide exactly one collapse model. |
| `Field '<name>' is not configured as a collapse field` | Collapse field not configured in index settings. | Route index update/configuration to `../index-and-vespa/`, or choose an existing collapse field. |
| `collapseFields ... only supported...` | Collapse on structured or old index. | Use a compatible semi-structured/unstructured index. |
| `collapse.sortBy` errors | Collapse sort-by on unsupported index/schema or conflicts with second-phase modifier. | Remove collapse sort-by, remove second-phase modifier, or update index schema. |
| `Error validating score_modifiers` | Malformed `scoreModifiers` object. | Provide at least one non-empty `multiply_score_by` or `add_to_score` list; use `field_name` and numeric `weight`; avoid `_id`. |
| `_id is not allowed as a field_name` | Score modifier targets `_id`. | Use a numeric ranking field, filter on `_id`, or sort/collapse by another configured field. |
| `Boosting is not currently supported with Vespa` | Legacy `boost` parameter reached Vespa-backed search. | Translate boost intent to `scoreModifiers`, `sortBy`, or a filter rule. |
| Custom score rerank unsupported | `marqo__score_*` key used on structured/old schema or unsupported metric. | Use compatible semi-structured/unstructured schema; avoid closeness custom scores on geodegrees distance metric. |
| `Cannot parse empty filter string` / `Empty filter string` | Filter is `""` or only whitespace. | Omit `filter`. |
| `Unexpected AND/OR/NOT` or unbalanced parentheses | Malformed filter grammar. | Rewrite with explicit terms and balanced parentheses. See `filter-and-modifier-reference.md`. |
| `The 'IN' filter keyword is only supported for the '_id' field` | `IN` used on a non-id field. | Use equality OR terms or a numeric range. |
| `CONTAINS filter field ... not found` | `CONTAINS` on a field that is not lexically searchable. | Use a lexical field/searchable attribute, or route field setup to `../index-and-vespa/`. |
| Facet `excludeTerms` errors | `excludeTerms` supplied without filter or with terms not present in filter. | Add a filter and ensure each excluded term string appears exactly in the filter. |
| Missing `facets` in response | Facets not requested, wrong search method, unsupported index path, or facet field unavailable. | Use hybrid search with `facets`, verify field type, and expect empty dicts for array facets with no hits. |
| Missing `totalHits` | `trackTotalHits` not requested or Vespa did not return total hit metadata. | Set `trackTotalHits: true`; if absent after postprocess, Marqo may report `0` or cap by max retrievable docs. |
| Missing `_highlights` | `showHighlights` false, highlights unavailable for selected path, or lexical search returned empty highlights. | Set `showHighlights: true`; do not rely on highlights for every search method/field. |
| `Marqo could not collect any vectors...` | Query/context/recommend inputs produced no valid vector. | Check `q`, custom vector dimensions, context tensors, context documents, model availability, and document embeddings. |
| `No document IDs provided` | Recommend/context documents list empty or null. | Provide a non-empty list or dict of ids. |
| `Duplicate document IDs found` | Recommend document list contains duplicates. | De-duplicate ids or use a dict of id weights. |
| `No documents with non-zero weight provided` | Recommend dict weights are all zero. | Keep at least one non-zero weight. |
| `do not have embeddings` / `not found` | Recommendation/context document ids missing or lack embeddings. | Enable `allowMissingDocuments` / `allowMissingEmbeddings` only if dropping those docs is acceptable; otherwise re-index or choose tensor fields that have embeddings. |
| `Cannot interpolate vectors with all zero weights` | Recommend interpolation received all-zero effective weights. | Adjust weights or drop zero-weight docs. |
| `zero-magnitude vector` | NLERP normalization cannot normalize the interpolated vector. | Use non-cancelling vector weights, switch interpolation method if valid, or inspect embeddings. |
| Missing rank profile / no tensor or lexical fields | Search method requires field type not present in the index. | Tensor search requires tensor fields; lexical search requires lexical fields; hybrid requires both unless configured as pure tensor/lexical hybrid. Route schema repair to `../index-and-vespa/`. |

## Filter repair examples

Invalid:

```json
{
  "q": "red backpack",
  "searchMethod": "HYBRID",
  "filter": "category IN (backpack, luggage)",
  "hybridParameters": {"retrievalMethod": "disjunction", "rankingMethod": "rrf"}
}
```

Repaired:

```json
{
  "q": "red backpack",
  "searchMethod": "HYBRID",
  "filter": "category:backpack OR category:luggage",
  "hybridParameters": {"retrievalMethod": "disjunction", "rankingMethod": "rrf"}
}
```

## Incompatible-parameter repair examples

Invalid:

```json
{
  "q": {"red backpack": 1.0, "waterproof": 0.5},
  "searchMethod": "LEXICAL",
  "efSearch": 100,
  "approximate": true
}
```

Repaired as tensor search:

```json
{
  "q": {"red backpack": 1.0, "waterproof": 0.5},
  "searchMethod": "TENSOR",
  "efSearch": 100,
  "approximate": true
}
```

Repaired as lexical search:

```json
{
  "q": "red waterproof backpack",
  "searchMethod": "LEXICAL"
}
```

Hybrid repair for top-level searchable attributes:

```json
{
  "q": "red backpack",
  "searchMethod": "HYBRID",
  "hybridParameters": {
    "retrievalMethod": "disjunction",
    "rankingMethod": "rrf",
    "searchableAttributesTensor": ["title", "description"],
    "searchableAttributesLexical": ["title", "description"]
  }
}
```

## Service/model dependency boundaries

- Lexical search still needs a running Marqo/Vespa service and lexically searchable fields, but it does not need vectorisation.
- Tensor and hybrid search need inference/model availability for string/dict/media queries unless all required vectors are supplied through `customVector` or `context.tensor`.
- Recommendation needs document-vector retrieval and interpolation before search; failures often happen before the final search request.
- Media URLs/pointers require a modality-capable index/model and successful media download. Use `mediaDownloadHeaders` for safe headers; do not put secrets in examples.
- Backend start/stop, Docker, Vespa, Triton, or API route health checks are not owned by this sub-skill. Route to the owning sub-skill rather than embedding service commands here.
