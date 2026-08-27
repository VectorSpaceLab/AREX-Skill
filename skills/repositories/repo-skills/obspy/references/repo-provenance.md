# Repository Provenance

Read this before deciding whether the operating graph matches a checkout. If
the commit, dirty paths, package version, public entry points, or major evidence
families differ, use the repo-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "obspy",
    "remote_url": "https://github.com/obspy/obspy.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c839d096dd0ce15ea8c27360004d7089f46819b4",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "obspy",
      "version": "0.0.0.dev0+0.gc839d096dd",
      "import_names": ["obspy"]
    }
  ],
  "evidence": {
    "source_roots": ["obspy"],
    "docs": ["README.md", "misc/docs/source/packages", "misc/docs/source/tutorial"],
    "examples": ["misc/docs/source/tutorial/code_snippets"],
    "tests": ["obspy/core/tests", "obspy/io/*/tests", "obspy/clients/*/tests", "obspy/signal/tests", "obspy/realtime/tests", "obspy/taup/tests", "obspy/geodetics/tests", "obspy/imaging/tests", "obspy/scripts/tests"],
    "configs": ["setup.py", "pyproject.toml", "MANIFEST.in"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- Compare current dirty paths with the recorded `skills/`-only generated-output
  state; source edits invalidate the baseline.
- Recheck package metadata, console entry points, IO plugin registrations,
  compiled extension names, and the public modules that own the five routes.
- Recheck optional dependency behavior and focused native cases before carrying
  claims into a refreshed graph.

The snapshot records a development checkout. The graph intentionally omits
local environment paths, activation commands, caches, compiled build outputs,
and review artifacts from public runtime content.
