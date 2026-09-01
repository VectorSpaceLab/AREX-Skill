# Hosted compute and integration troubleshooting

Use this page after identifying the surface and whether the failure is local,
credentialed, networked, or billable. Do not “fix” a remote failure by
repeating a mutation blindly: inspect the authoritative state, capture the
status/message, and retry only after changing one validated input.

## Fast diagnosis

```bash
python -c "import huggingface_hub; print(huggingface_hub.__version__)"
python -c "import importlib.util; print({n: bool(importlib.util.find_spec(n)) for n in ['torch','safetensors','gradio','authlib','tensorboard']})"
hf jobs --help
hf sandbox --help
hf spaces --help
hf webhooks --help
```

Use the extra matching the requested surface rather than installing every
optional dependency. `oauth` supplies OAuth/session/Authlib dependencies;
`gradio` supplies the Gradio-backed webhook server; `torch` supplies PyTorch
and `safetensors` supplies safe model serialization; `tensorboard` or
`tensorboardX` supplies the summary writer. There is no dedicated TensorBoard
extra in this package version, so install one of those writer dependencies in
the same interpreter used by the application. The package itself should still
import when optional modules are absent. If an import error names a missing
extra, install that extra and repeat the import check. Do not mistake a
CUDA-capable host for proof that torch or a particular CUDA wheel is installed.

## Jobs and scheduled Jobs

| Symptom | Likely cause | Recovery |
|---|---|---|
| Job is `ERROR` before `RUNNING` | Image cannot be pulled, command executable is missing, or the accelerator/resource is unavailable | Inspect `JobInfo.status.message`, verify the image tag and argv locally, choose a flavor from `list_jobs_hardware`, and rerun only with explicit authorization. |
| “invalid image” or pull failure | Malformed registry/image tag, private registry, or unsupported Space-image form | Use a known public image, or ensure the required registry/Space access exists. Do not put registry credentials in labels or source. |
| Command appears to do nothing | `command` was passed as one incorrectly quoted argv element, or the image lacks the executable | Use `command=["python", "-c", "print('ok')"]`; preserve argv boundaries. For shell operators, deliberately invoke `sh -lc` or use the documented shell-capable wrapper. |
| Invalid accelerator/flavor | Flavor is misspelled, unavailable, incompatible with the image, or not permitted by billing/resource group | Query `api.list_jobs_hardware()`, select an exact `name`, verify the image's runtime, namespace/resource group, and payment/grant. Do not infer pricing from an old table. |
| Job times out | Default 30-minute limit or too-small explicit timeout | Set `timeout` as seconds or `"5m"`/`"2h"` with execution margin; distinguish a client wait timeout from the server Job timeout. |
| Wait never returns or returns unexpectedly | Non-positive poll interval, stale namespace, or a terminal failure | Check `namespace`, use positive `poll_interval`, and handle `COMPLETED`, `CANCELED`, `ERROR`, and `DELETED`. `wait_for_job` returns a failed final record; check its stage. |
| Logs are empty or stream errors | Job is still scheduling, build failed, SSE keep-alive/timeout, or Job ended | Use `follow=False` to drain buffered output, `tail` to bound output, inspect Job status, then retry logs. Do not treat an empty stream as successful execution. |
| Volume rejected or mount collision | Unknown type, bad source/revision, non-absolute mount path, read/write mismatch, or duplicate mount path | Construct `Volume` with `bucket`/`model`/`dataset`/`space`, absolute `mount_path`, and an explicit revision/read-only policy. Test `to_dict()`/`to_uri()` locally; use read-only input mounts. |
| Local volume sync uploads unexpected data | Source resolves to a broad directory or includes credentials/cache files | Review the directory, use a narrow fixture/output path, and exclude secrets. `sync_job_volume` and `sync_bucket` are networked side effects. |
| SSH/exposed URL unavailable | `ssh`/`expose` was not requested, access is insufficient, port is not listening, or the Job is not `RUNNING` | Inspect `status.ssh_url`/exposed URLs, require the proper namespace access and registered key, and confirm the process binds the expected port. |
| Scheduled trigger returns 409 | An instance is running and `concurrency=False` | Inspect the scheduled record and the last Job; wait or enable concurrency only as an intentional remote configuration change. |
| Schedule rejected | Unsupported alias or malformed cron expression | Validate locally against supported aliases (`@hourly`, `@daily`, etc.) or a known cron parser. Keep `suspend=True` for an explicitly approved initial create when possible. |
| Labels disappeared | Label update replaces all user labels | Read current labels, merge the desired set in memory, and submit the full replacement map. Never put secrets in labels. |
| Job appears in a different owner | Namespace was implicit or token identity changed | Pass `namespace` explicitly and confirm `whoami`/token scope before creating or listing. |

