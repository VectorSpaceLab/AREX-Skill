# Index and Vespa troubleshooting

Use this reference when an index-create/update/schema/query/local-Vespa task fails. Start with validation errors before blaming Vespa.

## Triage order

1. Identify the index type path: structured, current semi-structured, or legacy unstructured.
2. Validate index name, field names, field types, features, tensor fields, collapse fields, model properties, and version-gated settings.
3. If the error appears during document ingestion, check whether semi-structured dynamic field discovery attempted a schema update.
4. If the error appears during search, confirm the stored index has the lexical/tensor/string-array/collapse fields that the generated Vespa query references. Use `search-and-ranking` for payload semantics.
5. If the error appears during deployment, inspect Vespa config/document/query URL routing, app-package convergence, configChangeActions, Zookeeper lock status, and custom-searcher jar deployment.
6. If local services are involved, use the bundled inspector first, then route service/test command choice to `local-development`.

## Invalid index names

Symptoms:

- Validation error before schema generation.
- Vespa schema name contains unexpected `marqo__` prefix or encoded `_00` / `_01` segments.

Checks:

- Index name must match `[a-zA-Z_-][a-zA-Z0-9_-]*`.
- Index name must not start with `marqo__`.
- Vespa schema names encode `_` and `-`; this is normal and not a bug.

Recovery:

- Rename the index in the public/API layer before create.
- Do not manually edit generated schema names; Marqo uses a reversible encoding to map index names to Vespa-safe schema names.

## Invalid field names

Symptoms:

- Validation error mentioning Vespa name pattern, reserved prefix, or protected names.
- Legacy unstructured document errors mentioning reserved substring `::`.

Checks:

- Field names must match `[a-zA-Z_][a-zA-Z0-9_]*`.
- Field names must not start with `marqo__`.
- Field names cannot be `_id`, `_tensor_facets`, `_highlights`, `_score`, or `_found`.
- Legacy unstructured field names additionally cannot contain `::`.
- Collapse field names use the same rules.

Recovery:

- Rename the field before index creation or document ingestion.
- For semi-structured dynamic fields, fix the document/mapping field name; do not try to add an invalid field to the schema manually.

## Invalid field types or features

Symptoms:

- Validation error on `FieldRequest` or `Field`.
- Structured request rejects `tensorFields`, `dependentFields`, or feature combinations.
- Add-documents fails because dynamic field content does not match a supported semi-structured storage type.

Checks:

- `lexical_search` only works with `text`, `array<text>`, and `custom_vector` fields.
- `score_modifier` only works with integer/long/float/double scalar types and numeric map types.
- `filter` works for most non-image/non-multimodal types, but `image_pointer` and `multimodal_combination` cannot carry any feature.
- `multimodal_combination` requires `dependentFields`; no other field type may define it.
- Structured `tensorFields` entries must all exist in `allFields`.
- Structured `custom_vector` and `multimodal_combination` fields must also be tensor fields.
- A `custom_vector` field cannot be a dependent field of a multimodal field.
- Semi-structured documents support strings, bools, ints/floats, numeric dicts, lists of strings, tensorized fields, and configured collapse strings. Other content types fail conversion.

Recovery:

- Move public request-shape examples to `documents-and-api`; keep the core fix here: change the field type, remove the incompatible feature, add the missing tensor field, or split incompatible data into valid fields.
- For dynamic semi-structured fields that hit a max-field-count error, either raise the relevant maximum field-count environment variable intentionally or reduce field cardinality.

## Invalid collapse settings or documents

Symptoms:

- Create-index validation says collapse fields are empty, multiple, or unsupported.
- Add-documents fails because a required grouping field is missing or has the wrong type.
- Search collapse behaves as if grouping values are unavailable.

Checks:

- Collapse fields are semi-structured/unstructured only; structured settings reject them.
- Exactly one collapse field is supported when provided.
- `minGroups` must be positive.
- Every document must include the collapse field as a non-empty string.
- Semi-structured schema renders the collapse field as a direct string attribute/summary field, separate from auto lexical fields.

Recovery:

