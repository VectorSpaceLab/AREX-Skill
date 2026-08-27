# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Argos Translate. If the current repo commit, dirty state, package version, entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T05:42:39Z",
  "repository": {
    "name": "argos-translate",
    "remote_url": "https://github.com/argosopentech/argos-translate.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "17ed1a9b055c5ba1b51d76b683bbb0c64e2a4a88",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "argostranslate",
      "version": "1.11.1",
      "import_names": ["argostranslate"],
      "console_scripts": ["argos-translate", "argospm"]
    }
  ],
  "evidence": {
    "source_roots": ["argostranslate/"],
    "docs": [
      "README.md",
      "docs/settings.md",
      "docs/source/cli.rst",
      "docs/source/examples.rst",
      "docs/source/settings.rst",
      "docs/source/modules.rst"
    ],
    "tests": [
      "tests/test_package.py",
      "tests/test_translate.py",
      "tests/test_english_translations.py",
      "tests/data/package/"
    ],
    "entry_points": ["setup.py", "bin/argos-translate", "bin/argospm", "bin/argos-translate-cli"],
    "scripts_considered": [
      "scripts/completion.bash",
      "scripts/uninstall.sh",
      "scripts/model_sacrebleu_score.py",
      "scripts/format.sh",
      "scripts/type_check.sh",
      "scripts/build_and_upload_snap.sh",
      "scripts/update_to_pypi.sh"
    ],
    "excluded_high_level_paths": [
      ".github/",
      "img/",
      "p2p/",
      "data_snap/",
      "docs/source/gui.rst"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current working tree is dirty and this snapshot is clean, inspect the changed paths before relying on the skill.
- If `setup.py` changes `name`, `version`, dependencies, or console scripts, refresh the skill.
- If the package changes `.argosmodel` metadata, `argospm` subcommands, `ARGOS_*` settings, or `translate` APIs, refresh the corresponding sub-skill and references.

## Known scope decisions

- The GUI is not part of this checkout; GUI-specific requests should use the separate GUI project.
- CUDA, Stanza, remote LibreTranslate, and OpenAI provider paths are documented as optional runtime modes, but the generated skill's required verification scope is CPU package/API/CLI behavior.
- Remote language-package downloads are not assumed to be available; package installation guidance distinguishes local archive checks from network index/download steps.
