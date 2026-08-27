# Ranking Parameters

This reference describes the search payload knobs that affect retrieval, ranking, filtering, and post-processing. Use it before adding advanced hybrid features.

## Top-level `SearchQuery` fields

| Field | Allowed / useful on | Defaults / constraints | Operating note |
|---|---|---|---|
| `q` | Tensor, lexical, hybrid | String for all; weighted dict for tensor; `customVector` for tensor/hybrid; may be `null` when valid `context` or split hybrid query is supplied. | Lexical requires a string query. For hybrid split queries, set `q: null` and use `hybridParameters.queryTensor` / `queryLexical`. |
| `searchMethod` | All | Defaults to `TENSOR`; string values are normalized case-insensitively. | Valid values: `TENSOR`, `LEXICAL`, `HYBRID`. |
| `limit` | All | Default `10`; must be positive integer. | Combined with `offset` for max retrievable docs checks. |
| `offset` | All | Default `0`; cannot be negative. | Keep low unless pagination is required. |
| `rerankDepth` | Tensor, hybrid RRF | Cannot be negative; lexical rejects it. For hybrid, only supported with `rankingMethod: rrf`. | Global hybrid rerank depth is separate from `rerankDepthTensor` and `rerankDepthLexical`. |
| `efSearch` | Tensor, hybrid | Not valid for lexical. | Controls HNSW exploration. Pair with `approximate`/`approximateThreshold` carefully. |
| `approximate` | Tensor, hybrid | Defaults to true when needed. Not valid for lexical. | If false and Vespa reports degraded/partial coverage, search errors. |
| `approximateThreshold` | Tensor, hybrid | Must be between `0` and `1`; cannot be set when `approximate` is false. | Sent to Vespa as matching threshold. |
| `showHighlights` | All | Default `true`. | Lexical highlights may be empty lists; tensor/hybrid highlights depend on retrieved fields. |
| `filter` | All | String parsed by Marqo filter grammar. | See `filter-and-modifier-reference.md`. |
| `searchableAttributes` | Tensor and lexical | List of field names. Tensor search can be constrained by `MARQO_MAX_SEARCHABLE_TENSOR_ATTRIBUTES`. | Do not use top-level `searchableAttributes` for hybrid; use hybrid-specific fields. |
| `attributesToRetrieve` | All | List of field names. | For semi-structured/unstructured indexes, flattened map fields with matching prefixes may also be returned. |
| `boost` | Legacy tensor-only validation | Field names must be valid and weights/biases numeric, but Vespa-backed search paths reject boost. | Prefer `scoreModifiers`; treat boost failures as a request-design issue. |
| `mediaDownloadHeaders` | Tensor/hybrid multimodal | Dict of download headers. | Use this instead of deprecated `imageDownloadHeaders`; do not set both. |
| `context.tensor` | Tensor/hybrid | 1 to 64 tensor entries, each with `vector` and `weight`. | Do not combine tensor context with a string `q` for tensor search; use dict/custom vector or `q: null`. |
| `context.documents` | Tensor/hybrid | `ids` must be non-empty; parameters include `tensorFields`, `excludeInputDocuments`, `allowMissingDocuments`, `allowMissingEmbeddings`. | Not supported for lexical search or lexical/lexical hybrid. |
| `scoreModifiers` | Tensor/lexical; hybrid RRF global | At least one of `multiply_score_by` or `add_to_score`; each list must be non-empty. | Root-level hybrid modifiers require RRF and become global score modifiers. |
| `textQueryPrefix` | Tensor/hybrid vectorisation | Optional string. | Applied to text query content before vectorisation. |
| `hybridParameters` | Hybrid only | Defaults to disjunction retrieval + RRF ranking. | Forbidden for non-hybrid search. |
| `facets` | Hybrid only | Semi-structured/unstructured search path only. | Adds facet group output; can pair with `trackTotalHits`. |
| `trackTotalHits` | Hybrid only | Boolean. | Returns total hit metadata when supported; count may be capped by max retrievable docs. |
| `language` | Lexical/hybrid | Optional language code. | Tensor search rejects language because it only applies to lexical ranking. |
| `sortBy` | Hybrid only | 1 to 3 fields; see sort section below. | Cannot be combined with global `scoreModifiers`; conflicts with recency unless recency excludes global phase. |
| `relevanceCutoff` | Hybrid only | See relevance cutoff section below. | Semi-structured/unstructured search path only. |
| `interpolationMethod` | Tensor/recommend flows | `lerp`, `nlerp`, or `slerp`. | Mainly used when combining vectors from context/recommendation. |
| `collapseFields` | Hybrid only | Exactly one collapse field. | The field must already be configured as a collapse field on the index. |
| `recencyParameters` | Hybrid only | See recency section below. | Semi-structured/unstructured search path only. |

## Query-shape matrix

