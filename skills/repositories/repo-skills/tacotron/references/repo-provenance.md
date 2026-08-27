# Repository Provenance

Read this before deciding whether the skill matches a changed Tacotron
checkout. If the commit, dirty state, package behavior, or major evidence paths
differ, run a refresh of the repo skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:24:41Z",
  "repository": {
    "name": "tacotron",
    "remote_url": "https://github.com/keithito/tacotron.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d26c763342518d4e432e9c4036a1aff3b4fdaa1e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tacotron-source-checkout",
      "version": null,
      "import_names": ["text", "datasets", "models", "util", "synthesizer"]
    },
    {
      "name": "tensorflow",
      "version": "1.15.5",
      "import_names": ["tensorflow"]
    }
  ],
  "evidence": {
    "source_roots": ["datasets", "models", "text", "util"],
    "source_files": ["hparams.py", "preprocess.py", "train.py", "eval.py", "synthesizer.py", "demo_server.py"],
    "docs": ["README.md", "TRAINING_DATA.md"],
    "examples": ["preprocess.py", "train.py", "eval.py", "demo_server.py"],
    "tests": ["tests"],
    "configs": ["hparams.py", "requirements.txt"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- Re-check any dirty paths; this snapshot intentionally includes generated
  `skills/` output and is not a clean source-only baseline.
- Refresh if public CLI flags, `tf.contrib` usage, dataset formats, text
  symbols/cleaners, checkpoint handling, or audio hparams change.
- The source tree has no package metadata; inspect import roots directly when
  refreshing.
