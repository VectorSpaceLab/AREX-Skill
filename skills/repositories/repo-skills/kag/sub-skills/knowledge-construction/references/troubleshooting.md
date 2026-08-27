# Knowledge Construction Troubleshooting

## Purpose

Use this when a KAG project cannot be created, restored, committed, or built cleanly.

## Failure surfaces

### Namespace or schema mismatch

**Symptoms**

- project creation rejects the namespace
- schema commit cannot find the expected schema file
- a build writes data under the wrong namespace

**Likely causes**

- the namespace is not the expected capitalized alphanumeric form
- `schema/<Namespace>.schema` does not match `project.namespace`
- the project directory was copied from another example without renaming the schema

**Recovery**

1. Run `scripts/validate_project_layout.py`.
2. Fix the namespace and schema filename so they match.
3. Re-run `knext project ...` or `knext schema commit` only after the layout is consistent.

### Missing OpenSPG project or server

**Symptoms**

- `knext project restore` or `knext schema commit` fails with a connection error
- builder output cannot be written to the graph store

**Likely causes**

- the host address is wrong
- the target project id does not exist
- the OpenSPG server is not running

**Recovery**

1. Confirm the server host in the project config.
2. Confirm the project id in the local config.
3. Stop and ask for service approval if the workflow needs a live backend.

### Builder config does not register

**Symptoms**

- `from_config(...)` cannot find the builder, reader, extractor, or writer type
- a custom project module is ignored

**Likely causes**

- the `type` value is misspelled
- the custom module was never imported before registry construction
- the config points at a chain or component name that is not registered in this package version

**Recovery**

1. Use `kag interface --list` or `kag interface --cls <ClassName>`.
2. Import project modules before building the chain.
3. Correct the `type` field to a registered name.

### Vectorizer dimension mismatch

**Symptoms**

- a project created with one vectorizer later fails when the vectorizer changes
- a validator reports a dimension that does not match the project config

**Likely causes**

- the embedding model changed after the project was created
- the vectorizer config uses the wrong `vector_dimensions`

**Recovery**

1. Inspect the redacted config summary.
2. Confirm the vectorizer dimension before reusing a project.
3. Recreate the project if the vectorizer family changed in a way the project cannot absorb.

### Destructive writer mode

**Symptoms**

- graph data disappears after a build
- a writer seems to delete rather than upsert

**Likely causes**

- the writer was configured with `delete: true`
- a domain-specific writer mapped an operation to delete semantics

**Recovery**

1. Inspect the builder config before running it.
2. Use the layout validator and config inspector to confirm the writer mode.
3. Only run destructive deletion when you explicitly intend to clear graph data.

### Checkpoints and resume behavior

**Symptoms**

- a rerun appears to skip work
- a build resumes from older data
- the checkpoint directory hides the real source of failure

**Likely causes**

- the writer or reader checkpoint has already recorded work for a chunk
- the layout changed but old checkpoints were kept

**Recovery**

1. Check whether the failure is a safe resume or a layout/config bug.
2. Keep checkpoints when the run is genuinely resumable.
3. Remove checkpoints only after you have confirmed the bug is not caused by them.

### Optional file readers fail

**Symptoms**

- `docx`, `pdf`, or markdown readers fail even though the package imports
- a scanner needs a network source or third-party dependency

**Likely causes**

- the reader depends on a library or service that is not available
- the source is external and not safe to fetch during preflight

**Recovery**

1. Prefer a local file reader for validation.
2. Check whether the needed optional dependency is installed.
3. For network readers, stop and request credentials or network approval.
