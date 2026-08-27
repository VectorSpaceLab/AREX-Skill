# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a GPT Academic checkout. If the current checkout's commit, dirty state, package version, plugin registry, or major evidence paths differ from this snapshot, refresh the repo skill before relying on detailed workflow guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T10:47:13Z",
  "repository": {
    "name": "gpt_academic",
    "remote_url": "https://github.com/binary-husky/gpt_academic.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d6bde0fa54373309bd05823a49bda8da019d2c77",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": [
      "skills/ (generated runtime skill and review artifacts)"
    ]
  },
  "packages": [
    {
      "name": "gpt_academic",
      "version": "4.00",
      "import_names": [
        "toolbox",
        "core_functional",
        "crazy_functional",
        "request_llms",
        "shared_utils",
        "crazy_functions"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "crazy_functions/",
      "request_llms/",
      "shared_utils/",
      "themes/",
      "toolbox.py",
      "core_functional.py",
      "crazy_functional.py",
      "main.py",
      "check_proxy.py",
      "config.py"
    ],
    "docs": [
      "README.md",
      "docs/get_started/",
      "docs/features/",
      "docs/models/",
      "docs/reference/",
      "docs/troubleshooting/",
      "docs/use_audio.md",
      "docs/use_tts.md",
      "docs/use_vllm.md",
      "docs/use_azure.md"
    ],
    "examples": [],
    "tests": [
      "tests/test_key_pattern_manager.py",
      "tests/test_markdown.py",
      "tests/test_markdown_format.py",
      "tests/test_save_chat_to_html.py",
      "tests/test_safe_pickle.py",
      "tests/test_plugins.py",
      "tests/test_llms.py",
      "tests/test_searxng.py",
      "tests/test_vector_plugins.py",
      "tests/test_doc2x.py",
      "tests/test_latex_auto_correct.py",
      "tests/test_tts.py",
      "tests/test_media.py",
      "tests/test_anim_gen.py"
    ],
    "configs": [
      "config.py",
      "requirements.txt",
      "version"
    ]
  }
}
```

## Refresh check

Refresh this skill when any of these change:

- the commit or public version file;
- `crazy_functional.py` plugin names, groups, or wrapper classes;
- provider bridge names or model registry behavior in `request_llms/`;
- setup, configuration, model, document, media, or troubleshooting docs;
- required dependencies in `requirements.txt`;
- native tests that anchor the candidate map or optional backend behavior.
