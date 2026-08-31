# Spaces, OAuth, and server integrations

Read this reference for Space runtime/resource management, Hub webhook
registration, `WebhooksServer`, webhook payloads, and Hugging Face OAuth. The
resource and registration methods mutate remote state. Keep the examples with
placeholder ids/tokens as plans, or mock `HfApi`/HTTP boundaries during
verification.

## Space lifecycle and resources

Create a Space with `HfApi.create_repo` and `repo_type="space"`. Its relevant
signature is:

```python
api.create_repo(
    repo_id, *, token=None, private=None, visibility=None, repo_type=None,
    exist_ok=False, resource_group_id=None, region=None, space_sdk=None,
    space_hardware=None, space_storage=None, space_sleep_time=None,
    space_secrets=None, space_variables=None, space_volumes=None,
    space_template=None,
)
```

`space_sdk` is commonly `gradio`, `streamlit`, `docker`, or `static`.
`space_hardware`, `space_storage`, sleep time, initial secrets/variables, and
volumes are applied as part of creation. `exist_ok=True` avoids failure for an
existing id but does not mean all requested settings are harmlessly reconciled.
Use a private Space for workflows containing private data or privileged
controls. Uploading the application code is a separate networked side effect;
validate the file set before calling `upload_folder` or `upload_file`.

Read current state first:

```python
runtime = api.get_space_runtime("OWNER/SPACE", token=token)
print(runtime.stage, runtime.hardware, runtime.requested_hardware, runtime.storage)
print(runtime.sleep_time, runtime.volumes)
```

`SpaceRuntime.stage` commonly reports `NO_APP_FILE`, `CONFIG_ERROR`, `BUILDING`,
`BUILD_ERROR`, `RUNNING`, `RUNNING_BUILDING`, `RUNTIME_ERROR`, `DELETING`,
`STOPPED`, `PAUSED`, `APP_STARTING`, or `RUNNING_APP_STARTING`. The
intermediate states are building and app-starting states; `wait_for_space` polls
until a non-intermediate stage and raises `TimeoutError` on a deadline. A
returned `RUNNING` means the service reached its run state, not that the app's
business health check succeeded. For build or crash diagnosis, consume
`fetch_space_logs(repo_id, build=True|False, follow=False|True)`.

### Hardware, storage, sleep, and restart

Inspect the service catalog with `api.list_spaces_hardware(token=token)`. Then
request resources deliberately:

```python
from huggingface_hub import SpaceHardware, SpaceStorage

# Each call below is a remote mutation and may restart or incur billing.
api.request_space_hardware("OWNER/SPACE", SpaceHardware.T4_MEDIUM, sleep_time=3600, token=token)
api.request_space_storage("OWNER/SPACE", SpaceStorage.SMALL, token=token)
api.set_space_sleep_time("OWNER/SPACE", 3600, token=token)
api.pause_space("OWNER/SPACE", token=token)
api.restart_space("OWNER/SPACE", factory_reboot=False, token=token)
```

`request_space_hardware(repo_id, hardware, *, token=None, sleep_time=None)`
returns the new `SpaceRuntime`; strings such as `"t4-medium"` are accepted by
runtime validation as well as enum values. The returned `requested_hardware`
can differ from current `hardware` while the service rebuilds. Free
`cpu-basic` sleep policy is not custom-configurable; upgraded hardware can use
seconds or `-1` for no automatic sleep. Upgraded hardware needs an eligible
payment card or grant and can bill while running. Pause avoids billing and
requires an owner; restart can be a factory rebuild, which discards cached
build dependencies and is slower.

`request_space_storage`/`delete_space_storage` are deprecated in favor of
`set_space_volumes`/`delete_space_volumes`:

```python
from huggingface_hub import Volume

api.set_space_volumes(
    "OWNER/SPACE",
    [Volume(type="model", source="OWNER/MODEL", mount_path="/models")],
    token=token,
)
# Replaces the Space volume configuration; deletion is also a remote mutation.
api.delete_space_volumes("OWNER/SPACE", token=token)
```

Volumes use `bucket`, `model`, `dataset`, or `space`, an id, absolute
`mount_path`, and optional revision/read-only/path fields. Repository mounts
are normally read-only. Resource changes and secrets/variables trigger an app
restart; poll runtime and reread logs after a change.

### Secrets and variables

Use `add_space_secret(repo_id, key, value, *, description=None, token=None)` for
sensitive values and `add_space_variable` for non-sensitive configuration.
Secret values are write-only: `get_space_secrets` returns keys, descriptions,
and update timestamps, not values. Variables are returned with their values.
Deletion is a mutation and returns `None` for secret deletion or the remaining
variable mapping for variable deletion:

```python
api.add_space_secret("OWNER/SPACE", "API_KEY", secret_value, token=token)
api.add_space_variable("OWNER/SPACE", "MODEL_ID", "OWNER/MODEL", token=token)
print(api.get_space_secrets("OWNER/SPACE", token=token).keys())
print(api.get_space_variables("OWNER/SPACE", token=token)["MODEL_ID"].value)
```

Validate key naming, value type, and expected application environment names
before writing. Never use `get_space_secrets` as a way to recover the value;
rotate by writing a replacement. A mock recovery should model an invalid
secret/variable causing `CONFIG_ERROR` or app failure, then replace/delete the
bad setting, wait for restart/build, and assert the corrected state without
calling the live service.

