# Filter and Modifier Reference

This reference covers Marqo filter strings, safe filter composition, score modifiers, custom score rerank keys, and legacy boost behavior.

## Filter grammar

A filter is a string parsed into a tree of terms, operators, and modifiers. Use uppercase operators for readability even though some term dividers are case-insensitive.

| Syntax | Meaning | Example | Notes |
|---|---|---|---|
| `field:value` | Equality term | `brand:acme` | Value may be grouped as `field:(multi word value)`. |
| `field:[lower TO upper]` | Numeric range | `price:[0 TO 100]` | Use `*` for an open side: `price:[* TO 100]`. |
| `_id IN (a, b)` | Id list | `_id IN (doc1, doc2)` | On semi-structured indexes, `IN` is supported only for `_id`; use `OR` equality terms for other fields. |
| `field CONTAINS value` | Lexical field contains term | `description CONTAINS waterproof` | Field must be a lexical field in the index. |
| `NOT expr` | Negation | `NOT brand:excluded` | Use parentheses for multi-term negation: `NOT (brand:a OR brand:b)`. |
| `expr AND expr` | Conjunction | `category:backpack AND inStock:true` | `AND` is greedy in stringification. |
| `expr OR expr` | Disjunction | `brand:a OR brand:b` | Parenthesize mixed `AND`/`OR` logic. |
| `(expr)` | Grouping | `(brand:a OR brand:b) AND price:[0 TO 100]` | Extra parentheses are tolerated when balanced. |
| `\` escape | Escape spaces/special chars | `My\ Field\-:(hello\ world)` | Backslash escapes spaces, quotes, and backslashes in field names/values. |

## Valid filter examples

```text
category:backpack AND price:[0 TO 100]
NOT (brand:blocked OR brand:unsafe)
_id IN (doc1, doc2, doc3)
description CONTAINS waterproof AND inStock:true
(color:red OR color:burgundy) AND NOT size:(kids small)
```

## Common malformed filters and recoveries

| Invalid filter | Why it fails | Safer rewrite |
|---|---|---|
| `category IN (backpack, luggage)` | `IN` is only supported for `_id` on semi-structured indexes. | `category:backpack OR category:luggage` |
| `price IN (20, 30)` | Numeric membership is not the supported `IN` use case. | `price:20 OR price:30`, or a range such as `price:[20 TO 30]` |
| `brand:a OR` | Ends with an operator. | `brand:a` or `brand:a OR brand:b` |
| `a:1 (b:2)` | Missing operator between expressions. | `a:1 AND b:2` |
| `a IN (one two)` | Ungrouped whitespace inside an `IN` value. | `a IN ((one two))` when the field is `_id`; otherwise use equality/OR. |
| `description CONTAINS [0 TO 1]` | Range syntax is only for range terms. | `description CONTAINS 0` or a numeric field range. |
| `` | Empty filter string. | Omit `filter` entirely. |

## Filter composition rules

- Prefer simple filters first, then add parentheses only where precedence matters.
- Use grouped text values for spaces: `field:(hello world)`.
- Use range syntax only as `field:[lower TO upper]`.
- Use `CONTAINS` only on lexical fields; if the field is unavailable, repair the index or use a searchable attribute in lexical/hybrid search.
- If `facets.fields.<field>.excludeTerms` is set, a non-empty `filter` must also be set and each excluded term string must appear in the filter.
- For recommendation exclusion filters, structured indexes use `NOT _id IN (...)`; semi-structured/unstructured search paths use a negated OR of `_id:(...)` equality terms.

## Score modifier object shape

`scoreModifiers` and hybrid leg-specific score modifiers use this object shape:

```json
{
  "scoreModifiers": {
    "multiply_score_by": [
      {"field_name": "margin", "weight": 1.1}
    ],
    "add_to_score": [
      {"field_name": "rating", "weight": 0.05}
    ]
  }
}
```

Validation rules:

- At least one of `multiply_score_by` or `add_to_score` must be provided.
- If a list is present, it must contain at least one operator.
- Each operator has `field_name` and numeric `weight`; extra keys are rejected.
- `_id` is forbidden as a `field_name`.
- Score modifier field values must be available as numeric score-modifier signals in the search backend; if the field was never indexed as numeric, score changes may be absent or ineffective.

## Where to place score modifiers

| Placement | Payload location | Use when | Key restriction |
|---|---|---|---|
| Tensor/lexical classic modifiers | Top-level `scoreModifiers` | You want field values to add/multiply score in tensor or lexical search. | `_id` forbidden; fields should be numeric score-modifier fields. |
| Hybrid global modifiers | Top-level `scoreModifiers` | You want a global modifier after hybrid RRF fusion. | Hybrid `rankingMethod` must be `rrf`; conflicts with `sortBy`. |
| Hybrid tensor leg | `hybridParameters.scoreModifiersTensor` | You want to modify tensor leg before/inside hybrid fusion. | Requires tensor or RRF ranking. |
| Hybrid lexical leg | `hybridParameters.scoreModifiersLexical` | You want to modify lexical leg before/inside hybrid fusion. | Requires lexical or RRF ranking, or lexical retrieval. |
| Custom score rerank | Top-level `scoreModifiers` fields prefixed with `marqo__score_` | You want BM25/closeness summary features in global RRF rerank. | Semi-structured/unstructured search path and supported schema only. |

## Custom score rerank keys

Custom rerank keys start with `marqo__score_`; the suffix is parsed as either a per-field key or aggregate key.

| API field name | Meaning |
|---|---|
| `marqo__score_bm25_field_title` | BM25 score for lexical field `title`. |
| `marqo__score_bm25_sum` | Aggregate BM25 sum across lexical fields. |
| `marqo__score_bm25_max` | Aggregate BM25 max across lexical fields. |
| `marqo__score_bm25_avg` | Aggregate BM25 average across lexical fields. |
| `marqo__score_closeness_retrieval_vector_field_image` | Tensor closeness score for tensor field `image`. |
| `marqo__score_closeness_retrieval_vector_sum` | Aggregate tensor closeness sum across tensor fields. |
| `marqo__score_closeness_retrieval_vector_max` | Aggregate tensor closeness max across tensor fields. |
| `marqo__score_closeness_retrieval_vector_avg` | Aggregate tensor closeness average across tensor fields. |

Operational cautions:

- Invalid custom score suffixes are ignored before custom reranking.
- Aggregate BM25 keys are omitted when the index has no lexical fields; aggregate closeness keys are omitted when the index has no tensor fields.
- Per-field custom score keys that reference missing fields are tolerated by the searcher and usually contribute no score change.
- Closeness-based custom reranking is not supported for indexes using the geodegrees distance metric.
- When custom score rerank is used together with `attributesToRetrieve`, Marqo must fetch summary features for sub-query hits so that global rerank has the needed scores.

## Legacy `boost`

`boost` is not the same as `scoreModifiers`.

```json
{
  "boost": {
    "rating": [1.2],
    "margin": [0.8, 0.1]
  }
}
```

Validation recognizes tensor-only boost with valid field names and numeric weight/bias arrays. In the current Vespa-backed search path, boost is still rejected as unsupported. Prefer `scoreModifiers` unless you are explicitly diagnosing legacy behavior.

## Safe request-builder checklist

1. Build filters with equality, range, `_id IN`, `CONTAINS`, `AND`, `OR`, and `NOT`; avoid unsupported SQL-like syntax.
2. Keep facet `excludeTerms` identical to strings in the filter.
3. Place score modifiers according to search method and hybrid ranking mode.
4. Do not add `boost` to production payloads; translate boost intent into `scoreModifiers` or a sort/filter rule.
5. If a filter or modifier repairs the symptom but changes semantics, report the semantic change in the handoff.
