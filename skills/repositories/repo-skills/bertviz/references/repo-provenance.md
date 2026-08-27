# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T18:16:01Z",
  "repository": {
    "name": "bertviz",
    "remote_url": "https://github.com/jessevig/bertviz.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "79dbaebfe31ada110c1268de7bb6509b14fe9df3",
    "working_tree": "dirty-untracked-skill-artifacts",
    "dirty_paths": [
      "skills/disco/bertviz"
    ]
  },
  "packages": [
    {
      "name": "bertviz",
      "version": "1.4.1",
      "import_names": ["bertviz"]
    }
  ],
  "evidence": {
    "source_roots": [
      "bertviz/__init__.py",
      "bertviz/head_view.py",
      "bertviz/model_view.py",
      "bertviz/neuron_view.py",
      "bertviz/util.py",
      "bertviz/transformers_neuron_view/"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "notebooks/head_view_distilbert.ipynb",
      "notebooks/model_view_bart.ipynb",
      "notebooks/model_view_bert.ipynb",
      "notebooks/model_view_distilbert.ipynb",
      "notebooks/model_view_encoder_decoder.ipynb",
      "notebooks/neuron_view_bert.ipynb",
      "notebooks/neuron_view_gpt2.ipynb",
      "notebooks/neuron_view_roberta.ipynb"
    ],
    "tests": [
      "bertviz/tests/test_attention.py",
      "bertviz/tests/fixtures/config.json",
      "bertviz/tests/fixtures/vocab.txt"
    ],
    "configs": [
      "setup.py",
      "MANIFEST.in"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run
  `refresh-repo-skill`.
- If package metadata, public APIs, packaged JavaScript assets, notebook
  workflows, or neuron-view supported model classes changed, run
  `refresh-repo-skill`.
