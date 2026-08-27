# Repo Provenance

schema: `disco.repo-provenance.v1`

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "repository": {
    "name": "ogb",
    "remote_url": "https://github.com/snap-stanford/ogb",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "61e9784ca76edeaa6e259ba0f836099608ff0586",
    "working_tree": "dirty",
    "package": {
      "distribution": "ogb",
      "version": "1.3.6"
    },
    "evidence_paths": [
      "README.md",
      "MANIFEST.in",
      "setup.py",
      "ogb/",
      "ogb/graphproppred/",
      "ogb/nodeproppred/",
      "ogb/linkproppred/",
      "ogb/lsc/",
      "ogb/io/",
      "ogb/utils/",
      "examples/README.md",
      "examples/graphproppred/",
      "examples/linkproppred/",
      "examples/nodeproppred/",
      "examples/lsc/"
    ]
  }
}
```

## Staleness note

This skill reflects the repository state at the commit above. If the source
checkout changes, refresh the skill and compare the new source evidence before
reusing it.
