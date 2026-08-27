# Index models and schema settings

This reference distills Marqo's index model layer for future agents. It intentionally describes the behavior rather than linking to source files or tests.

## Class and model map

| Layer | Main classes | Use for |
|---|---|---|
| API settings model | `IndexSettings`, `AnnParameters` | Validate user-facing create/update settings and convert them to core requests. Keep public payload examples in `documents-and-api`; use this section for internal semantics. |
| Core request models | `MarqoIndexRequest`, `StructuredMarqoIndexRequest`, `UnstructuredMarqoIndexRequest`, `FieldRequest` | Validated index-create requests consumed by Vespa schema factories. |
| Stored core models | `MarqoIndex`, `StructuredMarqoIndex`, `UnstructuredMarqoIndex`, `SemiStructuredMarqoIndex`, `Field`, `TensorField`, `StringArrayField`, `CollapseField`, `Model` | Persisted index settings and derived helper maps used by add/search/update paths. |
| Vespa implementations | `StructuredVespaIndex`, `SemiStructuredVespaIndex`, `UnstructuredVespaIndex`, `VespaIndex` | Convert Marqo documents and queries to/from Vespa. |
| Schema implementations | `StructuredVespaSchema`, `SemiStructuredVespaSchema`, `UnstructuredVespaSchema`, `VespaSchema` | Generate Vespa `.sd` schema text and the corresponding stored Marqo index object. |
| Deployment layer | `IndexManagement`, `VespaApplicationPackage`, `VespaClient`, `ZookeeperClient` | Bootstrap, create/delete indexes, update schema/settings, rollback, and coordinate deployment locks. |

`MarqoIndex.parse_obj()` dispatches by stored `type`: `structured` → `StructuredMarqoIndex`, `unstructured` → `UnstructuredMarqoIndex`, and `semi-structured` → `SemiStructuredMarqoIndex`.

## Index type choice

| Type label | What it means in this codebase | Choose when | Avoid/notes |
|---|---|---|---|
| `semi-structured` | Future-facing internal schema that grows lexical/tensor/string-array fields as data arrives, while keeping fixed maps for numeric, bool, short string, type metadata, vector count, and score modifiers. | Default for new flexible indexes, fields discovered from documents, partial updates, collapse fields, language/stemming on mapped text fields, recency/schema-template features, or custom-score rerankers. | Direct future changes here. It inherits/duplicates some structured behavior, but the project direction is to modify semi-structured directly. |
| `structured` | Explicit schema with `allFields` and `tensorFields`. Vespa fields are generated up front and field features must be declared. | Tasks requiring strict field declarations or exact field-feature validation. | Deprecated relative to semi-structured for new internal work. Some newer schema-template and custom-score features are semi-structured only. |
| `unstructured` | Public/legacy compatibility label. For Marqo versions at or after the semi-structured cutover, an `UnstructuredMarqoIndexRequest` generates a `SemiStructuredVespaSchema`. Legacy unstructured schema remains only for old indexes. | Maintaining old stored indexes or understanding why public settings still use the word unstructured. | Do not add new flexible-index behavior to legacy `UnstructuredVespaSchema` unless the task is explicitly legacy recovery. |

Routing factory behavior:

- `StructuredMarqoIndexRequest` always uses `StructuredVespaSchema`.
- `UnstructuredMarqoIndexRequest` with an old Marqo version below the semi-structured cutover uses `UnstructuredVespaSchema`.
- `UnstructuredMarqoIndexRequest` for current versions uses `SemiStructuredVespaSchema` and returns a `SemiStructuredMarqoIndex`.

## Default index settings

`IndexSettings` defaults observed from live package/source inspection:

| Setting | Default / behavior |
|---|---|
| `type` | `semi-structured` by default. |
| `model` | `hf/e5-base-v2` by default. Model properties are populated from the registry unless explicit `modelProperties` marks it custom. |
| `normalizeEmbeddings` | `true`. |
| `textPreprocessing` | Split by sentence, split length `2`, overlap `0`. |
| `imagePreprocessing` | `patchMethod=None`. |
| `videoPreprocessing` | Split length `20`, overlap `3`. |
| `audioPreprocessing` | Split length `10`, overlap `3`. |
| `vectorNumericType` | `float` by default; `bfloat16` exists as an enum and is reflected by the semi-structured schema template. |
| `annParameters.spaceType` | `prenormalized-angular` by default. Other enum values are `euclidean`, `angular`, `dotproduct`, `geodegrees`, and `hamming`. |
| `annParameters.parameters` | HNSW `efConstruction=512`, `m=16`. Both must be positive. |
| `filterStringMaxLength` | For unstructured/semi-structured settings, defaults to `50` when omitted. |
| URL/pointer treatment | `treatUrlsAndPointersAsMedia=true` forces `treatUrlsAndPointersAsImages=true`; `treatUrlsAndPointersAsImages=false` with media enabled is invalid. The images flag is deprecated in favor of media. |
| `collapseFields` | Only valid on unstructured/semi-structured settings; structured settings reject it. One collapse field is supported. |

