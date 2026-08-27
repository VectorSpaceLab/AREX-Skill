# Contribution Maintenance Troubleshooting

Use this reference when Menagerie contributor checks fail. Keep the failure class explicit: setup/pre-commit, XML formatting, license generation, gallery rendering, structural tests, or model loading. Route model runtime debugging to `model-loading` and advanced XML editing to `model-editing`.

## `uv` is missing or cannot create an environment

Symptoms:

- `make install`, `make check`, or `make test` fails before running hooks.
- Shell reports `uv: command not found`.

Actions:

1. Install `uv` using the user's preferred package manager or Python tool installer.
2. Re-run `make install` in the checkout.
3. If only a targeted script is needed, run bundled helpers directly with Python:

   ```bash
   python scripts/format_mjcf_xml.py --check path/to/file.xml
   python scripts/check_menagerie_license.py --root /path/to/checkout --check
   ```

## Pre-commit hook environment is stale

Symptoms:

- Hooks fail with missing dependencies after tool versions changed.
- `pre-commit run --all-files` behaves differently from commit-time hooks.

Actions:

```bash
pre-commit clean
make install
make check
```

If the pytest hook is needed, run it explicitly because it is manual-stage only:

```bash
pre-commit run --hook-stage manual pytest --all-files
```

## XML formatter reports "Not formatted"

Symptoms:

- `format_xml.py --check` or pre-commit `format-xml` fails.
- Diff shows indentation, quoting, wrapping, or `<foo />` versus `<foo/>` changes.

Actions:

```bash
uv run format_xml.py --write path/to/file.xml
uv run format_xml.py --check path/to/file.xml
```

If the repo formatter is unavailable, use the bundled formatter:

```bash
python scripts/format_mjcf_xml.py --write path/to/file.xml
```

Then rerun structural and loading checks if the XML's semantics changed; formatting alone does not prove the model compiles.

## XML parse error while formatting

Symptoms:

- Formatter raises an XML syntax error.
- No formatted output is produced.

Actions:

1. Open the reported file and line.
2. Fix unclosed tags, invalid attribute quoting, duplicate attributes, invalid comments, or bad entity escaping.
3. Re-run formatter check.
4. Route MJCF-level errors after parsing to `model-loading`.

## Top-level `LICENSE` is out of date

Symptoms:

- `regenerate_license.py --check` fails.
- Bundled license checker reports `FAIL: LICENSE file is out of date`.
- A model directory `LICENSE` changed, or a model directory was added/removed.

Actions:

```bash
uv run regenerate_license.py
uv run regenerate_license.py --check
```

Portable alternative:

```bash
python scripts/check_menagerie_license.py --root /path/to/checkout --write
python scripts/check_menagerie_license.py --root /path/to/checkout --check
```

Inspect the top-level `LICENSE` diff. It should be a deterministic concatenation of one section per model directory license followed by the base project license.

## License checker cannot find a base license

Symptoms:

- Error says `Cannot find base license`.
- Top-level `LICENSE` is missing and no `opensource/LICENSE` fallback exists.

Actions:

1. Restore a valid top-level `LICENSE` or base project license source.
2. Re-run license generation.
3. Do not invent license text; ask the maintainer for the correct base license.

## Contributors sorting test fails

Symptoms:

- `ContributorsTest` reports a section starting line and first out-of-order entry.

Actions:

1. Keep each contiguous block of `- ` contributor lines sorted by `str.casefold`, effectively alphabetically by first name.
2. Do not move non-list headings or prose into the sorted block.
3. Re-run:

   ```bash
   uv run --with-requirements test/requirements.txt pytest test/model_dir_test.py::ContributorsTest -q
   ```

## Model directory structural test fails

Symptoms:

- Missing `README.md`, exact `LICENSE`, `CHANGELOG.md`, or `scene*.xml`.

Actions:

1. Add the missing required file if this is a normal standalone model directory.
2. If the directory is intentionally non-standalone or sensor-only, route the exemption/catalog decision to `model-catalog`; avoid casually weakening tests.
3. Re-run:

   ```bash
   uv run --with-requirements test/requirements.txt pytest test/model_dir_test.py -q -k model_dir
   ```

## Pytest model simulation fails or emits warnings

Symptoms:

- `test/model_test.py` fails on a `scene*.xml`.
- MuJoCo warnings are reported after the short 0.1 second simulation.

Actions:

1. Route the specific scene XML to `model-loading` for selected compile/step smoke debugging.
2. Check asset paths, include paths, actuator control ranges, contacts, keyframes, and minimum MuJoCo version.
3. If many scenes fail after a tooling change, reproduce CI with:

   ```bash
   uv run --with-requirements test/requirements.txt pytest -n auto
   ```

## Gallery rendering fails

Symptoms:

- `make gallery` fails while compiling a model, rendering a PNG, or rewriting README.
- Output mentions missing mesh assets, MuJoCo render/OpenGL problems, missing README markers, or unknown license text.

Actions:

1. For compile and asset errors, route the affected XML to `model-loading`.
2. For missing markers, restore the generated README model-section markers before rerunning.
3. For OpenGL/rendering problems, validate MuJoCo rendering support in the local environment; document the environment block if rendering is not available.
4. For bad thumbnails, adjust keyframe/camera overrides only after confirming the model compiles and the gallery target is correct.

## Local `make all` passes but CI fails

Compare:

- Python version used by CI: 3.12
- pytest command: `uv run --with-requirements test/requirements.txt pytest -n auto`
- package resolution from `test/requirements.txt`
- MuJoCo native wheel/runtime availability
- test parallelism and file-order assumptions
- whether generated files were committed after formatter/license/gallery rewrites

Re-run local checks in the closest CI shape before changing code:

```bash
make check
uv run --with-requirements test/requirements.txt pytest -n auto
```

## A check was intentionally skipped

When returning a maintainer plan or PR-readiness summary, name skipped checks and why:

- `make gallery` skipped because no gallery-facing files changed.
- Full `make test` skipped because only docs changed and the user requested a quick plan.
- Selected loading smoke skipped because `mujoco` is not installed in the available environment.
- License regeneration skipped because no model `LICENSE`, top-level `LICENSE`, or model directory set changed.

Do not present a skipped check as passed.
