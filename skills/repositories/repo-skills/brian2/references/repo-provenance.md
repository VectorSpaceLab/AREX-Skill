# Repository Provenance

## Purpose

Read this before deciding whether the Brian2 skill matches a checkout or before
running a refresh. The skill was distilled from the source state below and from
live package inspection. A changed commit, package version, dirty evidence set,
or public API should trigger a refresh review.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "brian2",
    "remote_url": "https://github.com/brian-team/brian2",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "aec54d2afae3621f42be2a7030b9bb6f21488571",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "Brian2",
      "version": "2.9.0",
      "import_names": ["brian2"]
    }
  ],
  "evidence": {
    "source_roots": ["brian2"],
    "docs": [
      "README.md",
      "docs_sphinx/introduction/install.rst",
      "docs_sphinx/user",
      "docs_sphinx/advanced selected pages"
    ],
    "examples": ["examples", "tutorials"],
    "tests": ["brian2/tests"],
    "configs": ["pyproject.toml", "setup.py", "setup.cfg"]
  }
}
```

## Version and inspection notes

- The checkout is shallow and has no local tags. The prepared inspection
  environment observed Brian2 `2.9.0`; its editable install required a
  temporary `setuptools-scm` version override. That setup workaround is not a
  runtime dependency of an ordinary PyPI/Conda installation.
- The source package declares Python >=3.12 and base dependencies including
  NumPy, Cython, SymPy, pyparsing, Jinja2, setuptools, and packaging.
- The runtime graph intentionally does not claim GSL, plotting, SciPy, Pandas,
  Jupyter, multiprocessing, or benchmark coverage as required capabilities.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the graph as
  potentially stale and run `refresh-repo-skill`.
- If the current dirty paths differ materially from `skills/`, re-check whether
  source evidence changed before using the graph.
- If package metadata, public entry points, code-generation behavior, or major
  documentation paths change, refresh the graph even when the commit is
  unchanged in a local export.
