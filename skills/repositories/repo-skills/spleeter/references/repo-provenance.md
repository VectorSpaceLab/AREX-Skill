# Repo provenance

- Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: Deezer Spleeter public package.
- Public remote URL: `https://github.com/deezer/spleeter.git`.
- Commit: `c8854001ac8acad34a9bc2bd15f28475541828b1`.
- Branch: `master`.
- Exact tag at commit: none found.
- Package version from metadata/inspection: `2.4.2`.
- Working tree state at source-evidence capture: source checkout was clean before generated skill artifacts were written. Generated files under `skills/` are construction output and were not used as upstream source evidence, except for production logs and integration artifacts explicitly kept under the artifact directory.

## Evidence paths used

| Relative path | Use |
| --- | --- |
| `pyproject.toml` | Package name/version, Python constraints, dependencies, `evaluation` extra, CLI entry point. |
| `poetry.lock` | Dependency evidence for package runtime. |
| `README.md` | Public quick start, install prerequisites, separation examples, Windows note, troubleshooting pointers. |
| `CHANGELOG.md` | Version changes, deprecated `-i` behavior, Typer/Poetry/API changes, Python support notes. |
| `spleeter.ipynb` | Notebook quick-start separation flow; distilled as reference-only evidence. |
| `spleeter/__main__.py` | CLI command implementations for `train`, `separate`, `evaluate`, metric compilation, exit codes. |
| `spleeter/options.py` | Typer option names, defaults, aliases, argument constraints. |
| `spleeter/separator.py` | `Separator` API, estimator creation, separation, output saving, filename conflict behavior. |
| `spleeter/audio/` | `Codec`, `AudioAdapter`, `FFMPEGProcessAudioAdapter`, audio load/save behavior and ffmpeg requirements. |
| `spleeter/dataset.py` | Training dataset builder, CSV expansion, cache behavior, dimension validation rules. |
| `spleeter/model/` | TensorFlow estimator model function, U-Net/softmax U-Net behavior, MWF path. |
| `spleeter/model/provider/` | Model cache, `.probe`, GitHub release download, checksum behavior, environment variables. |
| `spleeter/resources/*.json` | Embedded pretrained/training descriptors and config defaults. |
| `configs/` | MUSDB-style training/evaluation config and CSV examples. |
| `tests/test_command.py` | CLI version smoke evidence. |
| `tests/test_ffmpeg_adapter.py` | Default adapter, load/save, invalid path behavior. |
| `tests/test_separator.py` | Separation API/file-output behavior, expected stems, filename conflict behavior. |
| `tests/test_train.py` | Tiny training fixture and checkpoint smoke behavior. |
| `tests/test_eval.py` | Tiny MUSDB-like fixture and metric compilation behavior. |
| `.github/CONTRIBUTING.md`, `.github/workflows/test.yml` | Development install/test context and supported Python versions. |

## Excluded source areas

- `.git/`, caches, generated outputs, and `skills/tests/`: VCS/cache/review artifacts.
- `images/`: media assets not needed for operating guidance.
- `paper.md`, `paper.bib`: paper/citation context, not necessary for package operation.
- `docker/`, `conda/`, release/publish workflows: release-maintainer infrastructure not selected for this repo skill.
- `.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`, `CODEOWNERS`: community/review metadata not needed for selected Spleeter operation workflows.

## Runtime verification baseline

A private inspection environment verified Spleeter 2.4.2 imports, CLI help/version, system `ffmpeg`/`ffprobe`, TensorFlow CPU import, `AudioAdapter.default()`, and optional `musdb`/`museval` imports. GPU acceleration was not verified and is treated as optional.
