# Cross-cutting troubleshooting

Read this reference before changing configuration or retrying a Hub operation.
First identify the package/CLI version, endpoint, repo ID/type/revision, token
source, and whether the action is local, networked, credentialed, paid, or
destructive.

## Import and installation

**Symptom:** `ModuleNotFoundError`, an old `hf` command, or an API argument is
rejected.

- Run `python -c "import huggingface_hub; print(huggingface_hub.__version__)"`
and `command -v hf; hf version` using the same environment.
- Install the base package in that environment, then add only the needed extra:
`oauth`, `mcp`, `torch`, `gradio`, or `hf_xet`.
- Do not assume an extra called `inference` or `test` exists. The `testing`
extra is for repository tests, not application inference setup.
- Re-run the exact subcommand's `--help` after an upgrade; generated CLI
references and generated async/type surfaces are version-specific.

## Authentication and access

**Symptom:** HTTP 401/403, a private or gated repo appears missing, or an
inference provider rejects the request.

- Prefer an existing `hf auth login` or process-scoped `HF_TOKEN`; do not echo
or serialize the token. Use a write-scoped token only for mutations.
- Verify the token source without printing its value. Distinguish Hub tokens
from direct provider API keys and ensure the selected provider accepts the
credential type.
- Confirm the fully qualified namespace/repo ID, singular Python `repo_type`,
endpoint, and revision. A private or gated resource can intentionally look like
not-found without access.
- Stop when authorization scope is unknown. Do not “fix” access by putting a
token in a URL, commit message, log, prompt, or report.

## Repository, revision, and API misuse

**Symptom:** 404/RevisionNotFound, wrong resource type, empty listing, or a
commit is applied to an unexpected branch.

- Use `model`, `dataset`, or `space` in Python; CLI flags and `hf://` prefixes
have their own plural spelling. Pin `revision` when reading or mutating a
non-default ref.
- Inspect `repo_info`/`model_info` and the target ref before mutation. Do not
use `exist_ok=True` as proof that an existing repository has the requested
visibility or settings.
- For a PR, inspect `CommitInfo.pr_revision`, `pr_url`, and `pr_num`; `main`
does not change until merge.
- For a filesystem path, distinguish a repository from a bucket and reject
absolute or `..` paths before materialization.

## Network, timeout, and ambiguous outcomes

**Symptom:** timeout, 429/5xx, connection reset, or a mutation request whose
result is unknown.

- Record status/request ID and whether the server may have accepted the request.
Re-read the resource, commit list, PR refs, or job status before retrying.
- Retry only idempotent reads or a mutation whose idempotence and current
parent/state have been re-established. Use bounded backoff, not an unlimited
loop.
- Set a finite API/CLI timeout. A request timeout is not proof that a remote
upload, job, endpoint update, or inference did not happen.
- For offline work, set `HF_HUB_OFFLINE=1` before Python starts and use
`local_files_only=True`; do not combine offline mode with `force_download=True`.

## Cache, storage, and paths

**Symptom:** cache miss, incomplete snapshot, no space, symlink failure, Xet
warning, or a bucket copy selects the wrong objects.

- Use the storage sub-skill's read-only diagnostic and `scan_cache_dir` before
pruning. A cache ref/tree record is metadata, not proof that every payload is
present.
- Use `dry_run=True` or CLI `--dry-run` before large transfers. `local_dir`
materializes a normal working copy; shared cache paths should be treated as
immutable.
- Check disk space and permissions for both the cache and destination. If
symlinks are unavailable, use the documented no-symlink setting rather than
manually editing cache internals.
- Xet is an optional transfer backend. A missing or failed Xet path does not
necessarily mean ordinary HTTP download is unavailable; follow the specific
error and do not claim Xet acceleration was used without evidence.
- For bucket prefixes and trailing slashes, inspect the complete plan and
reject `logs`/`logs-old` prefix collisions or traversal paths before applying.

## CLI output and destructive actions

**Symptom:** a shell parser receives warnings, JSON is invalid, a command blocks
for confirmation, or a delete has an unexpected target.

- Parse stdout only. Keep stderr separate for warnings, hints, progress, and
errors; select `--format json`, `quiet`, or `agent` only after checking help.
- A format flag does not authorize a mutation. Use `--dry-run`, `--plan`, or a
read-only list, display exact targets, then confirm immediately before apply.
- `--yes` bypasses a prompt but does not make a target safe. Never use it just
to make an unreviewed automation script non-interactive.
- `hf auth token` deliberately prints a secret; never include it in a general
environment diagnostic.

## Optional integrations and hosted resources

**Symptom:** OAuth/MCP/Gradio/torch/serialization import errors, invalid Space
or endpoint configuration, or a Job/Sandbox appears stuck.

- Install the optional extra that owns the surface and re-run a local import or
mocked fixture. Keep `mcp`, `oauth`, `gradio`, and `torch` concerns separate.
- Validate model/card metadata, shard indexes, DDUF entry names, image/command,
accelerator, volumes, secrets, variables, webhook route, and endpoint hardware
locally before a remote call.
- Inspect terminal Job status rather than treating streamed logs as success.
For Spaces and endpoints, wait for a healthy/running state and read logs/state
before retrying. Stop or pause billable resources after use.
- Never load untrusted pickle checkpoints. Prefer safetensors and validate the
index/aggregate key set. DDUF is a constrained archive; reject unsafe entry
names and malformed structure.

## Recovery record

For any unresolved issue, retain only non-secret evidence: package/CLI version,
operation classification, target type/revision, status/error fragment, current
remote/local state, recovery attempted, and the next safe action. Stop rather
than guessing when credentials, ownership, parent SHA, billing, or destructive
intent cannot be established.
