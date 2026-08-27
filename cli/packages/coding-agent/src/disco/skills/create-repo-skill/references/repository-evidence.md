# Repository Evidence Discovery

## Purpose

Read this reference before extracting repo knowledge into a generated skill. The goal is to automatically discover which repository directories and files should inform the skill, instead of asking the user to list them manually.

## Build an Evidence Map First

Read the repo structure before extracting skills. First build a short evidence map that identifies which directories and files will be used for extraction. Do not ask the user to preselect these directories unless the repo is so large or ambiguous that automatic discovery cannot distinguish project code from vendored or generated material.

Also build an explicit exclusion map for directories that should stay out of
later extraction context, such as vendored code, generated outputs, build
artifacts, local environments, large caches, and review/test artifacts. The
goal is to keep subagent extraction focused on evidence that can improve the
generated skill.

Record the evidence map in working notes before planning sub-skills:

```text
Evidence source | Why it matters | Planned use
src/package_name/ | canonical source root from pyproject package_dir | verify APIs, signatures, config objects, CLI modules
docs/ | public guides and install docs | workflow references and troubleshooting
examples/ | runnable user workflows | adapt smoke tests and recipes into skill scripts/references
scripts/ | repo-maintained automation | wrap safe reusable scripts inside generated skill
tests/ | behavior and edge-case evidence | confirm defaults, errors, and expected outputs
skills/*/SKILL.md | existing repo-local agent guidance | follow compatible structure and reuse validated guidance in the new self-contained skill
```

Also build a native test/example candidate map before planning sub-skills. This
map records repo-owned examples, tests, notebooks, CLI snippets, smoke scripts,
fixtures, and golden files that can later serve as ground-truth verification
after the generated skill is complete and integrated. Do not run those native
cases during repository structure analysis. The purpose here is to preserve
traceability from real repo behavior to the later skill coverage and validation
plan.

Build a separate source script inventory before planning sub-skills. This
inventory covers repo-owned `scripts/`, `tools/`, `bin/`, runnable examples,
workflow helpers, conversion utilities, validators, launchers, and smoke-test
programs. For every useful script, decide whether the generated skill should:

- `copy`: preserve a small, safe, self-contained script with only path/import
  normalization.
- `adapt`: extract or simplify reusable logic into a bundled skill helper with
  safe defaults.
- `wrap`: create a bundled helper that calls a public package CLI/API instead
  of depending on the source checkout.
- `reference-only`: describe the workflow in a nearby reference because the
  original script is too large, environment-specific, or not safe to run.
- `exclude`: leave it out because it is generated, vendored, destructive,
  credential-bound, unrelated to selected workflows, or otherwise not useful.

Do not use `reference-only` merely because prose is easier. If a repo-maintained
script is useful to future agents and can reasonably be copied, adapted, or
wrapped safely, plan a bundled script under the root `scripts/` directory or the
nearest owning `sub-skills/<id>/scripts/` directory.

Use this shape in working notes or under the review/test artifact directory
when practical. Classify backend needs now because environment preparation
happens before native cases run:

```text
Native artifact | Workflow/capability | Safety class | Backend requirement | Backend criticality | CPU substitute | Dependency variant | Hardware prerequisites | Verification expectation | Candidate command | Expected signal | Planned skill owner
examples/infer.py | GPU inference | tiny-fixture-runnable | cuda | required | none | [cuda] + repo-documented torch wheel | NVIDIA GPU, compatible driver/wheel, sufficient VRAM | backend smoke + native example | python examples/infer.py --tiny-fixture | exits 0 and uses CUDA | sub-skills/inference
tests/test_cli.py | CLI errors and flags | safe-runnable | any | alternative | full | base | none | native test | pytest tests/test_cli.py -q | selected tests pass | sub-skills/cli
notebooks/train.ipynb | training workflow | skip-expensive | cuda | optional | partial | [train,cuda] | compatible GPU plus training data | documentation/assertions only unless approved | none | documents full training flow, not executed | sub-skills/training
```

Use these backend fields consistently:

- `Backend requirement`: `cpu`, `cuda`, `rocm`, `mps`,
  `accelerator-specific`, or `any`. Name the vendor/runtime in hardware notes
  when `accelerator-specific` is used.
- `Backend criticality`: `required` when the selected capability cannot be
  truthfully validated without that backend; `optional` when it is an additive
  capability that may remain explicitly unverified; `alternative` when another
  backend can validate the same selected behavior.
- `CPU substitute`: `full`, `partial`, or `none`. A CPU import check is not a
  substitute for a CUDA/ROCm/MPS runtime check unless evidence shows equivalent
  behavior.
- `Dependency variant`: the exact extra, requirements file, wheel index,
  package variant, or toolkit needed for the candidate.
