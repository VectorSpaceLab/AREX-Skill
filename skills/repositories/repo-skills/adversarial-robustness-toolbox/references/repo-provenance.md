# Repository provenance

Read this before deciding whether this skill is current for a checkout of Adversarial Robustness Toolbox. If the current repository commit, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:33:15Z",
  "repository": {
    "name": "adversarial-robustness-toolbox",
    "remote_url": "https://github.com/Trusted-AI/adversarial-robustness-toolbox.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "23539e2c06045d78594b6b6da533eed57967e410",
    "working_tree": "dirty because this DisCo run added generated skill and review artifacts under skills/",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "adversarial-robustness-toolbox",
      "version": "1.20.1",
      "import_names": ["art"]
    }
  ],
  "evidence": {
    "source_roots": ["art"],
    "docs": ["README.md", "docs/guide", "docs/modules"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "setup.cfg", "requirements_test.txt"]
  }
}
```

## Refresh check

Refresh this skill when any of these change:

- ART package version, public estimator constructor signatures, attack/defence class exports, or metric/evaluation/certification import paths.
- Optional backend requirements for PyTorch, TensorFlow/Keras, boosted trees, GPy, OpenCV/Kornia, TensorBoardX, or certification modules.
- Major docs/examples/tests for estimator wrapping, evasion attacks, preprocessing defences, poisoning/privacy/extraction, or metrics/certification.
- The source repository changes away from commit `23539e2c06045d78594b6b6da533eed57967e410`.

This skill intentionally excludes heavy speech, object-detection, tracking, malware, GAN/generation, experimental, notebook, and container-only workflows from its selected runtime coverage. Refresh if those domains become required.
