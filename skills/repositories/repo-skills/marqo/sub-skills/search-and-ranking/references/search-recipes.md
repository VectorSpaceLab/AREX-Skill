# Search Recipes

This reference gives payload-oriented recipes for Marqo search and recommend work. It assumes the index already exists and has the required tensor, lexical, filter, facet, sort, and collapse fields. If a recipe needs index-field changes, route that part to `../index-and-vespa/`; if it needs HTTP route mechanics, route to `../documents-and-api/`; if it needs model/vectorisation internals, route to `../inference-and-models/`.

## Assembly order

1. Choose the search method: `TENSOR`, `LEXICAL`, or `HYBRID`.
2. Choose the `q` shape for that method: string, weighted dict, custom vector, or `null` with `context`.
3. Add result controls: `limit`, `offset`, `showHighlights`, `attributesToRetrieve`.
4. Add filter and searchable-attribute constraints.
5. Add ranking controls one at a time: score modifiers, hybrid RRF parameters, recency, sort, collapse, facets, relevance cutoff.
6. If a feature is rejected, remove it and re-add it using the compatibility tables in `ranking-parameters.md`.

## Intent selector

| User intent | Start with | Key fields | Watch out |
|---|---|---|---|
| Natural-language semantic search | Tensor search | `q`, `searchMethod: TENSOR`, `searchableAttributes`, `context` | Tensor search needs vectorisation/model service. |
| Exact keyword/BM25 search | Lexical search | `q` string, `searchMethod: LEXICAL`, `language`, `filter` | `q` must be a string; no `efSearch` or `approximate`. |
| Blend semantic and keyword relevance | Hybrid RRF | `searchMethod: HYBRID`, `hybridParameters.retrievalMethod: disjunction`, `rankingMethod: rrf` | Top-level `searchableAttributes` must move into hybrid sub-fields. |
| Separate tensor and lexical text | Hybrid with split queries | `hybridParameters.queryTensor`, `queryLexical` and `q: null` | Do not provide both `q` and split query fields. |
| Search with weighted text + image inputs | Tensor or hybrid multimodal | `q` as a weighted dict; optional `context.tensor` | Requires an index/model that can vectorise those modalities. |
| Use a precomputed query vector | Tensor or hybrid custom vector | `q.customVector.vector`, optional `content` | Custom vectors are not accepted by lexical search. |
| Recommend similar documents | Recommend / context flow | `documents`, `tensorFields`, interpolation, then `context.tensor` | Duplicate ids, missing embeddings, or all-zero weights fail. |
| Variant de-duplication | Hybrid + collapse | `collapseFields` with exactly one field | The collapse field must already be configured on the index. |

## Tensor search recipe

Use tensor search when the query should be embedded and compared against tensor fields. A string query uses the model to produce a vector. A weighted dict allows multi-term semantic composition, including negative weights.

```json
{
  "q": "red waterproof hiking backpack",
  "searchMethod": "TENSOR",
  "limit": 10,
  "offset": 0,
  "searchableAttributes": ["title", "description", "image"],
  "filter": "category:backpack AND price:[0 TO 100] AND inStock:true",
  "attributesToRetrieve": ["_id", "title", "price", "image", "rating"],
  "showHighlights": true,
  "scoreModifiers": {
    "add_to_score": [
      {"field_name": "rating", "weight": 0.05}
    ]
  }
}
```

Weighted tensor query:

```json
{
  "q": {
    "red backpack": 1.0,
    "waterproof": 0.7,
    "child backpack": -0.4
  },
  "searchMethod": "TENSOR",
  "limit": 10,
  "filter": "category:backpack"
}
```

## Lexical search recipe

Use lexical search when exact tokens and BM25-like relevance matter. Keep `q` a string. Add filters for structured constraints instead of putting all constraints in the keyword query.

```json
{
  "q": "red waterproof backpack",
  "searchMethod": "LEXICAL",
  "limit": 10,
  "offset": 0,
  "searchableAttributes": ["title", "description"],
  "language": "en",
  "filter": "category:backpack AND price:[0 TO 100]",
  "attributesToRetrieve": ["_id", "title", "price", "brand"],
  "showHighlights": true
}
```

## Hybrid RRF recipe

Use hybrid search when you need both semantic recall and lexical precision. The default hybrid parameters are disjunction retrieval, RRF ranking, `alpha: 0.5`, and `rrfK: 60`; make them explicit when debugging or comparing runs.

```json
{
  "q": "red waterproof hiking backpack",
  "searchMethod": "HYBRID",
  "limit": 10,
  "offset": 0,
  "filter": "category:backpack AND price:[0 TO 100] AND inStock:true",
  "attributesToRetrieve": ["_id", "title", "price", "brand", "rating"],
  "showHighlights": true,
  "hybridParameters": {
    "retrievalMethod": "disjunction",
    "rankingMethod": "rrf",
    "alpha": 0.6,
    "rrfK": 60,
    "searchableAttributesTensor": ["title", "description", "image"],
    "searchableAttributesLexical": ["title", "description"],
    "rerankDepthTensor": 50,
    "rerankDepthLexical": 50,
    "weakAndParameters": {
      "stopwordLimit": 0.6,
      "adjustTarget": 0.2,
      "allowDropAll": false
    }
  },
  "facets": {
    "fields": {
      "brand": {"type": "string", "maxResults": 10},
      "price": {
        "type": "number",
        "ranges": [
          {"to": 50, "name": "budget"},
          {"from": 50, "to": 100, "name": "mid"},
          {"from": 100, "name": "premium"}
        ]
      }
    },
    "maxResults": 10,
    "order": "desc"
  },
  "trackTotalHits": true
}
```