- `Hardware prerequisites`: device family, driver/runtime, compute capability,
  memory, system service, compiler, or vendor tooling required to run it.
- `Verification expectation`: distinguish package/backend smoke checks needed
  while preparing the environment from native tests/examples that must wait
  until the generated skill is fully integrated.

After the extraction scope is confirmed, derive a backend verification plan
from all candidates owned by included workflows. The plan must identify every
required backend, optional/alternative backends, CPU substitution evidence,
dependency variants, hardware probes, the minimum environment set, preparation
smoke checks, final native cases, and the blocking consequence of an unavailable
required backend. Usually one GPU-capable environment can also cover CPU cases;
use separate prefixes only when backend variants conflict or an independent CPU
fallback claim also requires verification.

Use this shape for the source script inventory:

```text
Source script | Workflow/capability | Decision | Bundled target | Rationale | Safety/check
scripts/validate_data.py | data validation | adapt | sub-skills/data-preparation/scripts/validate_data.py | reusable schema checks, remove repo-local paths | parser + tiny invalid fixture
tools/export_model.py | model export | wrap | sub-skills/export/scripts/export_model.py | expose public package API with safer args | --help check
scripts/download_weights.sh | setup | reference-only | sub-skills/setup/references/troubleshooting.md | network and external storage side effects | document skip-network
scripts/dev/release.py | maintainer release | exclude | none | maintainer-only and mutates release state | not selected
```

Safety classes should be conservative:

- `safe-runnable`: short, deterministic, no network, no credentials, no large
  downloads, no destructive writes, no long training, and compatible with the
  prepared inspection environment.
- `help-only`: safe to run only for `--help`, parser import, version output, or
  dry-run style checks.
- `tiny-fixture-runnable`: safe only after creating or using a tiny fixture.
- `skip-network`: requires network access or model/data downloads.
- `skip-gpu-or-hardware`: requires unavailable GPU, accelerator, service, or
  system dependency.
- `skip-credentials`: requires API keys, private tokens, accounts, or private
  datasets.
- `skip-expensive`: likely long-running, benchmark-scale, training-scale, or
  memory-heavy.
- `skip-unsafe`: destructive, mutates external state, deletes data, rewrites
  repo state, or performs irreversible side effects.
- `skip-unknown`: not enough information to run safely.

`skip-gpu-or-hardware` is a safety/execution state, not permission to erase a
backend requirement. If the candidate is `required` with `CPU substitute:
none`, carry it into the backend verification plan as a blocking requirement.
If it is `optional`, record the unverified capability without blocking the CPU
scope. If it is `alternative`, name and verify the selected equivalent backend.

The native candidate map is an input to sub-skill planning, whole-skill
integration, and final verification. It is not public runtime skill content and
must not make the generated skill depend on the original repo checkout.

After the initial include/exclude evidence map, native test/example candidate
map, and backend verification plan are ready, ask the user whether the analysis
is reasonable before planning sub-skills. Keep the question concise, but include
enough detail for the user to intervene: the main included/excluded directories,
ambiguous paths, required/optional backend decisions, proposed environment set,
and native examples/tests likely to become final verification candidates. If
the user changes directories, candidates, backend criticality, or source
scripts, update all affected maps and the environment plan before continuing.

## Start from Metadata and Top-Level Structure

Inspect:

- Package metadata: `pyproject.toml`, `setup.py`, `setup.cfg`, `MANIFEST.in`, `requirements*.txt`, lockfiles, `tox.ini`, `noxfile.py`, CI workflows such as `.github/workflows/*`, and documented dependency files.
- Root docs: `README*`, `CHANGELOG*`, `CONTRIBUTING*`, `LICENSE*`, release notes, and public install guides.
- Public CLI or service metadata: console entry points, `__main__.py`, `cli.py`, `commands/`, `bin/`, shell completions, config schemas, and service launch scripts.
- Existing repo skills: `skills/` and nested skill directories with `SKILL.md`, when present. Exclude `skills/tests/` because it is the review/test artifact area, not an existing generated skill.

## Capture Repository Snapshot

Before writing the generated skill, capture a publish-safe repository snapshot
for `references/repo-provenance.md`. This snapshot lets future agents decide
whether the skill is aligned with the current repo or should be refreshed.

When the repository is a Git checkout, collect:

- Current commit: `git rev-parse HEAD`.
- Current branch: `git branch --show-current`, when available.
- Exact tag: `git describe --tags --exact-match HEAD`, when available.
- Working tree state: `git status --short`.
- Relevant package version from package metadata or installed-package
  inspection, when available.

If the working tree is dirty, record that the skill was generated from a dirty
checkout and list only relative changed paths or a short count summary. A dirty
checkout means the commit alone is not a complete baseline.

If the repo is not a Git checkout, record `vcs: none` and use the best available
package version, release archive name, or user-provided source identifier. Do
not invent a commit.

