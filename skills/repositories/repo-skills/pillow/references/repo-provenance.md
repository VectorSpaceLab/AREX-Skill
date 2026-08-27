# Repo Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from the Pillow repository snapshot below.

| Field | Value |
| --- | --- |
| Repository | Pillow |
| Distribution/import | `pillow` / `PIL` |
| Package version observed | `12.3.0.dev0` |
| Git commit | `2d18dacf0b4a4c1ceab2f07f65394431a4c3428e` |
| Branch | `main` |
| Exact tag | none |
| Remote URL | https://github.com/python-pillow/Pillow |
| Working tree state before skill generation | clean |
| Working tree state after skill generation | generated untracked `skills/` review/runtime artifacts |

## Evidence Paths

The generated skill used these relative repository paths as evidence:

- `pyproject.toml`
- `setup.py`
- `_custom_build/`
- `README.md`
- `docs/installation/`
- `docs/handbook/tutorial.rst`
- `docs/handbook/concepts.rst`
- `docs/handbook/image-file-formats.rst`
- `docs/handbook/text-anchors.rst`
- `docs/handbook/writing-your-own-image-plugin.rst`
- `docs/handbook/third-party-plugins.rst`
- `docs/reference/`
- `docs/example/anchors.py`
- `docs/example/DdsImagePlugin.py`
- `src/PIL/`
- `selftest.py`
- `Tests/test_000_sanity.py`
- `Tests/test_image*.py`
- `Tests/test_imageops*.py`
- `Tests/test_file_*.py`
- `Tests/test_imagedraw.py`
- `Tests/test_imagefont.py`
- `Tests/test_imagetext.py`
- `Tests/test_features.py`
- `Tests/test_main.py`

## Excluded Evidence

These paths were intentionally excluded or de-prioritized for runtime skill extraction:

- `.git/`, cache, build, and distribution output directories.
- `.ci/`, `.github/`, `wheels/`, `winbuild/`, `depends/`, and `RELEASING.md` because they are maintainer/release/build infrastructure rather than primary end-user Pillow API workflows.
- `docs/releasenotes/` except as broad version-change context.
- `Tests/oss-fuzz/`, crash, leak, and large-memory checks because they are fuzzing, expensive, unsafe, or maintainer-only validation surfaces.
- DisCo review/test artifact directories because they are generated quality artifacts, not runtime skill evidence.

## Refresh Guidance

Refresh this skill when Pillow's public APIs, docs/reference pages, plugin architecture, supported formats, optional feature checks, build requirements, or version baseline change materially from this snapshot.
