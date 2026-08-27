# Contributor Workflows

This reference distills the Menagerie contributor setup, local maintainer checks, CI mapping, generated-file rules, and safe test selection. Commands assume the shell is at the root of a Menagerie checkout unless a command explicitly supplies `--root`.

## One-time setup

Menagerie's contributor tooling is intentionally small. The repo documents `uv` as the only setup prerequisite.

```bash
make install
```

`make install` runs:

```bash
uv tool install pre-commit
pre-commit install
```

After installation, fast lint/format/license/XML hooks run automatically on `git commit`. The pytest hook is configured for the manual pre-commit stage because it is slower.

## Make targets

| Target | Repo command | What it does | When to use |
| --- | --- | --- | --- |
| `make install` | `uv tool install pre-commit && pre-commit install` | Installs pre-commit and the Git hook. | Once per checkout. |
| `make check` | `pre-commit run --all-files` | Runs generic whitespace/YAML/merge-conflict hooks, ruff lint/format, top-level license check, and MJCF XML format checks. | Before commit and after XML/license/tooling changes. |
| `make test` | `pre-commit run --hook-stage manual pytest --all-files` | Runs the manual pytest hook, which executes the model simulation and structural test suite. | Before pushing model changes, new model dirs, or test/tooling changes. |
| `make gallery` | `uv run --no-project generate_gallery.py` | Renders thumbnails into `assets/` and updates the README gallery between generated markers. | Only when gallery entries/thumbnails/categories/previews should change. |
| `make all` | `make check && make test` | Runs the documented local CI-equivalent check set. | Final local readiness check for a PR. |

## Pre-commit hooks

The pre-commit configuration excludes `*.patch` and `*.ipynb` files. It includes:

- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-merge-conflict`
- `mixed-line-ending`
- `ruff --fix`
- `ruff-format`
- local `regenerate-license`: `uv run --quiet regenerate_license.py --check`
- local `format-xml`: `uv run --quiet format_xml.py --check` for `*.xml`
- manual-stage `pytest`: `uv run --quiet --with-requirements test/requirements.txt pytest test/ -q`

Useful direct commands:

```bash
pre-commit run --all-files
pre-commit run --hook-stage manual pytest --all-files
pre-commit run format-xml --files path/to/model.xml
pre-commit run regenerate-license --all-files
```

## GitHub workflow mapping

The build workflow checks out the repository, installs `uv` with Python 3.12 and cache keyed by `test/requirements.txt`, then runs:

```bash
uv run --with-requirements test/requirements.txt pytest -n auto
```

The repository documentation describes a green local `make all` as the practical CI-equivalent because it covers both pre-commit checks and the slower pytest suite. If local `make all` passes but CI fails, compare Python version, pytest parallelism (`-n auto`), MuJoCo wheel/OpenGL availability, and any path-dependent asset loading.

## Safe check selection from changed paths

Use the bundled checklist helper first when the changed-path set is non-trivial:

```bash
python scripts/menagerie_checklist.py path/to/changed.xml path/to/LICENSE
# or, from a Git checkout:
python scripts/menagerie_checklist.py --base origin/main
```

General selection rules:

1. **Always include `make check`** for PR readiness unless the task is only advisory and no checkout is available.
2. **Changed `*.xml`:** run `format_xml.py --check` or the bundled formatter on the changed XML files; for scene/model behavior, route selected compile/step validation to `model-loading`.
3. **Changed model directory layout:** run structural tests, at least `pytest test/model_dir_test.py -q`, and narrow with `-k <model_dir>` when only one directory changed.
4. **Changed model license or added/removed model directory:** run the top-level license check/regeneration.
5. **Changed README gallery, `generate_gallery.py`, thumbnail-relevant XML, or gallery model map:** run `make gallery` only when writes are allowed and the render cost is acceptable.
6. **Changed tests/tooling/pre-commit/Makefile:** run `make all`; direct `pytest -n auto` is useful when reproducing CI exactly.

## Model directory requirements

The structural test discovers top-level directories that contain XML files, skipping non-model infrastructure directories. For each model directory it requires:

- `README.md`
- `LICENSE` exactly with that filename
- `CHANGELOG.md`
- at least one `scene*.xml` unless the directory is intentionally non-standalone, such as a sensor-only directory documented as exempt

When adding a model directory, also verify:

- model XML files include only the model; standalone scenes include planes/lights/extra bodies in `scene*.xml`
- `assets/` or other mesh directories exist if referenced by XML
- all XML include paths remain relative to the model directory layout
- model-specific README documents the source/conversion path and minimum MuJoCo version when applicable
- model-specific changelog records the new model or update
- top-level license is regenerated from every model `LICENSE`
- gallery mapping is updated when the model should appear in the README model table

## Changelog, contributors, and CLA policy

Document changes in the correct changelog:

- repo-wide tooling, CI, docs, and shared infrastructure changes belong in top-level `CHANGELOG.md`
- model-specific changes belong in that model directory's `CHANGELOG.md`

Add the contributor name to `CONTRIBUTORS.md` and keep each contiguous contributor section sorted alphabetically by first name. The structural test contains a dedicated `ContributorsTest` for this sorting rule.

Contributions must be accompanied by the Google Contributor License Agreement. The contributor or their employer retains copyright; the CLA grants permission to use and redistribute the contribution. The CLA is an external administrative requirement: do not try to prove it with local scripts; ask the contributor or maintainer to confirm status through the official CLA process.

## Case: edited one model XML and license

Suggested scoped plan:

```bash
# 1. Format/check only the touched XML.
uv run format_xml.py --check model_dir/file.xml
# or, if writes are allowed:
uv run format_xml.py --write model_dir/file.xml

# 2. Check/regenerate top-level LICENSE after model LICENSE changed.
uv run regenerate_license.py --check
# if mismatch is expected and writes are allowed:
uv run regenerate_license.py

# 3. Run structural checks for layout and contributor sorting.
uv run --with-requirements test/requirements.txt pytest test/model_dir_test.py -q -k model_dir

# 4. Route selected compile/step smoke for the affected scene XML to model-loading.
```

Run `make check` before committing. Run `make test` or `make all` if the XML controls, contacts, includes, assets, or scene behavior changed beyond formatting/license metadata.

## Case: added a new model directory

Suggested scoped plan:

1. Confirm `README.md`, `LICENSE`, `CHANGELOG.md`, model XML, and normally `scene*.xml` are present.
2. Confirm mesh assets referenced by XML are checked in and paths are relative.
3. Add a model-specific changelog entry and a contributor entry.
4. Regenerate top-level `LICENSE`.
5. Decide with `model-catalog` whether the model belongs in the gallery/catalog; if yes, update the gallery model map/category and run `make gallery`.
6. Run `make check` then `make test`; for final PR readiness run `make all`.
7. Route selected compile/step debugging to `model-loading` if full pytest fails on the new scene.