- Put collapse-field configuration in the index settings, not in ordinary ranking payloads.
- Repair documents so the collapse field is present and a non-empty string.
- If the index is too old for the desired collapse query behavior, check schema-template version and apply-template eligibility.

## Unsupported distance metrics or vector numeric types

Symptoms:

- Schema generation error for unknown distance metric.
- Vespa deploy failure involving tensor type, distance metric, or HNSW field.
- Generated schema does not use expected numeric type.

Checks:

- Marqo distance enum values are `euclidean`, `angular`, `dotproduct`, `prenormalized-angular`, `geodegrees`, and `hamming`.
- HNSW `efConstruction` and `m` must be positive.
- Semi-structured embeddings use the configured `vectorNumericType` in the schema template and have specific evidence for `bfloat16` generation.
- Structured embeddings were observed as `tensor<float>` in the schema generator; do not assume structured `bfloat16` support without checking the generated schema.
- `Model.get_dimension()` must resolve `dimensions`; missing or incompatible model properties can surface as schema-generation failures.

Recovery:

- Use an enum-supported distance metric and positive HNSW settings.
- If `bfloat16` is required, prefer a semi-structured path or explicitly verify structured schema output before deploying.
- Keep model-property updates dimension/type-compatible with existing settings.

## Unsupported language, stemming, preprocessing, or schema-template features

Symptoms:

- Add-documents rejects text-field language or stemming.
- Search/ranking code reports unsupported sort, recency, collapse summary, collapse sort, second-phase score modifiers, or custom-score rerank.
- Apply-latest-schema-template refuses to update an old index.

Checks:

- Language and stemming require lexical-search text fields and index support from Marqo `2.16.0+`.
- Sort-by/relevance-cutoff support starts at `2.22.0`.
- Collapse fields, typeahead schema, and schema-template updates start at `2.23.0`.
- Recency/collapse/custom-score features are gated by schema-template versions after `2.24.x` and `2.26.0`.
- `schema_template_version` is the most accurate source for generated-template features when present; otherwise behavior falls back to `marqo_version`.
- Preprocessing enums are strict: text split method is `character`, `word`, `sentence`, or `passage`; image patch method is `simple`, `frcnn`, `dino-v1`, `dino-v2`, or `marqo-yolo`.

Recovery:

- For index-create failures, correct enum values and field features.
- For existing semi-structured indexes, consider a dry-run apply-latest-schema-template to inspect schema diff and Vespa actions before changing production state.
- For existing structured or too-old indexes, recreating the index may be the only safe path.

## Bfloat16 and schema-template issues

Symptoms:

- Expected `tensor<bfloat16>` does not appear in schema.
- Schema update reports no change even though code changed.
- Search feature says the index was created with an older schema version.

Checks:

- Confirm the index is semi-structured if relying on vector numeric type in the template.
- Confirm `schema_template_version`, not just running Marqo version.
- Confirm the latest template was rendered and that deployment activated successfully.
- Confirm Vespa supports the generated tensor type and that the deployed app package actually converged.

Recovery:

- Use `apply_latest_schema_template(..., dry_run=True)` first to compare old/new schema and inspect `configChangeActions`.
- If Vespa requires restart, refeed, or reindex actions, do not force activation unless the operator accepts the impact.
- After activation, verify convergence and refresh index metadata before relying on query behavior.

## Vespa config/document/query URL failures

Symptoms:

- Deploy endpoints return 404/connection refused while document/query health appears healthy, or the reverse.
- Document feed/get/delete fails but query succeeds.
- Query fails with connection errors despite successful deployment.
- Multi-node deployment-session content paths intermittently return 404.

Checks:

- Config URL should target the deploy/config server port, commonly `19071` for local single-node.
- Document and query URLs should target the container document/search port, commonly `8080` for local single-node.
- Base URLs should not include Vespa REST subpaths; Marqo appends them.
- Multi-node config deployment sessions are local to one config server. Sticky sessions or a consistent client are important for subsequent session content calls.
- The content cluster name must match the deployed app package.

Recovery:

