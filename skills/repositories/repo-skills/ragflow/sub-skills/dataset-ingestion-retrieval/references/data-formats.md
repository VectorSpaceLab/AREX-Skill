# Data Formats

## Public-to-Internal Field Aliases

RAGFlow REST APIs expose friendly field names that map to internal database/index names.

| Public field | Internal field | Notes |
| --- | --- | --- |
| `chunk_method` | `parser_id` | Dataset/document parser method. |
| `embedding_model` | `embd_id` | Public model id string such as `<model>@<provider>`. |
| `dataset_id` | `kb_id` | Public API name vs internal knowledge base id. |
| `document_id` | `doc_id` | Public API name vs internal document id. |
| `chunk_count` | `chunk_num` | Document row counter. |
| `token_count` | `token_num` | Document row counter. |
| `content` | `content_with_weight` | Public chunk content vs indexed text field. |
| `important_keywords` | `important_kwd` | Manual or generated chunk keywords. |
| `questions` | `question_kwd` | Manual or generated chunk question prompts. |
| `document_keyword` | `docnm_kwd` | Indexed document name/title field. |
| `image_id` | `img_id` | Stored image reference for image/table chunks. |
| `available` | `available_int` | Public boolean vs indexed integer flag. |
| `positions` | `position_int` | Page/coordinate metadata. |

Keep these aliases stable. Many tests assert public response field names even when internal fields differ.

## Chunk Methods

Dataset create/update validates the common public chunk methods:

- `naive`
- `book`
- `email`
- `laws`
- `manual`
- `one`
- `paper`
- `picture`
- `presentation`
- `qa`
- `table`
- `tag`
- `resume`

Document update additionally accepts `knowledge_graph`. Older internal code may also use `general` as an alias for the naive parser factory path.

When adding or renaming a method, update dataset validation, document validation, parser defaults, task executor parser selection, frontend forms, SDK/docs, and tests together.

## Parser Config Shape

`parser_config` is a JSON object. It is intentionally extensible, but these keys are common and should be preserved where applicable:

| Key | Type | Used for |
| --- | --- | --- |
| `layout_recognize` | string | PDF/document parser selection such as DeepDOC or plain text mode. |
| `chunk_token_num` | integer | Built-in token chunk size. |
| `delimiter` | string | Text delimiter for naive chunking. |
| `auto_keywords` | integer | Number of generated keywords per chunk. |
| `auto_questions` | integer | Number of generated questions per chunk. |
| `html4excel` | boolean | Spreadsheet-to-HTML behavior for general chunking. |
| `filename_embd_weight` | number | Weight of filename/title vector in chunk embeddings. |
| `topn_tags` | integer | Number of tags selected during auto-tagging. |
| `tag_kb_ids` | list[string] | Tag set dataset ids used for auto-tagging. |
| `task_page_size` | integer/null | Page batching for parsing tasks. |
| `pages` | list[list[int]]/null | Page ranges, commonly one-indexed in config. |
| `table_context_size` | number | Context window around table chunks. |
| `image_context_size` | number | Context window around image chunks. |
| `parent_child` | object | Public parent-child chunking settings. |
| `children_delimiter` | string | Flattened execution field for child chunk splitting. |
| `enable_children` | boolean | Flattened execution flag for child chunks. |
| `toc_extraction` | boolean | Enables TOC extraction for naive parser. |
| `enable_metadata` | boolean | Enables auto-metadata extraction. |
| `metadata` | list/object | Auto-metadata schema/rules. |
| `built_in_metadata` | list | Built-in metadata rules merged with custom rules. |
| `llm_id` | string | Chat/indexing model id for metadata, GraphRAG, RAPTOR, TOC, keywords/questions. |
| `raptor` | object | RAPTOR configuration. |
| `graphrag` | object | GraphRAG configuration. |
| `ext` | object | Extra fields flattened into parser_config by update handlers. |

### Parent-Child Config

Public shape:

```json
{
  "parent_child": {
    "use_parent_child": true,
    "children_delimiter": "\n"
  }
}
```

Execution shape after dataset update:

```json
{
  "children_delimiter": "\n",
  "enable_children": true
}
```

If parent-child is disabled, execution fields are usually flattened to empty delimiter and `false`.

### RAPTOR Config

Common keys:

```json
{
  "raptor": {
    "use_raptor": true,
    "prompt": "Please summarize... {cluster_content}",
    "max_token": 256,
    "threshold": 0.1,
    "max_cluster": 64,
    "random_seed": 0,
    "scope": "file",
    "clustering_method": "gmm",
    "tree_builder": "raptor",
    "ext": {
      "psi_exact_max_leaves": 4096,
      "psi_bucket_size": 1024
    }
  }
}
```

`scope` is commonly `file` or dataset-level. `tree_builder`/`clustering_method` affect cleanup and duplicate summary detection.

### GraphRAG Config

Common keys:

```json
{
  "graphrag": {
    "use_graphrag": true,
    "entity_types": ["organization", "person", "geo", "event", "category"],
    "method": "light",
    "resolution": false,
    "community": false,
    "batch_chunk_token_size": 4096,
    "retry_attempts": 2,
    "retry_backoff_seconds": 2.0,
    "retry_backoff_max_seconds": 60.0,
    "build_subgraph_timeout_per_chunk_seconds": 300,
    "build_subgraph_min_timeout_seconds": 600,
    "merge_timeout_seconds": 180,
    "resolution_timeout_seconds": 1800,
    "community_timeout_seconds": 1800,
    "lock_acquire_timeout_seconds": 600
  }
}
```

