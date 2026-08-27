# Repository Provenance

## Purpose

Read this before deciding whether the NLTK skill still matches a checkout or an installed package. If the source commit, dirty state, package version, public entry points, or major evidence paths differ, run `refresh-repo-skill` rather than assuming this operating graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:02:43Z",
  "repository": {
    "name": "nltk",
    "remote_url": "https://github.com/nltk/nltk.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "5f39cb391eda689af5c8de5e3a8e758776c9c9dd",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/ (untracked production log and generated skill/artifact outputs)"
    ]
  },
  "packages": [
    {
      "name": "nltk",
      "version": "3.10.2",
      "import_names": ["nltk"]
    }
  ],
  "evidence": {
    "source_roots": [
      "nltk/",
      "nltk/tokenize/",
      "nltk/tag/",
      "nltk/corpus/",
      "nltk/chunk/",
      "nltk/parse/",
      "nltk/sem/",
      "nltk/classify/",
      "nltk/lm/",
      "nltk/metrics/",
      "nltk/translate/"
    ],
    "docs": [
      "README.md",
      "web/index.rst",
      "web/install.rst",
      "web/data.rst",
      "web/howto.rst"
    ],
    "examples": [
      "nltk/test/*.doctest"
    ],
    "tests": [
      "nltk/test/unit/test_cli.py",
      "nltk/test/unit/test_tokenize.py",
      "nltk/test/unit/test_pos_tag.py",
      "nltk/test/unit/test_stem.py",
      "nltk/test/unit/test_data.py",
      "nltk/test/unit/test_data_security.py",
      "nltk/test/unit/test_downloader*.py",
      "nltk/test/unit/test_corpus_util.py",
      "nltk/test/unit/test_corpora.py",
      "nltk/test/unit/test_chunk.py",
      "nltk/test/unit/test_classify.py",
      "nltk/test/unit/test_wordnet.py"
    ],
    "configs": [
      "setup.py",
      "setup.cfg",
      "requirements-ci.txt",
      "requirements-test.txt",
      "pip-req.txt",
      "tox.ini",
      ".github/workflows/ci.yml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `5f39cb391eda689af5c8de5e3a8e758776c9c9dd`, treat the skill as potentially stale.
- If the current working tree is clean or its changed paths differ from the recorded `skills/` production outputs, refresh the provenance and re-check the source evidence.
- If NLTK changes its console entry point, base dependencies, data-resource names, tokenizer/tagger model layout, or public API families, refresh the affected sub-skill even if the commit is unchanged in a local checkout.
- If the installed distribution version is not `3.10.2`, use the version-specific API/data facts from the active package and do not assume the current resource names are unchanged.