## Split tensor and lexical query recipe

When tensor and lexical intent differ, omit top-level `q` and use split query fields.

```json
{
  "q": null,
  "searchMethod": "HYBRID",
  "limit": 10,
  "hybridParameters": {
    "retrievalMethod": "disjunction",
    "rankingMethod": "rrf",
    "queryTensor": {
      "red hiking backpack": 1.0,
      "rain cover": 0.5
    },
    "queryLexical": "waterproof backpack",
    "searchableAttributesTensor": ["title", "description", "image"],
    "searchableAttributesLexical": ["title", "description"],
    "alpha": 0.65
  },
  "filter": "category:backpack"
}
```

## Multimodal and custom-vector recipes

These recipes assume the index/model can handle the modalities. For an image-enabled index, a weighted dict can blend text and image pointers.

```json
{
  "q": {
    "red hiking backpack": 1.0,
    "https://example.invalid/images/red-backpack.jpg": 0.8
  },
  "searchMethod": "TENSOR",
  "limit": 10,
  "mediaDownloadHeaders": {
    "User-Agent": "marqo-search-example"
  },
  "filter": "category:backpack"
}
```

Use a custom vector when a caller already has an embedding. In hybrid search, `customVector.content` can supply the lexical leg while `customVector.vector` supplies the tensor leg.

```json
{
  "q": {
    "customVector": {
      "content": "red hiking backpack",
      "vector": [0.11, -0.07, 0.32, 0.18]
    }
  },
  "searchMethod": "HYBRID",
  "limit": 5,
  "hybridParameters": {
    "retrievalMethod": "disjunction",
    "rankingMethod": "rrf",
    "alpha": 0.5
  }
}
```

## Recommendation recipe

Recommendation gathers vectors from input documents, interpolates them, then runs a tensor search with `context.tensor`. Duplicate ids, all-zero document weights, missing documents, or documents with no embeddings can fail before search.

Conceptual recommend request:

```json
{
  "documents": {
    "doc-red-backpack": 1.0,
    "doc-hiking-pack": 0.5,
    "doc-child-pack": -0.2
  },
  "tensorFields": ["title", "image"],
  "interpolationMethod": "slerp",
  "excludeInputDocuments": true,
  "filter": "category:backpack",
  "limit": 10,
  "attributesToRetrieve": ["_id", "title", "price"]
}
```

Equivalent search shape after interpolation:

```json
{
  "q": null,
  "searchMethod": "TENSOR",
  "limit": 10,
  "context": {
    "tensor": [
      {"vector": [0.12, 0.33, -0.21, 0.44], "weight": 1.0}
    ]
  },
  "filter": "(category:backpack) AND NOT (_id:(doc-red-backpack) OR _id:(doc-hiking-pack) OR _id:(doc-child-pack))",
  "attributesToRetrieve": ["_id", "title", "price"]
}
```

For structured-index recommendation exclusion, the equivalent id filter is `NOT _id IN (...)`; for semi-structured/unstructured search paths, use the negated OR form shown above.

## Ecommerce conversion case

Natural request: “Find red waterproof backpacks under $100, prefer recent popular listings, and de-duplicate variants.”

Tensor-first payload:

```json
{
  "q": "red waterproof hiking backpack",
  "searchMethod": "TENSOR",
  "limit": 10,
  "filter": "category:backpack AND price:[0 TO 100]",
  "scoreModifiers": {
    "add_to_score": [
      {"field_name": "popularity", "weight": 0.02}
    ]
  }
}
```

Lexical-first payload:

```json
{
  "q": "red waterproof backpack",
  "searchMethod": "LEXICAL",
  "limit": 10,
  "searchableAttributes": ["title", "description"],
  "filter": "category:backpack AND price:[0 TO 100]"
}
```

Hybrid payload with recency and collapse:

```json
{
  "q": "red waterproof hiking backpack",
  "searchMethod": "HYBRID",
  "limit": 10,
  "filter": "category:backpack AND price:[0 TO 100]",
  "hybridParameters": {
    "retrievalMethod": "disjunction",
    "rankingMethod": "rrf",
    "alpha": 0.6,
    "rrfK": 60,
    "searchableAttributesTensor": ["title", "description", "image"],
    "searchableAttributesLexical": ["title", "description"]
  },
  "recencyParameters": {
    "recencyField": "updated_at",
    "scale": "14d",
    "decayFunction": "exponential",
    "decayTo": 0.5,
    "applyInRankingPhase": "all"
  },
  "collapseFields": [
    {
      "name": "variant_group",
      "sortBy": {
        "fields": [
          {"fieldName": "popularity", "order": "desc"}
        ]
      }
    }
  ]
}
```

## Recovery case patterns

- If a filter uses `category IN (...)`, rewrite it as `category:(...) OR category:(...)` unless the field is `_id`.
- If lexical search carries `efSearch`, `approximate`, or a dict `q`, remove those fields or switch to tensor/hybrid.
- If hybrid search carries top-level `searchableAttributes`, move them into `hybridParameters.searchableAttributesTensor` and/or `searchableAttributesLexical`.
- If `sortBy` conflicts with `recencyParameters`, either remove one or set `recencyParameters.applyInRankingPhase` to `exclude-global`.

## Bundled payload printer

Run the safe offline helper to print stable examples:

```bash
python scripts/search_payload_examples.py
python scripts/search_payload_examples.py --case ecommerce --case recover-params
```
