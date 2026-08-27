# Repo provenance

- Schema: `disco.repo-provenance.v1`
- Source repository: Gerev
- Source commit: `1018e122aae288ca9c77d72b0efbe9ff7a6df750`
- Branch: `main`
- Exact tag at HEAD: none
- Dirty state at generation time: dirty checkout with untracked `skills/` content from this production run
- Remote URL: `https://github.com/GerevAI/gerev.git`
- Package version: not declared by pyproject/setup metadata; release hint `0.0.4` appears in `deploy.sh`

## Evidence paths used

- `README.md`
- `ADDING-A-DATA-SOURCE.md`
- `app/README.md`
- `app/requirements.txt`
- `app/main.py`
- `app/api/data_source.py`
- `app/api/search.py`
- `app/data_source/api/*`
- `app/data_source/sources/*`
- `app/indexing/*`
- `app/parsers/*`
- `app/paths.py`
- `app/search_logic.py`
- `app/models.py`
- `app/schemas/*`
- `docs/data-sources/*`
- `ui/package.json`
- `ui/src/*`
- `run.sh`
- `Dockerfile`
- `docker-compose.yaml`

## Refresh baseline

If the checkout changes, rerun the runtime inspection helpers and compare against this snapshot before reusing the skill:

- `../scripts/inspect_gerev_runtime.py`
- `../sub-skills/data-source-connectors/scripts/inspect_data_sources.py`
- `../sub-skills/search-indexing/scripts/inspect_search_indexing.py`
- `../sub-skills/deployment-runtime/scripts/inspect_runtime_paths.py`