Supported extractor methods are `light`, `general`, and `ner`. Use domain-specific `entity_types`; the default list is only a starting point.

## Dataset Request Shapes

Create dataset:

```json
{
  "name": "contracts",
  "permission": "me",
  "embedding_model": "model@provider",
  "chunk_method": "naive",
  "parser_config": {
    "chunk_token_num": 512,
    "delimiter": "\n"
  }
}
```

Update dataset:

```json
{
  "chunk_method": "naive",
  "pagerank": 10,
  "parser_config": {
    "auto_keywords": 3,
    "parent_child": {
      "use_parent_child": true,
      "children_delimiter": "\n\n"
    }
  }
}
```

Dataset update deep-merges config with the existing dataset config. If a new `chunk_method` is supplied with no config, defaults for that method are generated.

## Document Request Shapes

Update document parser config:

```json
{
  "parser_config": {
    "auto_questions": 2,
    "ext": {
      "filename_embd_weight": 0.3
    }
  }
}
```

Change document chunk method:

```json
{
  "chunk_method": "manual"
}
```

Parse documents:

```json
{
  "document_ids": ["document-id"]
}
```

Stop parsing:

```json
{
  "document_ids": ["document-id"]
}
```

Document update validates file-type compatibility for some parser choices, such as visual files requiring `picture` and presentations requiring `presentation`.

## Retrieval Request Shapes

Compatibility retrieval:

```json
{
  "dataset_ids": ["dataset-id"],
  "question": "what changed in the contract?",
  "document_ids": [],
  "page": 1,
  "page_size": 30,
  "top_k": 1024,
  "similarity_threshold": 0.2,
  "vector_similarity_weight": 0.3,
  "use_kg": false,
  "toc_enhance": false,
  "highlight": true,
  "keyword": false,
  "cross_languages": [],
  "metadata_condition": {
    "logic": "and",
    "conditions": [
      {"name": "author", "comparison_operator": "=", "value": "qa"}
    ]
  }
}
```

Dataset search uses a similar shape but may use `size` instead of `page_size`, `doc_ids` instead of `document_ids`, and `meta_data_filter` for the wrapper filter format.

## Chunk Request Shapes

Add chunk:

```json
{
  "content": "manually curated answer text",
  "important_keywords": ["contract", "liability"],
  "questions": ["What is the liability clause?"],
  "tag_kwd": ["legal"],
  "tag_feas": {"legal": 1.0}
}
```

Update chunk:

```json
{
  "content": "updated content",
  "important_keywords": ["updated"],
  "questions": ["What was updated?"],
  "available": true,
  "positions": [[1, 0, 0, 100, 100]]
}
```

Delete chunks:

```json
{
  "chunk_ids": ["chunk-id"]
}
```

Delete all chunks for a document:

```json
{
  "chunk_ids": null,
  "delete_all": true
}
```

## Indexed Chunk Fields

Common document-engine fields:

| Field | Meaning |
| --- | --- |
| `id` / row id | Chunk id. |
| `content_with_weight` | Main chunk text used for retrieval and answer context. |
| `content_ltks`, `content_sm_ltks` | Tokenized content fields. |
| `title_tks`, `title_sm_tks` | Tokenized document title fields. |
| `q_{dimension}_vec` | Embedding vector field; dimension must match the embedding model. |
| `doc_id` | Source document id. |
| `kb_id` | Dataset id. |
| `docnm_kwd` | Document name keyword. |
| `chunk_order_int` | Chunk ordering within document. |
| `page_num_int`, `top_int`, `position_int` | Page and layout positions. |
| `available_int` | Enabled/disabled flag. |
| `important_kwd`, `important_tks` | Keywords and tokens. |
| `question_kwd`, `question_tks` | Questions and tokens. |
| `tag_kwd`, `tag_feas` | Tags and rank-feature scores. |
| `pagerank_flt` or pagerank field | Dataset ranking boost field. |
| `doc_type_kwd` | Text/table/image/other chunk type. |
| `img_id` | Stored image id for image/table chunks. |
| `mom`, `mom_id` | Parent-child context fields. |
| `toc_kwd` | TOC synthetic chunk marker. |
| `raptor_kwd`, `raptor_layer_int`, `extra` | RAPTOR summary fields. |
| `knowledge_graph_kwd` | GraphRAG row type such as entity, relation, community report. |
| `entity_kwd`, `entity_type_kwd` | Graph entity fields. |
| `from_entity_kwd`, `to_entity_kwd` | Graph relation endpoints. |
| `rank_flt`, `weight_int`, `weight_flt`, `n_hop_with_weight` | Graph scoring and neighborhood fields. |

Strip vector/token runtime fields from public responses unless implementing an internal debug endpoint.

## Metadata Condition Shape

A metadata condition is an object with `logic` and `conditions`:

```json
{
  "logic": "and",
  "conditions": [
    {"name": "status", "comparison_operator": "=", "value": "published"},
    {"name": "priority", "comparison_operator": "contains", "value": "urgent"}
  ]
}
```

Common operators include equality/inequality, relational comparisons, and contains/not-contains variants. Conditions are applied to document metadata to produce a document id set before chunk search.

## Safe Parser Config Inspection

Use `scripts/inspect_parser_config.py` to check a config file without importing RAGFlow or touching services. It validates JSON shape, known keys, chunk method compatibility, nested RAPTOR/GraphRAG values, parent-child flattening risks, metadata filter shape, and file-extension hints.