Never use `run_job`, scheduled create/trigger/delete, log-follow on a paid
long-running Job, or volume sync as a “smoke test.” Mock the HTTP response and
assert the generated payload first. Cancel an explicitly authorized orphan and
then inspect its terminal state.

## Sandboxes and pools

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Sandbox.create` cannot become ready | Image lacks `/bin/sh`, startup download/network failed, port unavailable, or Job terminated | Use an image with `/bin/sh`, inspect the underlying Job status/logs, verify the requested flavor and network, and check that the client attempted cleanup. Recreate only after confirming no billable orphan remains. |
| `SandboxError` says not running/not a sandbox | Wrong id, wrong namespace/token, terminated Job, or a normal Job passed to `Sandbox.connect` | Recheck the exact sandbox id and owner; `Sandbox.connect` requires a running sandbox label. Do not convert an arbitrary Job into a Sandbox by guessing. |
| “connection lost while running command” | In-job server died, idle timeout fired, network interruption, or command killed the server | Inspect `sbx.processes()`, reconnect if the sandbox remains running, and use `check=False` only for expected command failures—not transport loss. |
| Nonzero command raises `SandboxCommandError` | Command itself failed | Read attached `exit_code`, `stdout`, and `stderr`; use an argv list or explicit `shell` mode and correct the command. `check=False` is useful for controlled probing. |
| Shell mode `ValueError` | String/list and `shell` disagree | String + `shell=True` for shell syntax; list + `shell=False` for direct argv. A list element is not automatically parsed as a shell command. |
| Files cannot be read/written | Path is outside the sandbox scope, parent is missing, or the sandbox died | Use `mkdir`/parent paths, validate with `exists`/`stat`, and reconnect. Treat downloaded files as untrusted. |
| Background process is still billing | It was started with `background=True` and never killed; idle timeout only applies when no process is running | List `processes()`, kill the process, close the sandbox, and inspect Job state. Foreground-only options do not apply to background processes. |
| `proxy_url_for` gives connection failure | Inner server is not listening on the requested port/socket, wrong scheme/path, or missing `proxy_headers` | Dedicated mode binds TCP on loopback; pooled mode uses `$SBX_PROXY_DIR/<port>.sock`. Start the server in background, use the exact port, and send `proxy_headers`. |
| Pool exceeds expected cost/hosts | `sandboxes_per_host` too small, `warm_up` starts hosts immediately, or `max_hosts` is unset | Set a capacity/cost ceiling, pre-warm only intentionally, and close/delete the pool. A pool is CPU-only and does not provide dedicated secret isolation. |
| Pooled sandbox rejects `volumes`/secret expectation | Volumes are host-level and `SandboxPool.create` has no per-sandbox volume or encrypted-secret channel | Mount volumes at pool host boot if appropriate; use per-sandbox plain `env` only for non-sensitive values, or choose dedicated `Sandbox.create`. Never forward HF tokens to untrusted code. |
| `SandboxPool.connect` cannot find a host | Pool was killed/idle-timed-out, stale cache, wrong pool name/namespace, or all hosts are full/dead | Confirm the pool id/namespace, let label discovery run, remove the stale local handle/cache, and create a new pool only after checking for live hosts. A connected pool must not resurrect a dead pool. |
| Closing a connected pool kills work | Code used explicit host deletion instead of `close()` semantics | A pool from `connect()` does not own shared hosts; close releases local clients. Use explicit pool deletion only when authorized to terminate shared hosts. |

Sandbox features are experimental and isolation is best-effort. For mutually
hostile code or GPU work, choose a dedicated sandbox; for cooperative CPU fanout,
a pool can amortize host cost.

## Spaces and runtime configuration

| Symptom | Likely cause | Recovery |
|---|---|---|
| Space is `CONFIG_ERROR`/`NO_APP_FILE` | Missing app file, malformed card/config, wrong SDK, or invalid Space metadata | Fetch build logs, inspect the local file set and card frontmatter, confirm `space_sdk`/app entry point, then upload a corrected commit. |
| Space is `BUILD_ERROR` | Dependency/build command failure or incompatible SDK/runtime version | Call `fetch_space_logs(build=True)`, reproduce dependency installation locally, pin compatible versions, upload a minimal fix, and use `wait_for_space`. |
| Space is `RUNTIME_ERROR`/stuck `APP_STARTING` | App crash, wrong port/entrypoint, missing variable/secret, or resource pressure | Read run logs, verify environment names and app port, check `runtime.raw`, correct one input, restart only with authorization, and wait for a terminal stage. |
| Requested hardware is not current | Hardware change is asynchronous or unavailable | Compare `requested_hardware` and `hardware`, poll `wait_for_space`, check hardware catalog/permissions/billing, and do not assume the requested flavor is active. |
| Hardware request rejected | Invalid flavor, no grant/payment, wrong owner, or static Space | Use `list_spaces_hardware`, an exact `SpaceHardware` value, correct namespace/permissions, and an eligible billing setup. Static Spaces do not use the same runtime controls. |
| Storage request rejected or does nothing | Invalid tier, deprecated storage API, unsupported Space, or missing permission | Prefer `set_space_volumes`/`delete_space_volumes` for new code; use exact `SpaceStorage` only for the deprecated compatibility API. Inspect runtime after the change. |
| Secret value cannot be read back | This is intentional write-only behavior | List only keys/metadata, rotate by writing a replacement, and never attempt to recover the old value through `get_space_secrets`. |
| Space app cannot see a setting | Key typo/case mismatch, restart not complete, or value stored in the wrong surface | Compare exact variable names with the app's expected environment, reread `get_space_variables`, wait for restart/build, and use a Space secret for sensitive values. |
| Secret/variable write fails | Invalid repo id, no write permission, invalid key/value, or remote auth failure | Validate strings locally, pass explicit token/namespace, inspect the HTTP error, and do not retry a secret write without knowing whether the first request succeeded. |
| Pause/restart fails | Not owner, static Space, wrong id, or paid-resource policy | Inspect runtime and permissions. `pause_space` is different from automatic sleep; `restart_space(factory_reboot=True)` is a destructive/rebuild-like choice and must be explicit. |
| Space keeps billing | Upgraded runtime is running or a host/replica is warm | Pause or downgrade only after confirming user intent; set sleep time where supported and inspect runtime after the operation. |

A remote Space change can restart the app. Treat the sequence as a state
machine: read current runtime → validate requested setting → make one
credentialed mutation → poll intermediate stages → inspect logs and resulting
runtime → record the outcome.

## Webhooks and OAuth

| Symptom | Likely cause | Recovery |
|---|---|---|
| Webhook returns 401 | `x-webhook-secret` header is absent | Send the exact configured header from the Hub integration; do not disable the server secret just to make a test pass. |
| Webhook returns 403 | Header secret differs from `webhook_secret`/`WEBHOOK_SECRET` | Rotate/configure both sides consistently, restart the server if its environment changed, and verify with a local mocked request. |
| Webhook is open to everyone | `WebhooksServer` was created without a secret | Treat this as a security failure. Set `webhook_secret` or `WEBHOOK_SECRET` before exposing the route. The warning is intentional. |
| 404 on webhook route | Path was registered under `/webhooks/<name>`, an explicit path was normalized differently, or the Hub URL is stale | Inspect registered routes, use `@app.add_webhook("/events")` or `@webhook_endpoint("events")`, and update the Hub destination after confirming the public URL. |
| Duplicate webhook route `ValueError` | Two handlers normalized to the same path | Give each handler a distinct explicit path or remove the duplicate registration. |
| Payload validation fails | Handler type does not match payload, required/optional nested fields assumed incorrectly, or malformed JSON | Type the handler as `WebhookPayload`, use optional `comment`/`updatedRefs` checks, and validate a local fixture with Pydantic before connecting a live hook. |
| Hub webhook registration fails | Neither URL nor Job id, both supplied, bad watch selector/domain, or insufficient token | Validate the mutually exclusive destination and `type:name` watch entries locally; list/inspect with the same namespace token. Create/update/delete are remote mutations. |
| Webhook signature/secret mismatch | Header secret was confused with a cryptographic body signature or rotated on only one side | Follow the server's `x-webhook-secret` contract; do not invent a signature algorithm. Keep any external signing layer separate and test canonical raw-body handling if one is added. |
| OAuth import error | `oauth` extra/Authlib/Starlette session support missing | Install the OAuth extra in the application environment and rerun import diagnosis. |
| OAuth configuration `ValueError` | Space OAuth is not enabled or one of `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_SCOPES`, `OPENID_PROVIDER_URL` is absent | Set `hf_oauth: true` in Space metadata and provision the service configuration; never hard-code client secrets. |
| OAuth callback loops or state mismatch | Session cookie blocked, wrong HTTPS/host, stale callback, or iframe cookie policy | Use HTTPS, check route prefix and public host, inspect browser cookie policy, and allow the package's bounded redirect recovery. Do not bypass state validation. |
| OAuth works locally but not in Space | Local mode intentionally mocks OAuth; production mode uses real provider configuration | Treat local login as a test fixture only. Validate real OAuth only in an explicitly authorized Space with non-production credentials. |

`WebhooksServer` is experimental and Gradio-backed. Start it non-blocking in a
mocked test, verify routes/401/403/payload parsing, and do not open a public
share tunnel as a test shortcut. OAuth is also experimental; do not log
`OAuthInfo.access_token`.

## Mixin, cards, and serialization

| Symptom | Likely cause | Recovery |
|---|---|---|
| Mixin reload has wrong shape/config | Constructor value was not JSONable, config was overridden, annotation is missing, or `_from_pretrained` does not match the hook contract | Keep stable constructor args JSONable, pass explicit `config`/model kwargs, annotate custom types, define coders, and compare `config.json` to the checkpoint before loading. |
| `_save_pretrained`/`_from_pretrained` not implemented | Generic `ModelHubMixin` is an integration contract, not a complete framework serializer | Implement both hooks; use `PyTorchModelHubMixin` for a PyTorch module and test local save/load first. |
| Mixin loads but behavior differs | PyTorch mixin restores in eval mode or loaded on the wrong device | Call `train()` before training, pass `map_location`, check dtype/device, and use `strict=True` for a compatibility gate when appropriate. |
| `safetensors` missing/incompatible | Safe serialization extra absent or version too old for desired device behavior | Install/upgrade safetensors, verify its version with the same interpreter, and use CPU fallback only when that is an accepted behavior. |
| Pickle warning or unsafe load | `safe_serialization=False`, `.bin` input, or an untrusted checkpoint | Prefer safetensors. For a trusted legacy pickle, use explicit `weights_only=True` where supported and isolate the source; never load arbitrary pickles. |
| Missing/unexpected keys | Wrong model class, stale index, tied/shared tensors discarded, or `strict` mismatch | Inspect `missing_keys`/`unexpected_keys`, compare index weight map, pass known tied names when saving, and fix model/checkpoint compatibility rather than suppressing blindly. |
| Checkpoint directory invalid | No single recognized file or index, multiple ambiguous files, or bad pattern | Use generated default names/index, pass matching `filename_pattern`, and list local files before loading. |
| Card metadata block is not a dict | YAML frontmatter is a scalar/list or malformed | Make the first fenced block valid YAML mapping; use `ignore_metadata_errors=True` only when deliberate loss is acceptable and record the warning. |
| Model-index parse error | Missing required fields, wrong nested type, eval results without model name, or source name without URL | Build `EvalResult` with required task/dataset/metric fields, provide `model_name`, pair source name+URL, and round-trip `to_dict()`. |
| Card loads but metadata disappears | Invalid model-index ignored or unknown typed field normalized | Check warnings and `data.to_dict()`, do not use ignored metadata as evaluation truth, and fix the YAML rather than relying on permissive parsing. |
| Jinja card generation fails | Jinja2 is missing or template variable is absent | Install Jinja2 or use direct Markdown/frontmatter; provide every custom template variable and save/reload locally. |
| Remote card validation fails | Hub schema rejects a value that YAML accepted, wrong repo type, or network/auth failure | Parse locally first, then call `validate()` only with explicit network authorization. Inspect the returned text and correct schema fields. |
| DDUF export says invalid entry | Unsupported extension, backslash, too many directory levels, duplicate name, or wrong content type | Use only `.json`, `.model`, `.safetensors`, `.txt`; normalize to Unix names and keep at most one folder level. Recreate output from a clean temporary path. |
| DDUF missing index/structure error | `model_index.json` missing/not a mapping, folder absent from index, or folder has no required config | Add a dictionary `model_index.json`, map each folder, and add `config.json`/tokenizer/preprocessor/scheduler config in every folder. |
| DDUF read rejects archive | Compressed entry, corrupt ZIP/header, invalid names, missing required index, or malformed JSON | Re-export with the library helper and uncompressed entries; do not patch a corrupt archive in place. |
| DDUF unsafe path concern | An external index or archive includes absolute/drive/`..`/backslash path | Reject the archive or entry before extraction. `DDUFEntry` reading is preferable to arbitrary extraction; the parser is not a general security sandbox. |
| DDUF weights do not load | Bytes are not valid safetensors, wrong framework/device, or wrong entry selected | Read exact `DDUFEntry`, use `as_mmap()`/bytes with the safetensors loader, and compare keys/shapes to the expected state dict. |
| TensorBoard writer fails/imports but does not log | `tensorboardX` and `torch.utils.tensorboard` dependencies are missing, logdir is wrong, or upload scheduler/network/permission failed | Diagnose the writer dependency, test a plain local `SummaryWriter`, then mock scheduler/card/upload. Remember `HFSummaryWriter` construction and context exit can mutate a remote repo. |

## Remote auth and network

- An HTTP 401 usually means no token, expired token, wrong token source, or a
  missing permission scope. A 403 usually means the token is valid but lacks
  write/owner/resource access. A 404 can mean a wrong id **or** a private target
  that the current token cannot see.
- Pass `token` and `namespace` explicitly in automation. Avoid printing token
  values, full request headers, Job secrets, OAuth access tokens, or private
  URLs. If using cached auth, confirm identity with a non-mutating `whoami` or
  an equivalent read check.
- Network timeouts and SSE disconnects are not proof of failed mutation. For a
  create/update, inspect the resource by id or list it before retrying. For
  logs, use bounded non-follow mode and authoritative status polling.
- Use `local_files_only=True` for mixin/card model loading when a local fixture
  is expected. Remote card validation, `RepoCard.load` from an id, Hub weight
  download, uploads, Jobs, Sandboxes, Spaces, OAuth provider calls, and webhook
  registration all require an explicit network/credential decision.
- Stop and ask for authorization when the next recovery step could incur
  billing, publish data, rotate a credential, expose an endpoint, or delete a
  remote resource. A successful local or mocked check is not evidence that a
  production mutation is safe.
