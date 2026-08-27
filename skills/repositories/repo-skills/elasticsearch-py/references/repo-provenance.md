# Repository provenance

Schema: `disco.repo-provenance.v1`

- Repository: public `elastic/elasticsearch-py` Python client
- Source commit: `dd583210d228b4004a96aa7a1e596518118669f8`
- Branch: `main`
- Exact tag: none at the source commit
- Working tree: clean at the initial snapshot; generated skill files are new workspace outputs
- Package distribution: `elasticsearch` version `9.5.0`
- Python requirement: `>=3.10`
- Public source URL: `https://github.com/elastic/elasticsearch-py`
- Evidence roots: `elasticsearch/`, `pyproject.toml`, `README.md`, `docs/reference/`, `examples/bulk-ingest/`, `examples/dsl/`, selected `test_elasticsearch/`, `AGENTS.md`, and `noxfile.py`
- Generated/API boundary: synchronous and asynchronous client modules under the package are generated from the Elasticsearch API specification; runtime users should not edit them.

Refresh this skill when the package major/minor version, public constructor
signatures, optional extras, DSL/ES|QL behavior, or evidence paths change. A
dirty source checkout or a new major client version should be treated as a
refresh trigger rather than assumed compatible.
