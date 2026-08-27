# Registry references and publishing boundaries

## Names, versions, and digests

Harbor distinguishes four related identifiers:

- task package: `[task].name = "org/task"`, with package version under
  `[task].version`;
- dataset package: `[dataset].name = "org/dataset"`, with version under
  `[dataset].version`;
- task content digest: `sha256:<64 lowercase hex>` for an archived task;
- dataset content hash/tag: a manifest snapshot resolved by a tag or digest.

`schema_version = "1.4"` identifies the task config format; it is not a package
version. Keep task names stable and unique within the intended dataset. A
changed task archive creates a new content digest even if the package name is
unchanged. A changed dataset-level metric file also changes the dataset content
hash.

## Local manifest operations

Initialize and inspect locally:

```bash
harbor dataset init "org/dataset" --description "..."
harbor dataset init "org/dataset" --with-metric
harbor add path/to/task
harbor add path/to/tasks --scan
harbor add "org/other-task@latest"       # remote resolution; explicit gate
harbor remove "org/other-task"
harbor sync
harbor sync --upgrade                    # remote upgrade; explicit gate
```

Review the resulting `dataset.toml` after every mutating command. `add` may
merge a local task, manifest, or registered package. `remove` removes task
references from the local manifest; it does not delete a remote package.
`sync` refreshes digests for local tasks and metric files. `--upgrade` may
resolve newer remote versions and should be used only with an intentional
upgrade decision.

A local metric is added by filename from the dataset directory:

```bash
harbor add metric.py
```

The manifest's `[[files]]` path must remain a simple filename. Use a temporary
fixture to check digest changes rather than modifying a production dataset.

## Read-only versus mutating operations

Safe authoring checks:

```bash
harbor --version
harbor publish --help
harbor download --help
harbor dataset list --help
harbor task download --help
```

Local, reviewable operations:

- task/dataset scaffolding;
- `add`, `remove`, and `sync` against a disposable local directory;
- manifest/model parse and content-hash checks;
- the bundled adapter structural validator.

Credentialed or externally mutating operations:

- `harbor auth login` / status and organization access changes;
- `harbor publish` and package uploads;
- public/private visibility changes;
- share/unshare and Hub/package access mutations;
- registry downloads when they are not already cached;
- any external dashboard, cloud, storage, or database operation.

Do not run these from an authoring validation step. Surface the exact command,
package name, tag, visibility, and expected scope to the caller for approval.

## Publishing a local package

The current publisher accepts one or more task or dataset directories:

```bash
harbor publish path/to/dataset --tag v1.0 --public
harbor publish path/to/dataset --tag parity --no-tasks
```

`latest` is always applied. `--public`/`--private` affects new package
visibility; existing package visibility is not silently changed. For a dataset,
publishing normally publishes tasks in its directory too; `--no-tasks`
prevents that. `--concurrency` controls upload parallelism and should be kept
bounded for a controlled rollout.

The publisher preflights the task config, requires a `[task]` name and an
environment directory, validates the task structure, collects publishable files,
computes a deterministic content hash, builds an archive, uploads it, and
registers the version. Task package files include config/instruction/readme,
environment/tests/solution/steps, and other supported task files after ignore
filtering. Never include caches, credentials, API tokens, model output, or
unreviewed generated artifacts in the package.

Dataset publication refreshes local task/file digests as part of upload. Use
`harbor sync` when you need to inspect that refresh first. A failed or skipped
upload is not a successful publication claim; inspect the command result and
registry state only in the credentialed publishing workflow.

## Tags and registry references

A release may receive tags such as:

- `latest` — always added by publishing;
- `v1.0`, `v1.1`, `v2.0` — explicit version snapshots;
- `verified`, `lite`, or benchmark-defined split tags;
- `parity` — a deliberately generated parity subset.

Request tags in the release/PR process, and keep the generated `--split parity`
subset distinct from the full adapter output. A registry reference commonly
looks like:

```text
org/dataset@v1.0
org/task@latest
org/task@sha256:<64-hex-digest>
```

The executable `harbor run -d`/`-t` behavior is owned by `run-evaluate`; this
reference only defines how authoring names and refs are formed. Pre-publish
checks should use a local `-p` path, not a registry ref that may point to an
older snapshot.

## Download and git-backed datasets

The current download command can export a task or dataset to a local directory
or use content-addressable cache mode:

```bash
harbor download "org/task@latest" --output-dir path/to/export --export
harbor download "org/dataset@v1.0" --output-dir path/to/cache --cache
```

`harbor task download` and `harbor dataset download` provide focused wrappers.
Git-backed datasets can resolve a registry manifest from an explicitly selected
repository/ref. These are data acquisition operations: require network/auth
approval, pin a ref for reproducibility, and inspect downloaded files before
adding or running them. Never treat an unpinned remote download as benchmark
provenance.

## Publishing handoff

Before handing to a publishing workflow, provide:

1. local task/dataset paths and package names;
2. parsed manifest summary and task/file counts;
3. content/digest changes and requested tags;
4. visibility choice and whether tasks should be included;
5. adapter/oracle/parity evidence and known omissions;
6. an explicit statement that credentials and remote mutation are still gated.

After publication, registry inspection, upload result analysis, version
comparison, and outcome sharing belong to `analyze-publish`. If the package
needs custom framework/plugin code, route it to `integrations`.