- Correct URL environment variables and restart the Marqo API process so the `VespaClient` is reconstructed.
- Check `/state/v1/health` on the intended config and document/query ports before running index operations.
- For multi-node session 404s, route through a sticky load balancer or the same config node.

## Java, Maven, and custom searcher prerequisites

Symptoms:

- Maven build fails before tests run.
- Vespa deployment cannot find the custom searcher bundle.
- Hybrid search behavior does not match Python query generation changes.
- Runtime logs mention invalid custom searcher parameters or missing custom-score fields.

Checks:

- JDK 17 is required for the Maven package.
- Maven must be available before building the custom searcher.
- Artifact coordinates are expected to remain `ai.marqo:marqo-custom-searchers:1.0.0` unless services configuration changes with them.
- Packaging is `container-plugin`, and the deploy jar name expected by the build/deploy path is `marqo-custom-searchers-deploy.jar`.
- Parent Vespa dependency is pinned conservatively for compatibility; do not bump it casually.
- Building the jar does not update a running Vespa deployment. Redeploy the application package after Java changes.

Recovery:

- Fix Java/Maven prerequisites first; use the local-development sub-skill for exact command selection.
- If `HybridSearcher.java` changed, rebuild, redeploy, wait for convergence, then rerun a hybrid query scenario.
- If services configuration or bundle names changed, update Maven and Vespa services configuration consistently.

## Zookeeper lock and convergence issues

Symptoms:

- Error says indexes are being updated and to retry shortly.
- Index create/delete/update races or leaves schema/settings inconsistent.
- Vespa application has not converged or convergence times out.

Checks:

- `IndexManagement` must be created with index operations enabled for mutations.
- If Zookeeper client is present, deployment operations acquire a distributed lock; lock timeout becomes an operation-conflict error.
- If Zookeeper hosts are not configured, Marqo proceeds without distributed locking and warns about races.
- Vespa convergence is asynchronous after deployment; Marqo checks current/wanted generation and non-converged services.
- Local single-node Zookeeper is commonly on port `2181`; multi-node local setups expose multiple Zookeeper ports.

Recovery:

- Retry lock conflicts after the other deployment finishes; do not run concurrent schema/index mutations manually.
- Configure Zookeeper hosts for multi-instance deployments.
- Wait for Vespa convergence before creating new deployment sessions or validating query behavior.
- If convergence never completes, inspect non-converged services and resource limits before retrying schema changes.

## Schema update and rollback cautions

Symptoms:

- `apply_latest_schema_template` returns a diff plus `configChangeActions` but does not activate.
- Schema update reports wrong index type, too-old index version, or future Marqo version.
- Rollback route succeeds but query/document behavior is still inconsistent.

Checks:

- `apply_latest_schema_template` only supports semi-structured indexes created with Marqo `2.23.0+`.
- It refuses indexes created by a newer Marqo version than the current runtime.
- It no-ops when `schema_template_version` already equals the current Marqo version.
- `dry_run=True` never deploys; it is the right first move when diagnosing schema diffs.
- Without `force`, required restart/refeed/reindex actions block activation.
- Rollback uses backup material in the application package; it is not a substitute for data refeed/reindex requirements.

Recovery:

- Prefer dry-run, inspect schema diff, then decide whether actions are operationally acceptable.
- Do not force schema activation that requires restart/refeed/reindex unless explicitly approved.
- After schema updates or rollback, wait for convergence and refresh Marqo index metadata/cache before validating searches.
- For structured or too-old indexes that need new semi-structured-only features, plan an index recreation/migration rather than forcing an unsupported update.

## Safe synthetic diagnostic cases

Use these as future usability cases after the whole skill is integrated:

1. **Structured versus semi-structured diagnosis**: Given an index-settings object with `type=structured`, `allFields` containing text, numeric map, custom vector, and multimodal fields, plus incompatible `collapseFields`, identify every invalid setting, explain which corrections belong to structured versus semi-structured, and predict whether the schema factory will generate structured or semi-structured output.
2. **Vespa local prerequisite inspection**: Run the bundled inspector against a repository root and explain which prerequisites are present or missing for local Vespa, schema templates, custom searcher build, health checks, and safe next steps without deploying anything.
