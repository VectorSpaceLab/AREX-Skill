# Actions and Notifications

Checkpoint actions run after validation results are produced. Use them for Data Docs updates, Slack/email alerts, and custom post-validation logic. Notification actions can send real network traffic, so keep secrets out of code and test them only with mocks or safe substitutes.

## Imports and action order

```python
from great_expectations.checkpoint import (
    ActionContext,
    CheckpointResult,
    EmailAction,
    SlackNotificationAction,
    UpdateDataDocsAction,
    ValidationAction,
)
```

A checkpoint accepts `actions=[...]`. GX internally runs `UpdateDataDocsAction` instances before other actions so notification renderers can reference fresh Data Docs URLs. Still list Data Docs updates first in code for readability.

## UpdateDataDocsAction

`UpdateDataDocsAction` builds configured Data Docs sites after each validation result:

```python
action = UpdateDataDocsAction(
    name="update_local_docs",
    site_names=["local_site"],
)
```

Constructor shape:

```text
UpdateDataDocsAction(*, type="update_data_docs", name: str, site_names: list[str] = [])
```

Behavior:

- Empty `site_names` means build all configured Data Docs sites.
- Non-empty `site_names` limits builds and returned URLs to those sites.
- The action incrementally calls Data Docs build logic for each validation result and returns a mapping from validation result identifiers to site-name/URL dictionaries.
- If no Data Docs sites are configured, the action cannot create useful docs output; configure the context first.

Use `UpdateDataDocsAction` freely in local smoke tests because it writes local docs only when the context is configured that way. Do not mix it with network notification actions in an unmocked smoke test.

## SlackNotificationAction

`SlackNotificationAction` sends a Slack message through either an incoming webhook or a bot token/channel pair:

```python
action = SlackNotificationAction(
    name="slack_on_failure",
    slack_webhook="${validation_notification_slack_webhook}",
    notify_on="failure",
    notify_with=["local_site"],
    show_failed_expectations=True,
)
```

Constructor shape:

```text
SlackNotificationAction(
  *,
  type="slack",
  name: str,
  slack_webhook: str | ConfigStr | None = None,
  slack_token: str | ConfigStr | None = None,
  slack_channel: str | ConfigStr | None = None,
  notify_on: "all" | "success" | "failure" | "info" | "warning" | "critical" = "all",
  notify_with: list[str] | None = None,
  show_failed_expectations: bool = False,
  renderer: SlackRenderer = ...,
)
```

Rules:

- Provide either `slack_webhook` or both `slack_token` and `slack_channel`; do not provide both patterns at once.
- Use config-variable references such as `${validation_notification_slack_webhook}` or environment variables, not literal secrets.
- `notify_with` names Data Docs sites whose links should be included. If a named site is not configured, the renderer warns and omits that link.
- `show_failed_expectations=True` can help alerts but may reveal expectation names and failure summaries; confirm this is acceptable for the channel.
- When `notify_on` matches the checkpoint result, this action performs an HTTP POST. Do not run it in unmocked tests or examples.

## EmailAction

`EmailAction` sends an SMTP email:

```python
action = EmailAction(
    name="email_on_failure",
    smtp_address="${smtp_address}",
    smtp_port="${smtp_port}",
    receiver_emails="${validation_receiver_emails}",
    sender_login="${validation_sender_login}",
    sender_password="${validation_sender_password}",
    sender_alias="${validation_sender_alias}",
    use_ssl=True,
    notify_on="failure",
    notify_with=["local_site"],
)
```

Constructor shape:

```text
EmailAction(
  *,
  type="email",
  name: str,
  smtp_address: str | ConfigStr,
  smtp_port: str | ConfigStr,
  receiver_emails: str | ConfigStr,
  sender_login: str | ConfigStr | None = None,
  sender_password: str | ConfigStr | None = None,
  sender_alias: str | ConfigStr | None = None,
  use_tls: bool | None = None,
  use_ssl: bool | None = None,
  notify_on: "all" | "success" | "failure" | "info" | "warning" | "critical" = "all",
  notify_with: list[str] | None = None,
  renderer: EmailRenderer = ...,
)
```

Rules:

- `receiver_emails` is a comma-separated string after config substitution.
- Use either TLS or SSL when sending real email; the action warns if neither is set.
- SMTP connection/authentication failures are logged by the action rather than producing a rich validation failure.
- When `notify_on` matches, this action connects to the SMTP server. Test with mocks or with a local dummy SMTP server only when explicitly safe.

## `notify_on` semantics

Built-in notification actions use `should_notify(success, notify_on, max_severity)`:

| `notify_on` | Sends when |
| --- | --- |
| `all` | Always. |
| `success` | Checkpoint result succeeds. |
| `failure` | Checkpoint result fails. |
| `info`, `warning`, `critical` | Checkpoint fails and the maximum failed expectation severity equals that value. |

For production alerts, prefer `failure` or a severity-specific mode over `all`. If a severity-specific notification never sends, inspect the expectation `severity` values and whether the run actually failed.

## Credential safety

Use the context/configuration sub-skill for secure substitution patterns. Practical rules:

- Store secrets outside code and generated skill content, using environment variables, `config_variables.yml`, or a secret manager supported by the deployed context.
- Reference secrets with `${name}` or `ConfigStr`-compatible values in action configuration.
- Never print substituted values in logs or helper scripts.
- Do not commit generated Data Docs that contain sensitive validation metadata unless the project has reviewed the content.
- Do not use placeholder URLs that match real webhook hostnames in tests; they can still trigger attempted network sends.

## No-network testing patterns

Safe tests should avoid real notification classes or monkeypatch their sending methods:

```python
class RecordingAction(ValidationAction):
    type: Literal["recording_action"] = "recording_action"
    marker: str = "recorded"

    def run(self, checkpoint_result: CheckpointResult, action_context: ActionContext | None = None) -> dict:
        return {"marker": self.marker, "success": checkpoint_result.success}
```

If testing Slack or email rendering, mock `_send_slack_notification()` or `_send_email()` and assert the payload shape. Do not rely on unreachable hosts to prove no send occurred; the action still attempts a network connection.

## Custom actions

A custom action subclasses `ValidationAction`, sets a unique literal `type`, declares any required fields, and overrides `run()`:

```python
from typing import Literal
from great_expectations.checkpoint import ActionContext, CheckpointResult, ValidationAction

class AuditAction(ValidationAction):
    type: Literal["audit_log"] = "audit_log"
    target_name: str

    def run(self, checkpoint_result: CheckpointResult, action_context: ActionContext | None = None) -> dict:
        summary = checkpoint_result.describe_dict()
        return {
            "target_name": self.target_name,
            "success": checkpoint_result.success,
            "evaluated_validations": summary["statistics"]["evaluated_validations"],
        }
```

Guidance:

- Keep `type` globally unique; reusing a built-in type such as `slack` raises a registry error.
- Return JSON-serializable dictionaries so action results can be inspected or stored safely.
- Use `action_context.filter_results(UpdateDataDocsAction)` when a custom action needs URLs produced by earlier Data Docs actions.
- Treat `checkpoint_result.run_results` as the stable source of validation payloads; result details vary with checkpoint `result_format`.
- Do not mutate validation results inside custom actions unless the caller explicitly wants that side effect.
