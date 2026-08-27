# Writer and Review Troubleshooting

## Artifact load fails

**Likely causes**: missing envelope fields, wrong schema name, incompatible model version, invalid JSON, or path from a previous tool step not preserved.

**Recovery**

- Check `schema`, `schema_version`, `data`, and `meta`.
- Use `load_artifact_json` with the expected model/schema.
- Recreate a tiny artifact with `scripts/writer_artifact_smoke.py` to isolate package issues.

## Nested blocks or spans disappear

**Likely causes**: manual JSON construction omitted `children`, `spans`, `provider_binding`, or `provider_payload`; conversion used a plain dict without validation.

**Recovery**

- Build `WriterBlock`/`WriterSpan` models and round-trip with Pydantic validation.
- Use `iter_blocks()` and `block_by_id()` to verify depth-first structure.

## Provider adapter fails

**Likely causes**: missing credentials, invalid external document/block ID, remote API quota, provider payload mismatch, or network failure.

**Recovery**

- Preserve provider fields locally first.
- Ask for credentials and approval before remote calls.
- Keep adapter failures separate from writer artifact schema failures.

## Writer pipeline fails at LLM step

**Likely causes**: provider/API-key/model error rather than writer model error.

**Recovery**

- Run local artifact/tool checks first.
- Route provider setup to model-deployment.
- Keep charge/provider-backed writer pipeline tests optional unless user selected them.

## Review command would post remotely

**Risk**: `lazyllm review` can post PR comments or call provider models.

**Recovery**

- Prefer `review-local` or output-only mode for planning.
- Ask before using `--post` or remote credentials.
- Record target repo/PR, base branch, output path, model, and posting policy.
