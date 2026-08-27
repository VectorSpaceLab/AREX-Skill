# Packaging and Release Safety

## Non-negotiable authorization gates

Packaging inspection and local wheel validation may be read-only or locally
mutating. A release is externally mutating. Never automatically:

- change package versions or dependency pins;
- stage or commit files;
- push a branch or tag;
- create a GitHub release;
- upload to TestPyPI, PyPI, or Hugging Face;
- reuse credentials merely because they exist in the environment.

Obtain explicit authorization immediately before each requested mutation. The
authorization must identify the exact version, commit, destination, artifact set,
and whether replacing/skipping an existing artifact is acceptable. A request to
“prepare a release” authorizes analysis and a checklist, not publication.

## What the repository automation does

These source scripts/workflows were used only as provenance for this safety
model; the generated skill does not bundle or invoke them.

| Automation | Behavior | Skill treatment |
|---|---|---|
| Manual build/repair helper | Installs build tools, removes prior `dist/`, `build/`, and `_skbuild/`, builds wheels, then repairs native wheels with auditwheel or delocate. It omits IVF/FlashLib from its `all` list. | Reference-only. It mutates the environment and build outputs and is incomplete as a current all-component release gate. Reproduce the needed package build deliberately. |
| Version bump helper | Rewrites every package `version` field and exact `leann-core==...` pins with platform-specific `sed`. It does not update all minimum constraints, root workspace metadata, lock data, source constants, docs, or changelog. | Excluded. Never run automatically; review a proposed explicit diff instead. |
| Legacy release helper | Calls the version bump, stages all files, commits, pushes, and creates a GitHub release. | Excluded as unsafe for agent execution. It combines too many irreversible stages and uses broad staging. |
| PyPI upload helper | Uploads every package artifact to TestPyPI, or prompts then uploads to production PyPI using Twine. | Excluded. Credentialed external publication; an interactive prompt is not sufficient agent authorization. |
| Hugging Face upload helper | Uploads a local benchmark-data folder to a dataset repository using hub credentials and creates a remote commit. | Excluded. Credentialed external mutation unrelated to wheel verification. |
| Manual release workflow | Requires the latest `main` CI success, validates `X.Y.Z`, rewrites/commits/pushes versions, runs the reusable build matrix, publishes with a PyPI token, creates/pushes a tag, and creates a GitHub release. | Architecture reference only. Its gates inform the checklist, but dispatch is itself an authorized release action. |
| Reusable build workflow | Lints/types, builds core/HNSW/DiskANN/IVF/umbrella across OS/Python rows, repairs native wheels, installs built artifacts, runs pytest, uploads CI artifacts, and performs an Arch Linux install/import/runtime smoke. | Ground truth for release breadth. Local focused checks do not replace the platform matrix. |

## Read-only version gate

Run the bundled checker by resolving it from this sub-skill and passing the
checkout explicitly:

```bash
python scripts/check_package_versions.py --repo-root "$LEANN_CHECKOUT"
python scripts/check_package_versions.py --repo-root "$LEANN_CHECKOUT" --json
```

The checker:

- reads root and `packages/*/pyproject.toml` files;
- excludes the root workspace version from component alignment;
- reports every LEANN component name, exact file, and version;
- fails on component version skew;
- validates internal exact pins and numeric minimum constraints against the
  target package metadata;
- never writes files or resolves/downloads dependencies.

Exit status `0` means the checked metadata is aligned under these rules; `1`
means version/constraint mismatch; `2` means invalid root, malformed TOML, or
missing TOML parser. Python 3.10 requires the optional `tomli` parser; Python
3.11+ provides `tomllib`.

A passing checker is necessary but not sufficient. It does not update or verify
`uv.lock`, source `__version__` constants, changelog/release notes, wheel tags,
ABI compatibility, remote version availability, or published artifacts.

## Safe release-preparation checklist

All steps through local artifact validation are preparation only.

### 1. Identify the candidate