`duplicate_space(from_id, to_id=None, *, private=None, visibility=None,
token=None, exist_ok=False, hardware=None, storage=None, sleep_time=None,
secrets=None, variables=None)` is also a remote creation/copy operation. Use
`duplicate_repo` for newer code where the deprecated helper warns. Confirm
whether copied settings include private values before proceeding.

## Hub-managed webhooks

The API methods are:

```python
api.list_webhooks(token=token)
api.get_webhook("WEBHOOK_ID", token=token)
api.create_webhook(
    url="https://service.example/hook",  # or job_id, not both
    watched=[{"type": "model", "name": "OWNER/MODEL"}],
    domains=["repo", "discussion"],
    secret=secret_value,
    token=token,
)
api.update_webhook("WEBHOOK_ID", url="https://new.example/hook", secret=secret_value, token=token)
api.enable_webhook("WEBHOOK_ID", token=token)
api.disable_webhook("WEBHOOK_ID", token=token)
api.delete_webhook("WEBHOOK_ID", token=token)
```

`create_webhook` requires exactly a destination URL or a source `job_id` and a
nonempty `watched` list. Watch items use model, dataset, Space, user, or org
selectors. Domains narrow event classes such as repository or discussion
changes. Registration, update, enable/disable, and deletion are credentialed
remote mutations. Treat webhook secrets as credentials; never log them or put
them in source. A webhook that targets a Job passes the payload in
`WEBHOOK_PAYLOAD` to that Job. Test registration with a mocked response and
send a locally generated payload to the endpoint before enabling a live hook.

The CLI mirrors this surface: `hf webhooks ls`, `info`, `create`, `update`,
`enable`, `disable`, and `delete`. Deletion prompts for confirmation. Read
`hf webhooks <command> --help` before scripting flags; do not use live create or
delete in a safe check.

## WebhooksServer

`WebhooksServer` is experimental and requires Gradio and FastAPI. Its checked
constructor is `WebhooksServer(ui=None, webhook_secret=None)`. A secret can be
passed directly or via `WEBHOOK_SECRET`; no secret leaves endpoints open.
Register endpoints with `add_webhook(path=None)` and start the Gradio-backed
server with `launch(prevent_thread_lock=False, **launch_kwargs)`:

```python
import gradio as gr
from huggingface_hub import WebhookPayload, WebhooksServer

with gr.Blocks() as ui:
    gr.Markdown("Webhook receiver")
app = WebhooksServer(ui=ui, webhook_secret="local-test-secret")

@app.add_webhook("/events")
async def events(payload: WebhookPayload):
    if payload.repo.type == "dataset" and payload.event.action == "update":
        return {"accepted": True}
    return {"accepted": False}

# In a local fixture use a mocked/non-blocking launch; production launch is a
# network-facing server and must have a reviewed secret and route.
```

`@app.add_webhook` uses the function name when no path is supplied and always
registers under `/webhooks/<path>`. Duplicate paths raise `ValueError`. The
handler may be sync or async and should accept `WebhookPayload` for automatic
Pydantic parsing; optional fields such as `comment` and `updatedRefs` can be
absent. `webhook_endpoint(path=None)` is the convenience decorator that uses a
global server and exposes `handler.launch()`; it registers launch at process
exit, which is convenient but less explicit than constructing a server.

When a secret is configured, requests without `x-webhook-secret` return 401 and
an incorrect header returns 403. A correct header allows payload dispatch. In
a Space, the public URL is based on `SPACE_HOST`; locally Gradio's local/share
URL is displayed. Configure the Hub webhook destination only after confirming
the route path, HTTPS/tunnel behavior, and matching secret. WebhooksServer is
experimental; pin the package and avoid relying on undocumented internals.

## OAuth in a FastAPI app

The optional OAuth integration uses:

```python
from fastapi import FastAPI, Request
from huggingface_hub import attach_huggingface_oauth, parse_huggingface_oauth

app = FastAPI()
attach_huggingface_oauth(app, route_prefix="/app")

@app.get("/me")
def me(request: Request):
    info = parse_huggingface_oauth(request)
    if info is None:
        return {"logged_in": False}
    return {"logged_in": True, "username": info.user_info.preferred_username}
```

`attach_huggingface_oauth(app, route_prefix="/")` adds login, callback, and
logout routes under `/oauth/huggingface/` (or the supplied prefix). In a real
Space, OAuth requires the Space metadata setting `hf_oauth: true` and the
service-provided `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_SCOPES`, and
`OPENID_PROVIDER_URL` configuration. The integration stores OAuth info in a
signed session cookie; use HTTPS and do not expose access tokens in responses
or logs. `parse_huggingface_oauth(request)` returns `OAuthInfo` or `None` and
intentionally tolerates missing fields.

Outside a Space, the package provides mocked OAuth routes for local debugging,
with a warning and a locally derived profile/token; this is not authentication
and must not be used as a production security decision. The `oauth` extra is
needed for session/Authlib dependencies. Missing `authlib`/Starlette session
support produces an actionable install error; missing Space OAuth configuration
raises `ValueError` naming the missing variable. Do not test a live callback in
safe verification—mock the session and inspect route registration.

## Native evidence and safe coverage

The native tests cover webhook payload deserialization, sync/async handlers,
implicit/explicit route naming, duplicate route errors, and 401/403 secret
checks. CLI tests cover mocked Space settings, logs, hardware, volume, Jobs,
and webhook command forwarding. They do not prove the integrated sequence of a
Space restart, corrected variable/secret, webhook request, and downstream Job.
Add that as a synthetic mocked lifecycle case and assert no remote mutation
when validation fails.
