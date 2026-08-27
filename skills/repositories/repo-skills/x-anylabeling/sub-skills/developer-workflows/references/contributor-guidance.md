# Contributor guidance

Use this reference when modifying X-AnyLabeling code, reviewing a patch, or preparing a focused developer validation plan.

## Contribution workflow posture

Keep changes focused and reviewable:

1. Work on a topic branch.
2. Make the smallest code change that satisfies the task.
3. Add or update focused tests for behavior changes when practical.
4. Format code before review.
5. Keep commits clear and scoped.
6. Do not mix release publishing, localization regeneration, packaging outputs, and feature changes unless the user explicitly requested that combined maintenance task.

## Required style for new Python APIs

New functions and classes must use:

- Python type hints in function signatures, including explicit parameter and return types.
- Google-style docstrings.

Docstrings should state what the function/class does, list arguments, describe return values, and include examples when helpful.

Pattern:

```python
def normalize_label(label: str, *, lowercase: bool = False) -> str:
    """Normalize a label name for display or comparison.

    Args:
        label: Raw label text supplied by a user or config file.
        lowercase: Whether to lowercase the normalized label.

    Returns:
        The normalized label string.

    Examples:
        >>> normalize_label(" Cat ", lowercase=True)
        'cat'
    """
    cleaned = label.strip()
    if lowercase:
        return cleaned.lower()
    return cleaned
```

## Formatting and lint posture

The bundled project formatter helper runs Black over the project. The equivalent command is:

```bash
black .
```

The project metadata configures:

- Black line length `79`, target Python `py311`, excluding generated resources and common build/cache directories.
- Flake8 line length `79`, max complexity `18`, with selected warnings ignored to match the project style.
- Pytest doctest modules and test discovery under `tests`.

Do not format generated `resources.py` by hand. If resource files change, use the localization/resource workflow in `packaging-and-localization.md` and review generated diffs separately.

## Focused tests

Prefer tests that exercise one behavior at a time:

- CLI parser and command behavior for command-line changes.
- Converter fixtures for data format behavior.
- Config normalization tests for configuration semantics.
- Safe model-registry/config inspection for auto-labeling model changes.
- Pure utility tests for label schema, path handling, and validation logic.

Avoid using heavyweight model downloads, remote services, GPU-only tests, or GUI display requirements as default validation unless the user specifically asks for those capabilities and the environment supports them.

## Developer validation tiers

| Change type | Minimum useful checks |
|---|---|
| Docs/reference only | Markdown review for accuracy, no source path leaks in generated skill content |
| CLI conversion behavior | `xanylabeling convert` help plus a tiny fixture conversion |
| Training config validation | Bundled `check_training_config.py` cases; no training launch by default |
| Training worker internals | Inspect command/payload/event behavior and parse synthetic event lines; do not call `model.train` unless approved |
| Packaging script/spec change | Verify target mapping, `pyinstaller` presence, and spec file existence before any build |
| Localization text/resource change | Confirm Qt translation/resource tools, then run generation/compile only with source-control review |
| Model adapter/config change | Inspect config schema and import adapter class without downloading weights; load model only with explicit model files |

## Release and maintainer-only boundaries

Exclude release publishing and release-note generation from ordinary developer workflow tasks. These actions can depend on maintainer credentials, package indexes, GitHub release state, or external changelog state. If the user explicitly asks for a release task, ask for target version, release channel, credentials policy, dry-run expectations, and rollback plan before running side-effectful commands.

## AGPL notice for training changes

Ultralytics is licensed under AGPL-3.0. X-AnyLabeling's core project license is GPL-3.0-only, and Ultralytics is optional for the training feature. If a contribution changes how training is exposed, packaged, or served over a network, preserve the AGPL notice and warn users about network-service source-disclosure obligations.