- exact semantic version in `X.Y.Z` form;
- exact commit SHA and branch;
- clean or intentionally scoped working tree;
- list of component distributions being released;
- platform/Python wheel matrix and any intentional exclusions;
- changelog entry and compatibility/migration notes.

Reject a candidate that silently mixes unrelated changes or cannot explain
component skew.

### 2. Verify repository policy

- current Python floor is 3.10;
- recursive submodules are at recorded commits;
- no credential, local path, environment, or generated build tree is staged;
- changelog has a bottom-appended dated entry for a significant release;
- roadmap/completed state matches implementation;
- source version constants and lock metadata are reconciled deliberately;
- the bundled version checker passes after any proposed version edits.

Version edits remain blocked until explicitly authorized. Prefer presenting an
exact patch/diff for review over running the broad bump helper.

### 3. Run quality and focused behavior gates

- Ruff format/lint checks;
- pre-commit with the pinned lint group, inspecting any modifications;
- focused metadata/public API/backend tests selected from the testing guide;
- broader non-live tests when dependencies are complete;
- type checking on core/apps/tests when release scope warrants it;
- exact native regression for every changed backend that can be prepared.

A skipped required backend is a block, not a pass. An optional backend skip must
be listed in release notes/verification status.

### 4. Build clean artifacts

Use isolated build and test environments. Build core before backends that pin or
consume it, then IVF/native backends, then the umbrella. Do not rely on an old
`dist/` glob. For each selected component:

- remove or segregate stale local build output only after confirming the target;
- build wheel/sdist with the intended Python and host toolchain;
- repair native wheels with the platform tool only when producing distributable
  wheels;
- list artifact filenames, sizes, hashes, Python ABI tags, and platform tags;
- run `twine check` locally; this validates metadata, not publication.

The repository's native matrix uses auditwheel on Linux, delocate on macOS, and
delvewheel on Windows. A wheel repaired on one host does not prove another host.

### 5. Install exactly the candidate artifacts

Create a fresh environment with the target Python. Install local core first or
provide a local wheelhouse so internal constraints resolve to candidate wheels,
then install backend and umbrella artifacts. Verify:

```bash
python -m pip check
python -c "import importlib.metadata as m; print(m.version('leann-core'))"
python -c "import leann; print(leann.__file__)"
```

Add direct imports for every shipped backend, registry assertions, public import,
CLI help, and one tiny prepared native behavior case. Ensure tests import from
the clean wheel environment, not the source checkout or an editable package.

### 6. Match CI evidence

The manual release design requires successful CI for the current `main` commit,
then rebuilds packages. Before any dispatch/publish request, confirm:

- the successful CI run belongs to the exact intended SHA;
- lint/type/build/test jobs are complete, not merely queued;
- every expected artifact exists for its matrix row;
- no artifact was copied from another commit/run;
- the version does not already exist remotely unless an idempotent skip policy
  is explicitly approved.

### 7. Stop and request publication authorization

Present:

- candidate version and SHA;
- component/version table and internal constraints;
- tests/builds run, skips, and failures;
- artifact list and hashes;
- target repository/release;
- exact commands/workflow dispatch that would mutate remote state;
- credentials required and rollback limitations.

Only after explicit authorization may a separate release operator perform the
approved stage. Reconfirm before production PyPI, tag push, or GitHub/Hugging
Face release even if TestPyPI was approved.

## Difficult case: skew without mutation

If the checker reports, for example, core/HNSW/DiskANN/umbrella at one version
and IVF/FlashLib components at an older version:

1. report every package file and declared version;
2. inspect internal exact/minimum constraints and intended release set;
3. determine whether the older components are intentionally excluded or must be
   aligned—do not infer intent from permissive `>=` constraints;
4. propose the exact metadata/source constant/lock/changelog changes;
5. propose focused metadata tests and clean wheel installs;
6. stop before version edits, commits, pushes, tags, uploads, or workflow dispatch.

There is no safe automatic fallback that converts observed skew into a chosen
release version.