Public setting keys are camelCase. Snake_case keys in the create-index settings object are rejected before deeper validation, except the internal aliases intentionally used by nested models.

## Name validation

Validate names before debugging schema/query failures.

| Name kind | Rule |
|---|---|
| Index name | Must match `[a-zA-Z_-][a-zA-Z0-9_-]*` and must not start with the reserved `marqo__` prefix. Hyphen and underscore are allowed in Marqo index names. |
| Vespa schema name | Generated from index name. `_` is encoded as `_00`, `-` as `_01`, and encoded names receive the reserved prefix so Vespa sees a schema name matching `[a-zA-Z_][a-zA-Z0-9_]*`. |
| Field name | Must match `[a-zA-Z_][a-zA-Z0-9_]*`, must not start with `marqo__`, and must not be `_id`, `_tensor_facets`, `_highlights`, `_score`, or `_found`. |
| Legacy unstructured field name | Uses the common field rule and also rejects the reserved substring `::`. |
| Collapse field name | Uses normal field-name validation. `minGroups` must be greater than zero. |

## Field type catalog

Live enum values:

| Group | Field types |
|---|---|
| Text and scalar | `text`, `bool`, `int`, `long`, `float`, `double` |
| Arrays | `array<text>`, `array<int>`, `array<long>`, `array<float>`, `array<double>` |
| Media pointers | `image_pointer`, `video_pointer`, `audio_pointer` |
| Vector/multimodal | `multimodal_combination`, `custom_vector` |
| Numeric maps | `map<text, int>`, `map<text, long>`, `map<text, float>`, `map<text, double>` |

`FieldRequest` normalizes extra whitespace around generic type strings, so inputs such as `map < text , float >` normalize to `map<text, float>` before enum validation.

## Field feature compatibility

| Feature | Valid field types | Required/derived fields | Invalid combinations |
|---|---|---|---|
| `lexical_search` | `text`, `array<text>`, `custom_vector` | Stored `Field` requires a `lexical_field_name`; generated structured/semi-structured schemas prefix lexical fields with `marqo__lexical_`. | Bool/numeric arrays/numeric scalars/media pointer/multimodal fields are invalid for lexical search. |
| `filter` | Most non-image/non-multimodal fields, including text, bool, numeric scalars, numeric arrays, numeric maps, custom vector, video pointer, and audio pointer. | Stored `Field` requires a `filter_field_name` when the filter feature is present. Structured schemas prefix filter fields with `marqo__filter_`. Semi-structured stores many filterable dynamic fields in typed maps or string-array fields. | `image_pointer` and `multimodal_combination` cannot carry any feature. |
| `score_modifier` | `int`, `long`, `float`, `double`, and numeric map variants. | Values feed score-modifier tensors/maps. | Text, bool, arrays, media pointer, custom vector, and multimodal fields are invalid for score modifiers. |
| `language` | Only meaningful on fields with `lexical_search`. | Semi-structured text mappings add `set_language` in the schema when supported by the index version. | Setting language without lexical search is invalid; old semi-structured indexes may reject language because the feature is version-gated. |
| `stemming` | Only meaningful on fields with `lexical_search`; enum values are `none`, `best`, `shortest`, `multiple`. | Semi-structured lexical fields can emit `stemming: <value>` in schema templates when supported. | Setting stemming without lexical search is invalid; old indexes may reject stemming because the feature is version-gated. |

Additional validation rules:

- `image_pointer` and `multimodal_combination` reject all features.
- `multimodal_combination` must define `dependentFields`; all other field types must not define `dependentFields`.
- In structured requests, every `tensorFields` entry must be present in `allFields`.
- In structured requests, every `multimodal_combination` and `custom_vector` field must also be a tensor field.
- A `custom_vector` field cannot be a dependent field of a `multimodal_combination` field.
- A stored `StructuredMarqoIndex` also validates that every stored `TensorField.name` exists in the field map.

