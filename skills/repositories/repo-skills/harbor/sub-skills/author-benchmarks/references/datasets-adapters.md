# Datasets, adapters, and parity preparation

## Dataset composition

A dataset is a versioned collection of task packages. Tasks may appear in more
than one dataset, and a dataset may combine tasks from different adapters. Use
local directories while authoring:

```bash
harbor dataset init "org/dataset-name" --description "..."
harbor dataset init "org/dataset-name" --with-metric
harbor add path/to/task
harbor add path/to/tasks --scan
harbor add path/to/another-dataset/dataset.toml
harbor remove "org/task-name"
harbor sync
```

Do these commands in a disposable/local dataset directory and inspect the diff.
`add`, `remove`, and `sync` change `dataset.toml`; they are not read-only
queries. `add` can resolve a local task, a local manifest, a registered task,
or a registered dataset. Registry resolution is an external operation and
requires access only when the selected ref is remote.

## `dataset.toml` manifest

The minimal current shape is:

```toml
[dataset]
name = "org/dataset-name"
version = "1.0.0"
description = "A collection of related tasks"
authors = [{ name = "Author" }]
keywords = ["benchmark", "programming"]

[[tasks]]
name = "org/task-a"
digest = "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

[[files]]
path = "metric.py"
digest = "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
```

The manifest model enforces:

- dataset and task names in `org/name` format;
- task digests as `sha256:` plus exactly 64 lowercase hexadecimal characters;
- dataset file paths as simple filenames with no directory separators;
- non-empty dataset versions when specified.

Task references pin the task archive content. File references pin dataset-level
files such as `metric.py`. A file digest may be blank during local development
and is refreshed by publishing; `harbor sync` is useful when you want a local
manifest diff before publishing. The dataset content hash incorporates sorted
task digests and, when present, sorted `path:digest` file pairs. Duplicate task
references can be counted separately; use unique task checks when reviewing a
manifest.

A local dataset can be evaluated by path, but execution is out of scope here:

```bash
harbor run -p path/to/dataset ...
```

Do not use a registry `-d` reference as a pre-publish validation shortcut. A
registry ref exists only after a package has been published.

## Adapter scaffold and generated task contract

An adapter converts an external benchmark's instructions, environment, tests,
and solutions into Harbor task directories. Scaffold the code package:

```bash
harbor adapter init my-adapter --name "My Benchmark"
```

The intended adapter package contains:

```text
my-adapter/
├── pyproject.toml
├── README.md
├── adapter_metadata.json
├── parity_experiment.json
├── run_my-adapter.yaml
└── src/my_adapter/
    ├── __init__.py
    ├── adapter.py
    ├── main.py
    └── task-template/
        ├── task.toml
        ├── instruction.md
        ├── environment/Dockerfile
        ├── solution/solve.sh
        └── tests/test.sh
```

The conversion entrypoint should support:

- `--output-dir` — deterministic destination for generated tasks;
- `--limit` — cheap bounded development generation;
- `--overwrite` — explicit replacement of existing outputs;
- `--task-ids` — focused reproduction/debugging;
- `--split parity` when a representative parity subset is supported.

Every generated task must include at least `task.toml`, `instruction.md`, an
environment definition, `solution/solve.sh` (when an oracle is available), and
`tests/test.sh`. The generated `[task].name` is required even when the task
folder has a name. Derive it from a stable upstream identifier, lowercase and
sanitize spaces/slashes/special characters to hyphens, and avoid leading or
trailing separators. If upstream has no stable ID, sort deterministically and
mint a stable fallback such as `dataset-1`; never use random IDs or iteration
order from an unordered source.

Set `schema_version = "1.4"` in generated task configs and set the package
version under `[task].version`; do not confuse the two. Preserve instruction,
environment, test, solution, timeout, resource, and network semantics from the
source benchmark. Any prompt modification must be applied symmetrically to the
original and Harbor sides and documented.

The adapter README is consumed by automation in many repository workflows.
Keep its generated top-level section order, fill all required fields, and put
caveats in its Notes section or metadata notes rather than inventing sections.
Do not publish or open a PR as part of local authoring.

## Bundled structural validator

Use the self-contained helper for generated adapter directories:

```bash
python scripts/validate_adapter.py --help
python scripts/validate_adapter.py path/to/adapter
python scripts/validate_adapter.py --json-output /tmp/adapter-report.json path/to/adapter
```

The helper accepts one or more relative/absolute directories and does not
import Harbor or assume a checkout. It checks required metadata/code files,
new `src/<package>/` and legacy flat layouts, `task-template/`, required
`task.toml` fields, reward path hints, parity/metadata JSON shape, README
sections, PR-link shape, cross-file size consistency, canary strings, and the
singular `parity_experiment.json` spelling. A legacy `adapter.py` +
`run_adapter.py` layout is a warning, not an automatic success claim. A
missing template `[task].name`, a plural `parity_experiments.json`, or other
structural error produces a non-zero exit. Treat warnings as review items.

The validator is a preflight check, not an oracle run, parity run, code review,
or registry publish check. Keep its report outside the runtime skill tree.

## Oracle and parity preparation

When reference solutions exist, first use a tiny local generation and a
non-network structure/schema check. Only an explicitly approved evaluation
workflow should run Oracle in a container. A target of 100% Oracle reward is a
solvability signal; a failed Oracle may indicate an adaptation, environment,
verifier, or solution defect. Do not use a model-generated solution as proof of
parity.

Before parity experiments, freeze and record on both sides:

1. Harbor/source revision or package version;
2. agent name and version;
3. exact dated model identifier;
4. installation script and entry command;
5. tools, arguments, temperature/max tokens, turn limits, and timeouts;
6. prompt modifications and working directory;
7. task subset and task ordering;
8. environment image/dependencies and relevant environment variables.

Required order is symmetric: a 5–10 task sanity subset on both sides, one full
run on both sides, then three runs on both sides. Do not complete all repeats
on one side before testing the other. Obtain coordination/approval before
incurring model or cloud cost.

A parity result matches when the run ranges overlap:

```text
max(original_runs) >= min(harbor_runs)
AND max(harbor_runs) >= min(original_runs)
```

Report scalar uncertainty as sample SEM, not sample standard deviation:

```text
SEM = sqrt(sum((x - mean(x))^2) / (n * (n - 1)))
```

Use at least two runs per side (`3+` preferred). Preserve raw run arrays and
report the same units. A non-overlap is an adaptation-error hypothesis until
logs and trajectories show otherwise. First resolve crashes/timeouts/build or
verifier errors; then inspect task-level disagreements, high-variance items,
configuration symmetry, and agent wrappers before scaling repeats.

## Files to keep separate from this skill

Parity result JSON, generated task datasets, logs, review reports, API
responses, and test cases are artifacts of a particular authoring run. Store
them in the caller's artifact/report roots, not beside the bundled runtime
references. Credentialed upload/publish and full outcome analysis belong to
sibling workflows.
