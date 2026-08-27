# Upload, sharing, publishing, and versioning

These operations contact Harbor services or change remote state. Before any
command below, show the exact source path/ID, account or organization, intended
visibility, recipients, tags, overwrite behavior, and expected cost. Confirm
that credentials are present with `harbor auth status`; use `harbor auth login`
only when the user explicitly requests the login flow.

## Upload job results

A local job upload requires both job-level `config.json` and `result.json` and
uploads trial archives. The default for a new upload is private:

```bash
harbor upload jobs/<job> --concurrency 10
harbor upload jobs/<job> --public
harbor upload jobs/<job> --private --org <org> \
  --share-org <org2> --share-user <github-user> --yes
```

`--public/--private` is tri-state on re-upload: no flag preserves existing
server visibility, while an explicit flag changes it. Re-uploading is
idempotent and fills missing trials; it does not change ownership. A partial
upload exits non-zero so the same command can be retried. Inspect the returned
job ID, visibility, owner, share list, and viewer URL. Never make a private job
public merely to make a debug link work; use a deliberate share instead.

`harbor job resume -p jobs/<job> --upload` combines local resume with a Hub
upload/finalization sweep. It is an execution/mutation operation, not an
inspection shortcut. `harbor run --upload` streams trials and also requires the
upload gate; route its execution choices to `run-evaluate`.

## Download jobs, trials, and trajectories

Downloads require authentication and write local files. Check the destination
and collision policy before running:

```bash
harbor job download <job-uuid> --output-dir jobs [--overwrite] [--include-retries]
harbor trial download <trial-uuid> --output-dir trials [--overwrite]
harbor hub trial download <trial-uuid> --trajectory --output-dir trials
```

A job download may reconstruct a job from trial archives when the full archive
is unavailable; read its download manifest and warnings, especially missing
trials. `--include-retries` retains retry history during reconstruction. A trial
trajectory-only download writes just `trajectory.json`; it is not a complete
trial archive and cannot replace artifact/result inspection. After download,
inspect locally with `harbor view <parent>` or `harbor analyze <downloaded-dir>`.
Downloading a task/dataset with top-level `harbor download` is a separate
registry-package workflow and should be treated as a credentialed remote read.

## Share job results

`harbor job share <job-uuid> --org <org> --user <user>` adds access to an
already-uploaded job. It does not replace private/public visibility. Confirm
organization membership, recipient spelling, private-data scope, and use
`--yes` only for the exact reviewed recipients. `hub job shares` is read-only;
use it before and after a share mutation to verify the access list.

## Publish tasks and datasets

Publishing creates or updates registry packages and uploads archives. Validate
locally first with the authoring workflow: task/dataset names and versions,
manifest digests, required files, reward/verifier contract, and intended
included tasks. Then authenticate and show the mutation command:

```bash
harbor publish path/to/task path/to/dataset \
  --tag v1.0 --concurrency 50 --private
harbor publish path/to/dataset --tag v1.0 --public --no-tasks
```

`latest` is always added as a tag. Dataset publishing normally discovers and
publishes local task children and refreshes local digests during upload;
`--no-tasks` prevents that task upload. `--public` affects new packages;
existing package visibility is not silently changed. Publishing a public dataset
may prompt about promoting owned referenced tasks; do not bypass that prompt
without confirming the package graph. Publishing is not the same as uploading
job results and has different package/visibility permissions.

For package access changes, `task/dataset visibility`, `access`, `share`, and
`unshare` are all mutations. Prefer their dry-run/read mode when available and
confirm organization recipients. Maintainer-only registry sync or release
scripts are outside this skill.

## Version inspection and mutable tags

Version reads are safe after access is established:

```bash
harbor version list org/name [--include-yanked] [--limit 50] [--json]
harbor version show org/name@latest --files --tasks --json
```

A version can be resolved by tag, numeric revision, or full `sha256:` digest.
Record package type, visibility, revision, tags, digest, publication time,
yank status/reason, file hashes/sizes, and dataset task references. A yanked
version remains inspectable but should not be used for a new run without an
explicit decision.

`harbor version tag org/name@<revision-or-digest> <tag>` assigns a mutable tag;
use `--force` only when intentionally moving a tag after checking its current
revision. Do not tag a yanked version. Tags are pointers, not immutable
provenance: use a revision or digest in reproducibility records and report the
tag's resolved revision at run time.

## External trace publication

`harbor traces export` without `--push` writes a local dataset. `--push
--repo org/name` publishes to Hugging Face and requires the correct token and
repository approval. OTLP `--endpoint` sends trace data to an external service
and reads auth headers from its environment. Validate output locally first,
exclude private instruction/verifier metadata unless approved, and record the
remote repository/endpoint and resulting revision or response.
