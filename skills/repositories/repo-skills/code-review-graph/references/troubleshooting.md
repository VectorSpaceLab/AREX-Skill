# Cross-Cutting Troubleshooting

## Package import or CLI command mismatch

Run the bundled smoke check:

```bash
python scripts/check_crg_install.py
```

If import works but the command is missing, use `python -m code_review_graph` temporarily, then fix PATH or reinstall with `pipx`/`uvx`.

## Graph exists but tools report stale or empty context

Likely causes:

- the graph was built from a different repo root,
- the current branch differs from the built commit,
- the changed files are ignored or not tracked,
- or the database is stale.

Recovery:

```bash
code-review-graph status
code-review-graph update
# if still suspicious:
code-review-graph build
```

## Optional dependency missing

Install only the extra that matches the task:

- embeddings: `pip install "code-review-graph[embeddings]"`
- communities: `pip install "code-review-graph[communities]"`
- wiki: `pip install "code-review-graph[wiki]"`
- eval: `pip install "code-review-graph[eval]"`
- enrichment: `pip install "code-review-graph[enrichment]"`

Do not install `all` by default.

## Cloud provider or credential needed

Cloud embeddings and external services are opt-in. Stop and ask before sending code-derived text to an external provider or assuming credentials are available.

## SQLite lock or concurrent build

CRG uses SQLite with WAL mode. Avoid multiple full builds/watch processes against the same graph database. Retry after the other process exits; if a crash left WAL/shm files inconsistent, rebuild after backing up any important local data.

## Runtime files in this skill

All runnable helpers referenced by this generated skill are bundled under this skill’s own `scripts/` or sub-skill `scripts/` directories. Do not use original source checkout scripts as runtime dependencies.