Do not put local absolute paths, conda prefixes, Python executables, private
cache paths, or `pip show Location` values into public provenance. Record repo
evidence paths relative to the repository root. Include a remote URL only when
it is clearly public or the user explicitly wants it included; otherwise write
`remote_url: omitted-private-or-unknown`.

## Locate Source Roots

Treat source roots as essential evidence. The source code is the most reliable reference for public APIs, signatures, options, object relationships, runtime constraints, and confusing edge behavior. Use documentation, examples, and tests to learn intent and workflows, but use source code plus installed-package inspection to confirm API facts.

Common Python source root patterns:

- `src/<package_name>/`, `src/<normalized_repo_name>/`, and other `src/*` package directories.
- `<package_name>/`, `<normalized_repo_name>/`, and other top-level import packages containing `__init__.py` or namespace package files.
- `lib/`, `libs/`, `python/`, `packages/*/src/`, `packages/*/<package_name>/`, `projects/*/src/`, and monorepo package directories.
- Module directories that match package metadata, entry points, or public imports even if their names differ from the repository name.
- Important implementation-adjacent directories such as `configs/`, `conf/`, `config/`, `schemas/`, `templates/`, or `assets/` when the source imports or validates them.

## Discover Workflow and Documentation Sources

Common useful names:

- Documentation and guides: `docs/`, `doc/`, `documentation/`, `guide/`, `guides/`, `site/`, `website/`, `website/docs/`, `mkdocs.yml`, `readthedocs.yml`, `sphinx/`, `tutorials/`, `cookbook/`, and `recipes/`.
- Examples and runnable workflows: `examples/`, `example/`, `samples/`, `sample/`, `demos/`, `demo/`, `notebooks/`, `notebook/`, `colab/`, `scripts/`, `tools/`, `bin/`, `recipes/`, `experiments/`, and files whose names include workflow terms such as `train`, `infer`, `inference`, `predict`, `evaluate`, `eval`, `serve`, `deploy`, `finetune`, `preprocess`, or `convert`.
- Tests and behavior evidence: `tests/`, `test/`, `testing/`, `integration/`, `e2e/`, `benchmarks/`, `benchmark/`, `examples/tests/`, fixtures, golden files, and snapshot data.
- Configuration and data-format evidence: `configs/`, `conf/`, `config/`, `examples/configs/`, `templates/`, `schemas/`, `data/`, `datasets/`, fixture directories, and documented sample input/output files.
- Existing skills: `skills/*/SKILL.md`, `skills/*/references/`, and `skills/*/scripts/`, excluding `skills/tests/`.

If the user supplied specific reference directories, merge them into the evidence map rather than limiting extraction to only those directories.

If automatic discovery finds no docs, examples, tests, scripts, or obvious source roots, explicitly report the missing category and continue with the installed package, package metadata, and any source files that can be identified.

## De-Prioritize Noise

Ignore or de-prioritize generated, vendored, build, and environment directories unless package metadata explicitly points to them:

- `.git/`, `.venv/`, `venv/`, `env/`, `site-packages/`, `node_modules/`
- `dist/`, `build/`, `.tox/`, `.mypy_cache/`, `.pytest_cache/`, `__pycache__/`
- Generated docs output, downloaded model/data caches, and large binary artifacts

For each candidate evidence directory, sample representative files before reading deeply. Prioritize files that expose public workflows, APIs, CLIs, data formats, configuration, and errors.

## Use Evidence Correctly

Prefer existing documentation and tests for intended behavior. Use source code to resolve gaps or confirm details. Use the installed package to verify live import behavior, signatures, and runtime facts before writing generated skill claims.

Treat repo docs, examples, notebooks, and scripts as source material for the generated skill. Do not merely summarize them into `SKILL.md`; decide which parts should become bundled reference files, which examples should become bundled reusable scripts, and which details are unnecessary. Useful repo scripts should normally become bundled scripts when they are small and safe enough to copy, adapt, or wrap; prose-only extraction is acceptable only with a recorded reason.

Treat native examples and tests differently in two phases:

- During extraction, use them as evidence and candidate ground-truth cases.
  They should influence coverage planning, bundled helper design, and
  troubleshooting depth.
- After all sub-skills are generated and integrated, use the safe selected
  subset as final native verification cases through
  `verify-repo-skill`. At that point, compare the native result
  against the generated skill's routes, references, scripts, and claims.

Never tell future agents to run original repo examples or tests as part of the
runtime skill unless the generated skill is explicitly a maintainer skill for
the same checkout and the instruction is clearly scoped to repo development.
For public repo-specific runtime skills, original examples/tests remain
evidence and verification artifacts; practical reusable logic must be copied,
distilled, adapted, or wrapped inside the generated skill tree.
