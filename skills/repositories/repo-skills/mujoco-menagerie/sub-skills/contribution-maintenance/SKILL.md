---
name: contribution-maintenance
description: "Contributor and maintainer workflow guidance for MuJoCo Menagerie
  checks, formatting, license regeneration, gallery updates, and safe test
  selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Contribution Maintenance

Use this sub-skill when the user is preparing, reviewing, or repairing a MuJoCo Menagerie contribution and needs the repo's maintainer checks, generated-file workflows, or contribution policy. Keep this sub-skill focused on contribution hygiene and CI-equivalent validation.

## Route boundaries

- Route model choice, directory anatomy, category selection, MJX availability, and catalog questions to `model-catalog`.
- Route direct XML loading, `mujoco.viewer`, `robot_descriptions`, compile errors, and short simulation smoke tests to `model-loading`.
- Route MJCF composition, attachment sites, PD gains, keyframes, mirrored hands, and other advanced editing plans to `model-editing`.
- Stay here for `make install`, `make check`, `make test`, `make gallery`, `make all`, pre-commit hooks, XML formatting, top-level license regeneration, README gallery maintenance, changelog/contributor/CLA policy, and choosing an efficient validation subset from changed paths.

## Inputs to collect

1. Repo root or exported Menagerie checkout to validate.
2. Changed paths, or a Git base/ref from which changed paths can be computed.
3. Whether writes are allowed for formatting, license regeneration, or gallery rendering.
4. Test budget: targeted checks only, full local `make all`, or gallery render as well.
5. Contribution type: existing model edit, new model directory, tooling/test change, docs-only change, or license/contributor update.

## Fast decision table

| Change type | Minimum local checks | Escalate when |
| --- | --- | --- |
| One or more `*.xml` files | Run the Menagerie XML formatter in `--check` or `--write` mode, then run structural/layout checks for the affected model directory and a selected compile/step smoke through `model-loading`. | Scene XML, asset references, actuator definitions, or includes changed; run full `make test` if many directories changed. |
| A model `LICENSE` changed or a model directory was added/removed | Regenerate or check the top-level `LICENSE`; run `make check`; run structural tests. | The generated top-level license diff is unexpected, a base license cannot be found, or several model licenses changed. |
| New model directory | Confirm `README.md`, `LICENSE`, `CHANGELOG.md`, one or more `*.xml`, and normally `scene*.xml`; update changelog/contributors; update gallery model map when it should appear in the README gallery; run `make all`. | Sensor-only or non-standalone assets may not need `scene*.xml`; route catalog/layout judgment to `model-catalog`. |
| Gallery entry, category, preview, or thumbnail changed | Run `make gallery` when writes are allowed; inspect `README.md` and `assets/*.png` diffs; then run selected loading checks for affected XMLs. | Rendering dependencies or MuJoCo/OpenGL fail; route loading/runtime errors to `model-loading`. |
| Tooling, tests, Makefile, or pre-commit config changed | Run `make check` and `make test` (`make all`); compare with the GitHub workflow command. | CI differs from local output, pytest parallelism changes, or hook configuration changed. |
| Changelog or contributors changed | Ensure the proper global or per-model changelog was updated; keep contributors sorted alphabetically by first name; run `pytest test/model_dir_test.py::ContributorsTest -q` when contributors changed. | Contribution ownership or CLA status is unclear; the user must resolve CLA outside the repo. |

## Commands to know

From a Menagerie checkout root:

```bash
make install   # one-time: install pre-commit and the git hook via uv
make check     # pre-commit run --all-files: lint, format, license, XML checks
make test      # manual pre-commit pytest hook over model + structural tests
make gallery   # render thumbnails and update README gallery
make all       # make check followed by make test
```

Bundled helpers in this sub-skill:

```bash
python scripts/menagerie_checklist.py path/to/changed.xml path/to/LICENSE
python scripts/format_mjcf_xml.py --check path/to/file.xml
python scripts/format_mjcf_xml.py --write path/to/file.xml
python scripts/check_menagerie_license.py --root /path/to/checkout --check
python scripts/check_menagerie_license.py --root /path/to/checkout --write
```

Use the repo's own `format_xml.py`, `regenerate_license.py`, and `generate_gallery.py` when operating inside a current checkout; use the bundled helpers when you need portable behavior or a scoped plan outside the source checkout.

## Required references

- Contributor setup, make/pre-commit/CI mapping, changelog/contributor/CLA rules, and check selection: [references/contributor-workflows.md](references/contributor-workflows.md)
- XML style, formatter behavior, and safe formatting commands: [references/xml-formatting.md](references/xml-formatting.md)
- Gallery generation, model map expectations, and write-heavy rendering cautions: [references/gallery-workflow.md](references/gallery-workflow.md)
- Common maintainer workflow failures and fixes: [references/troubleshooting.md](references/troubleshooting.md)

## Validation pattern

1. Run the checklist helper on changed paths to choose the smallest adequate checks.
2. If writes are allowed, apply formatter/license/gallery regeneration before running checks; otherwise use `--check` modes and report exact commands needed to fix generated files.
3. For model XML compile/step validation, route to `model-loading` and request a selected smoke rather than running the full model suite by default.
4. Before declaring ready, report which of `make check`, `make test`, `make all`, selected structural tests, selected loading smoke, license check, and gallery render were run or intentionally skipped.

## Two difficult usability cases

- **Edited one model XML and license:** format only the changed XML, check/regenerate the top-level `LICENSE`, run structural tests for the model directory, then route one selected scene compile/step smoke to `model-loading`; do not run `make gallery` unless the gallery-facing XML, thumbnail, category, or README gallery changed.
- **Added a new model directory:** require `README.md`, `LICENSE`, `CHANGELOG.md`, model XML, normally `scene*.xml`, assets/meshes as referenced, per-model changelog and contributor entry, top-level `LICENSE` regeneration, gallery `MODEL_MAP`/category/preview updates when it should be listed, and full `make all` before PR readiness.
