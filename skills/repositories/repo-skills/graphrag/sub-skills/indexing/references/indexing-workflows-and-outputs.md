# Indexing Workflows and Outputs

## Built-In Pipelines

`PipelineFactory` maps indexing methods to ordered workflow names. A config-level `workflows` list overrides these built-ins.

### Standard

1. `load_input_documents`
2. `create_base_text_units`
3. `create_final_documents`
4. `extract_graph`
5. `finalize_graph`
6. `extract_covariates`
7. `create_communities`
8. `create_final_text_units`
9. `create_community_reports`
10. `generate_text_embeddings`

### Fast

1. `load_input_documents`
2. `create_base_text_units`
3. `create_final_documents`
4. `extract_graph_nlp`
5. `prune_graph`
6. `finalize_graph`
7. `create_communities`
8. `create_final_text_units`
9. `create_community_reports_text`
10. `generate_text_embeddings`

### Update Suffix

Update runs prepend `load_update_documents`, run the standard or fast base workflows, then run:

1. `update_final_documents`
2. `update_entities_relationships`
3. `update_text_units`
4. `update_covariates`
5. `update_communities`
6. `update_community_reports`
7. `update_text_embeddings`
8. `update_clean_state`

The public CLI accepts `--method standard` or `--method fast` on `graphrag update`; the API derives `standard-update` or `fast-update` when `is_update_run=True`.

## Workflow Semantics

- Workflows read/write official data through the run context table providers and storage providers.
- A workflow result is for lifecycle reporting; durable output should be in configured tables/storage.
- `Pipeline.remove("load_input_documents")` or `Pipeline.remove("load_update_documents")` is used when API callers pass `input_documents` directly.
- A workflow may request the pipeline stop by returning `WorkflowFunctionOutput(stop=True)`.

## Default Output Tables

Core default tables:

- `documents`: imported documents and associated text units.
- `text_units`: chunks with token counts, source document IDs, and graph/covariate links.
- `entities`: entity titles, types, descriptions, frequencies, degrees, and text unit links.
- `relationships`: source/target pairs, descriptions, weights, combined degrees, and text unit links.
- `communities`: hierarchical Leiden communities with children, entity IDs, relationship IDs, text unit IDs, period, and size.
- `community_reports`: LLM reports per community with summary, full content, rank, findings, period, and size.
- `covariates`: optional claim records when claim extraction is enabled.

Support files commonly include `stats.json` and `context.json`. Embeddings are stored in the configured vector store; snapshot settings may add parquet or GraphML files.

## Query-Oriented Output Expectations

- Global search needs communities and community reports; BYOG global workflows need entities and relationships as inputs.
- Local search typically needs entities, relationships, text units, community reports, and compatible embeddings.
- DRIFT search relies on graph/community outputs plus text/vector context depending on config.
- Basic search is chunk/vector-oriented and needs text units plus text unit embeddings.
- BYOG workflows may intentionally omit upstream tables, but downstream workflows still need their input tables to exist.

## Incremental Update Details

Update runs create a timestamped update area with `previous` and `delta` table providers. Previous output tables are copied before delta work. Update merge workflows combine old and new tables, offset human-readable IDs where needed, and filter invalid graph relationships such as edges whose endpoints do not exist in the merged entity table.

Before update:

- Validate previous output has the tables required by the selected search/use case.
- Ensure new input data is discoverable and not identical to already indexed content unless a no-op update is intended.
- Check duplicate/deleted/new document titles in the project-specific update policy.

After update:

- Validate merged output tables, not just delta tables.
- Inspect logs for skipped embeddings or empty update states.
- Run query smoke checks only after output validation passes; route query setup to `../querying/`.

## Custom Workflow Registration

For advanced API use, `PipelineFactory.register(name, workflow)` registers a workflow function and `PipelineFactory.register_pipeline(name, workflows)` registers a method name. Custom workflow functions accept `(config, context)` and return a `WorkflowFunctionOutput`. Put substantial extension implementation guidance in `../package-extensions/`; keep this sub-skill focused on selecting and operating indexing pipelines.