| Query shape | Tensor | Lexical | Hybrid |
|---|---:|---:|---:|
| `q: "plain text"` | Yes | Yes | Yes |
| `q: {"text": weight, ...}` | Yes | No | No at top level; use `hybridParameters.queryTensor`. |
| `q.customVector` | Yes | No | Yes; `content` seeds lexical leg and `vector` seeds tensor leg. |
| `q: null` + `context.tensor` | Yes | No | Yes when retrieval/ranking needs tensor vectors. |
| `q: null` + `hybridParameters.queryTensor` / `queryLexical` | No | No | Yes, depending on retrieval/ranking method. |
| `context.documents` | Yes | No | Yes except lexical/lexical hybrid. |

## `hybridParameters`

| Field | Values / defaults | Compatibility rule |
|---|---|---|
| `retrievalMethod` | `disjunction` (default), `tensor`, `lexical` | `disjunction` means collect candidates from both tensor and lexical legs. |
| `rankingMethod` | `rrf` (default), `tensor`, `lexical` | If retrieval is `disjunction`, ranking must be `rrf`. If retrieval is `tensor` or `lexical`, ranking must be `tensor` or `lexical`. |
| `alpha` | Defaults to `0.5` for RRF; must be 0..1. | Only valid for `rankingMethod: rrf`. |
| `rrfK` | Defaults to `60`; integer >= 0. | Only valid for `rankingMethod: rrf`. |
| `searchableAttributesTensor` | List of tensor fields. | Only valid when retrieval is `tensor`/`disjunction` or ranking is `tensor`. |
| `searchableAttributesLexical` | List of lexical fields. | Only valid when retrieval is `lexical`/`disjunction` or ranking is `lexical`. |
| `scoreModifiersTensor` | `ScoreModifierLists`. | Only valid when ranking is `tensor` or `rrf`. |
| `scoreModifiersLexical` | `ScoreModifierLists`. | Only valid when ranking is `lexical` or `rrf`, or retrieval is lexical. |
| `queryTensor` | String or weighted dict. | Cannot be combined with top-level `q`. Do not provide when retrieval and ranking are both lexical. |
| `queryLexical` | String. | Cannot be combined with top-level `q`. Do not provide when retrieval and ranking are both tensor. |
| `rerankDepthTensor` | Integer, non-negative. | Overrides tensor target hits for hybrid tensor leg. |
| `rerankDepthLexical` | Integer >= 1. | Only valid when retrieval is `lexical` or `disjunction`. Required before `weakAndParameters`. |
| `weakAndParameters` | `stopwordLimit`, `adjustTarget`, `filterThreshold` in 0..1; `allowDropAll` bool. | Only valid when `rerankDepthLexical` is set. |
| `rerankCount` | Integer >= 1. | Overrides the number of candidates sent to hybrid phase-2 reranking. |
| `secondPhaseModifier` | Boolean. | `true` only when retrieval is `disjunction`, or retrieval and ranking are both lexical. Not compatible with collapse sort-by execution. |
| `lexicalOperand` | `or`, `and`, `weakAnd`. | Used by semi-structured/unstructured hybrid lexical term generation; not supported on structured indexes. |
| `verbose` | Boolean, default false. | Adds custom-searcher verbosity metadata when supported. |

## Tensor candidate controls

- If `efSearch` is absent, tensor candidate depth starts from `limit + offset`.
- If `efSearch` is present, Vespa receives additional exploration hits based on `efSearch - (limit + offset)` when positive.
- `rerankDepth` or `hybridParameters.rerankDepthTensor` can override tensor target hits, but `efSearch` still controls additional approximate-search exploration.
- `approximateThreshold` is valid only for approximate tensor/hybrid search and must be 0..1.
- `approximate: false` asks for exact behavior; if coverage is degraded or less than 100%, the search path treats that as an internal failure.

## Sort

`sortBy` is hybrid-only and uses global phase sorting.

```json
{
  "sortBy": {
    "fields": [
      {"fieldName": "price", "order": "asc", "missing": "last"}
    ],
    "sortDepth": 200,
    "minSortCandidates": 300
  }
}
```

Rules:

- `fields` must contain 1 to 3 fields. Later fields act as tie-breakers.
- `order` is `asc` or `desc`; default is `desc`.
- `missing` is `first` or `last`; default is `last`.
- If `minSortCandidates` is absent and no relevance cutoff is present, Marqo sets it to `max(3 * limit, offset + limit)`.
- If `minSortCandidates` is present, it is raised to at least `offset + limit`.
- `sortBy` cannot be used with root/global `scoreModifiers`.
- `sortBy` cannot be used with recency global-phase reranking; set `recencyParameters.applyInRankingPhase: exclude-global` if both are required.

## Collapse

`collapseFields` is a hybrid-only list with exactly one collapse model.

