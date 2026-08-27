# Haystack Troubleshooting

## Import And Optional Dependencies

- `ModuleNotFoundError` for a converter, generator, embedder, or evaluator usually means an optional integration is missing. Install the narrow extra or route to a local component.
- `Secret` and provider generators should read credentials from environment variables; do not hard-code API keys.
- Local model components may require large downloads, GPU memory, or backend-specific packages. Keep those as explicit user decisions.

## Pipeline And Component Failures

- Socket errors usually come from connecting the wrong output key to an input key. Inspect component input/output sockets and route to `pipelines-and-components`.
- Infinite or repeated execution usually needs `max_runs_per_component`, loop analysis, or breakpoints.
- Serialization failures often mean a component has non-serializable constructor state or missing `to_dict`/`from_dict` support.

## Retrieval And RAG Failures

- Empty retrieval results can come from an empty store, strict filters, missing embeddings, mismatched embedder dimensions, or duplicate-write policy.
- Validate `count_documents()`, document metadata, top result IDs, and scores before connecting a generator.

## Repository Development

- In this checkout, `AGENTS.md` requires Hatch before running project code. Use `hatch --version` and repository `hatch run ...` commands rather than bare `python`/`pip`.
- Prefer focused unit tests and small scripts before full suites.
