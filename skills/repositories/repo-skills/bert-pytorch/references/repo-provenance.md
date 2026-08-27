# Repo Provenance

```json
{
  "schema": "disco.repo-provenance.v1",
  "skill_id": "bert-pytorch",
  "source_repository": {
    "name": "BERT-pytorch",
    "remote_url": "https://github.com/codertimo/BERT-pytorch",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d10dc4f9d5a6f2ca74380f62039526eb7277c671",
    "working_tree": "dirty-generated-skill-artifacts-only"
  },
  "packages": [
    {
      "name": "bert_pytorch",
      "version": "0.0.1a4",
      "import_names": ["bert_pytorch"]
    }
  ],
  "evidence_paths": [
    "README.md",
    "setup.py",
    "requirements.txt",
    "bert_pytorch/__init__.py",
    "bert_pytorch/__main__.py",
    "bert_pytorch/dataset/",
    "bert_pytorch/model/",
    "bert_pytorch/trainer/",
    "test.py",
    ".circleci/config.yml"
  ]
}
```

## Refresh baseline

Treat this skill as potentially stale if the current checkout moves to a different commit, changes the public package version, changes the documented `bert` or `bert-vocab` workflows, or alters the `bert_pytorch` exports and model/training signatures used by the skill.