```json
{
  "collapseFields": [
    {
      "name": "variant_group",
      "sortBy": {
        "fields": [
          {"fieldName": "price", "order": "asc"}
        ],
        "disableIfMainSortByFields": ["price"],
        "alwaysFetchVariants": false
      }
    }
  ]
}
```

Rules:

- The collapse field must already be configured on the index.
- `collapse.sortBy.fields` contains exactly one field.
- Collapse sort-by runs a two-search flow: first collapsed relevance groups, then sorted variants inside those groups.
- Without `alwaysFetchVariants`, only hits with a numeric collapse sort field collect parent ids for the second search; booleans, strings, missing values, and `null` are not numeric.
- `disableIfMainSortByFields` disables collapse sort when the main query sort uses any listed field.
- Collapse sort-by is incompatible with second-phase lexical modifiers during the second collapse-sort pass.

## Facets and total hits

```json
{
  "facets": {
    "fields": {
      "brand": {"type": "string", "maxResults": 10},
      "tags": {"type": "array"},
      "price": {
        "type": "number",
        "ranges": [
          {"to": 50, "name": "budget"},
          {"from": 50, "to": 100, "name": "mid"},
          {"from": 100, "name": "premium"}
        ]
      }
    },
    "maxDepth": 3,
    "maxResults": 100,
    "order": "desc"
  },
  "trackTotalHits": true
}
```

Rules:

- Facets and `trackTotalHits` are hybrid-only and require the semi-structured/unstructured search path.
- Facet field `type` is `string`, `array`, or `number`.
- Numeric `ranges` are only valid for `number` facets; ranges must not overlap.
- `maxResults` must be 1..10000. `maxDepth` must be positive.
- `excludeTerms` requires a filter string, and every excluded term must appear in the filter.

## Recency

```json
{
  "recencyParameters": {
    "recencyField": "updated_at",
    "scale": "14d",
    "offset": "0d",
    "decayFunction": "exponential",
    "decayTo": 0.5,
    "applyInRankingPhase": "all",
    "applyToSubqueries": ["tensor", "lexical"]
  }
}
```

Rules:

- Hybrid-only and semi-structured/unstructured search path only.
- `scale` must be a positive duration such as `7d` or `12h`; `offset` must be non-negative.
- `decayFunction` is `exponential`, `linear`, `gaussian`, or `binary`.
- `decayTo` must be in `(0, 1]`.
- `applyInRankingPhase` is `all`, `only-global`, or `exclude-global`.
- `addToScoreWeight` switches from multiplicative to additive scoring and must be positive.
- `center` supplies a fixed Unix timestamp for reproducible recency scoring.
- `applyToSubqueries` can target `tensor`, `lexical`, both, or an empty list; it requires hybrid disjunction retrieval.
- `growFrom`, `growFunction`, `growScale`, and `growOffset` must be all provided together or all omitted.

## Relevance cutoff

```json
{
  "relevanceCutoff": {
    "method": "relative_max_score",
    "probeDepth": 1000,
    "parameters": {"relativeScoreFactor": 0.8},
    "affectFacets": true,
    "applyInRetrieval": "both"
  }
}
```

| Method | Required `parameters` | Notes |
|---|---|---|
| `relative_max_score` | `relativeScoreFactor` in 0..1 | Keeps candidates relative to max score. |
| `mean_std_dev` | `stdDevFactor` | Keeps candidates by mean/std thresholding. |
| `gap_detection` | None | Rejects non-null `parameters`. |

Rules:

- Hybrid-only and semi-structured/unstructured search path only.
- `probeDepth` must be >= 1.
- `affectFacets` makes facets/total hits count only documents passing cutoff.
- `applyInRetrieval` can be set only when `hybridParameters.retrievalMethod` is `disjunction`; `lexical` is not supported.
- Do not combine a specific `applyInRetrieval` leg with `overrideSortCandidatesWithRelevantCandidates` because the relevant-candidate pool would represent only one leg.

## Score modifier placement

| Placement | Use case | Constraint |
|---|---|---|
| Top-level `scoreModifiers` on tensor/lexical | Classic score modification by numeric fields. | At least one add/multiply list; field `_id` forbidden. |
| Top-level `scoreModifiers` on hybrid | Global RRF reranking modifiers. | Only valid when hybrid `rankingMethod` is `rrf`; conflicts with `sortBy`. |
| `hybridParameters.scoreModifiersTensor` | Modify tensor leg. | Requires tensor or RRF ranking. |
| `hybridParameters.scoreModifiersLexical` | Modify lexical leg. | Requires lexical/RRF ranking or lexical retrieval. |
| `marqo__score_*` custom score keys | Custom BM25/closeness rerank signals. | Semi-structured/unstructured path, supported schema, no geodegrees closeness. |

For filter syntax and score-modifier object shape, see `filter-and-modifier-reference.md`.
