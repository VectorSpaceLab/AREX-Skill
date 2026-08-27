# Repository Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- Repository: ANTsPy / `antspyx`
- Public remote: `https://github.com/ANTsX/ANTsPy`
- Branch: `main`
- Commit: `f53447b62f446e630c79fa24e6de79677fc076d9`
- Exact tag: none detected at the source commit
- Working tree state: dirty at generation time
- Dirty-state summary: `skills/` was untracked and contained generated DisCo runtime and review artifacts.

## Package Snapshot

- Source metadata distribution: `antspyx`
- Source metadata version: `0.6.4`
- Public import module: `ants`
- Live inspection distribution/version: `antspyx 0.6.3`
- Live inspection note: installed wheel inspection was used for importability, signatures, and smoke tests because building the current checkout from source requires native ANTs/ITK/CMake compilation.

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `requirements.txt`
- `environment.yml`
- `MANIFEST.in`
- `CMakeLists.txt`
- `ants/`
- `src/`
- `docs/`
- `tutorials/`
- `tests/`
- `data/`
- `scripts/`
- `skills/antspy/` as prior repo-local skill evidence only

## Refresh Guidance

Refresh this skill when ANTsPy changes public APIs, package version, install/build behavior, compiled wrapper names, tutorial workflows, test-backed return contracts, or major routing boundaries. Compare the current checkout against the commit and dirty-state summary above before deciding whether this skill is stale.