## Collapse fields

Collapse fields are semi-structured/unstructured settings, not structured settings.

Rules to remember:

- Request settings reject an empty collapse-field list and reject more than one collapse field.
- Stored semi-structured indexes also require exactly one collapse field when the field list is present.
- The field name uses normal field-name validation and `minGroups` must be positive.
- During add-documents handling, every document for an index with a collapse field must include that field as a non-empty string. Missing, non-string, or blank collapse values become add-document errors.
- Query-time collapse/ranking payload choices belong to `search-and-ranking`; this sub-skill owns the schema/index prerequisite and failure diagnosis.

## Semi-structured dynamic field handling

Semi-structured indexes start with empty `lexical_fields`, `tensor_fields`, and `string_array_fields` and grow the stored index plus schema as documents are ingested.

| Incoming document content | Semi-structured storage effect |
|---|---|
| String field | Must map to a known lexical field unless ingestion is in the field-discovery path. Discovered text fields become `Field(type=text, features=[lexical_search], lexical_field_name=marqo__lexical_<name>)`. Short strings are also stored in `marqo__short_string_fields` up to `filterStringMaxLength`. |
| Bool field | Stored in `marqo__bool_fields`; partial-update-capable indexes also record the field type. |
| Integer field | Stored in `marqo__int_fields`, added to score modifiers, and recorded in field-type metadata when supported. |
| Float field | Stored in `marqo__float_fields`, added to score modifiers, and recorded in field-type metadata when supported. |
| Dict of numeric values | Flattened as `field.key` into numeric maps and score modifiers; field-type metadata distinguishes int-map and float-map cases when supported. |
| List of strings | For partial-update-capable indexes, creates one schema field `marqo__string_array_<name>` and stores an array. Older schema templates combine values into a single legacy string-array field. |
| Tensorized content | Each discovered tensor field adds chunks field `marqo__chunks_<name>` and embeddings field `marqo__embeddings_<name>`, then records vector count. |
| Collapse field | Stored as a direct string attribute/summary field, not as an auto lexical field. |

Field-count limits for semi-structured auto-discovery are read from environment variables for maximum lexical field count, tensor field count, and string-array field count. Hitting the limit produces a `TooManyFieldsError` with the corresponding limit name.

## Version-gated index capabilities

Several capabilities are evaluated from `marqo_version` or `schema_template_version`. If `schema_template_version` is absent, semi-structured indexes fall back to `marqo_version` for backward compatibility.

| Capability | Minimum observed version |
|---|---:|
| Semi-structured replacement for new flexible indexes | `2.13.0` |
| Language mappings on text fields | `2.16.0` |
| Stemming mappings on text fields | `2.16.0` |
| Partial updates and separate string-array fields | `2.16.0` |
| Sort-by / relevance-cutoff index support | `2.22.0` |
| Collapse fields and typeahead schemas | `2.23.0` |
| Apply latest schema template | `2.23.0` |
| Collapse minimal summary | `2.24.6` |
| Recency scoring | `2.24.8` |
| Recency additive/grow | `2.24.9` |
| Second-phase lexical score modifiers | `2.24.11` |
| Collapse sort-by | `2.24.13` |
| Recency center and subquery application | `2.25.1` |
| Custom score rerankers | `2.26.0` |

When a feature fails on an older index, do not assume a request-payload bug. Check stored `marqo_version`, `schema_template_version`, and whether `apply_latest_schema_template` is allowed for that index type and age.

## Model properties in index settings

`Model` holds `name`, optional `properties`, `custom`, `text_query_prefix`, and `text_chunk_prefix`.

Important behavior:

- If `properties` is absent, Marqo tries to populate model properties from the registry when dimension/properties are needed.
- Custom model properties are validated when `custom=true` and properties are provided.
- Non-custom models omit `properties` from serialized settings to avoid persisting registry defaults unnecessarily.
- `get_dimension()` requires a `dimensions` key after registry/custom-property resolution.
- Updating index settings currently allows only `modelProperties`. The update validator requires `dimensions` and `type` to remain unchanged and requires the updated object to include all keys from the current model properties.
- Public request examples and backend/model registry choices belong to `inference-and-models`; this sub-skill only diagnoses model-property compatibility where it blocks index schema/settings.
