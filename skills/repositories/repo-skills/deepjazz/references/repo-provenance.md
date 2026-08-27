# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of deepjazz. If the current repo commit, dirty state, dependency surface, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:19:41Z",
  "repository": {
    "name": "deepjazz",
    "remote_url": "https://github.com/jisungk/deepjazz.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9c3b11245db196311b9f0176e984a38725a7113a",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "deepjazz",
      "version": null,
      "import_names": ["generator", "grammar", "preprocess", "qa", "lstm"],
      "distribution": "not-installable-script-collection"
    },
    {
      "name": "Keras",
      "version": "1.2.2",
      "import_names": ["keras"]
    },
    {
      "name": "Theano",
      "version": "0.9.0",
      "import_names": ["theano"]
    },
    {
      "name": "music21",
      "version": "3.1.0",
      "import_names": ["music21"]
    }
  ],
  "evidence": {
    "source_roots": ["generator.py", "grammar.py", "preprocess.py", "qa.py", "lstm.py"],
    "docs": ["README.md", "LICENSE", "NOTICE"],
    "examples": ["midi/original_metheny.mid"],
    "tests": [],
    "configs": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the repository gains packaging metadata, command-line options, tests, documentation, or a generalized MIDI parser, refresh this skill.
- If the public dependency target changes away from Python 2/Keras 1/Theano, refresh both the environment guidance and generation sub-skill.
- This skill was generated from source evidence before any creation-run output directories were added.
