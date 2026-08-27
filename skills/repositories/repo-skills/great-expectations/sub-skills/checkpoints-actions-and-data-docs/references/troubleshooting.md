# Troubleshooting Checkpoints, Actions, and Data Docs

Use this reference when checkpoint orchestration fails after the context, data asset, suite, and validation definition already exist. Route prerequisite object problems to the sibling sub-skills.

## Checkpoint has no validation definitions

Symptoms:

- `CheckpointRunWithoutValidationDefinitionError`.
- A checkpoint object exists but `checkpoint.validation_definitions` is empty.
- Actions never run.

Fix:

```python
validation_definition = context.validation_definitions.get("daily_orders_validation")
checkpoint = context.checkpoints.add_or_update(
    gx.Checkpoint(
        name="daily_orders_checkpoint",
        validation_definitions=[validation_definition],
        actions=checkpoint.actions,
        result_format="SUMMARY",
    )
)
```

If the validation definition cannot be retrieved, recreate it from the current batch definition and suite. Do not create a checkpoint around placeholder or unsaved validation definitions.

## Checkpoint is not fresh or cannot retrieve validation definitions

Symptoms:

- Freshness errors such as `CheckpointNotAddedError`, `CheckpointNotFreshError`, or validation-definition retrieval errors.
- A serialized checkpoint references validation-definition identifiers that no longer exist.

Fix:

1. Retrieve current child resources from the same context: datasource, asset, batch definition, suite, and validation definition.
2. Recreate the checkpoint with those objects.
3. Persist with `context.checkpoints.add_or_update(checkpoint)`.
4. Call `checkpoint.run()` only after all child resources are saved in the context.

Ephemeral contexts lose resources when the process ends; use a file context for persisted production checkpoints.

## Missing batch or expectation parameters

Symptoms:

- Checkpoint fails before evaluating expectations.
- A validation definition works for one batch but fails in scheduled runs.
- Error mentions missing partition keys or unresolved `$PARAMETER` values.

Fix:

- Inspect batch parameter keys from the asset/batch definition; route to `../datasources-and-assets/SKILL.md`.
- Pass shared batch parameters to `checkpoint.run(batch_parameters=...)`.
- Pass suite runtime parameters to `checkpoint.run(expectation_parameters=...)`.
- Split the checkpoint if different validation definitions need incompatible batch parameter keys.

## Missing Slack credentials

Symptoms:

- Constructing `SlackNotificationAction` raises a validation error.
- Error says to provide either `slack_webhook` or `slack_token` and `slack_channel`.
- Action raises `No Slack webhook URL provided.` after substitution.

Fix:

```python
SlackNotificationAction(
    name="slack_on_failure",
    slack_webhook="${validation_notification_slack_webhook}",
    notify_on="failure",
)
```

or:

```python
SlackNotificationAction(
    name="slack_on_failure",
    slack_token="${validation_notification_slack_token}",
    slack_channel="${validation_notification_slack_channel}",
    notify_on="failure",
)
```

Verify that config variables or environment variables are available to the same context that runs the checkpoint. Never paste real webhook URLs or tokens into generated code or logs.

## Missing email credentials or SMTP settings

Symptoms:

- Email action logs missing login/password warnings.
- SMTP connection or authentication errors appear in logs.
- No email arrives even though checkpoint failed.

Fix:

- Confirm `notify_on` matches the checkpoint result.
- Provide `smtp_address`, `smtp_port`, and `receiver_emails` through config variables.
- Provide both `sender_login` and `sender_password`, or neither for a trusted local relay.
- Use `use_ssl=True` or `use_tls=True` when sending real email.
- Test with mocks or a local dummy SMTP server before enabling production recipients.

## Accidental real Slack or email sends

Symptoms:

- A smoke test or notebook posts to Slack or sends email.
- A placeholder webhook is still contacted.
- Alerts fire on successful validations because `notify_on="all"`.

Fix:

1. Remove notification actions from local smoke workflows; use only `UpdateDataDocsAction` or a custom recording action.
2. Set production alerts to `notify_on="failure"` or severity-specific modes.
3. For tests, monkeypatch `SlackNotificationAction._send_slack_notification` or `EmailAction._send_email` before calling `checkpoint.run()`.
4. Rotate any secret that was committed, printed, or used in an unsafe test.

Do not rely on invalid hosts to prevent sends; the action still attempts network I/O.

## Data Docs site is not configured

Symptoms:

- `context.get_site_names()` returns `[]`.
- `context.build_data_docs()` returns `{}`.
- `context.open_data_docs()` raises `NoDataDocsError`.
- `UpdateDataDocsAction` returns empty docs mappings.

Fix:

```python
site_config = {
    "class_name": "SiteBuilder",
    "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
    "store_backend": {
        "class_name": "TupleFilesystemStoreBackend",
        "base_directory": "uncommitted/data_docs/local_site/",
    },
}
context.add_data_docs_site(site_name="local_site", site_config=site_config)
context.build_data_docs(site_names=["local_site"])
```

If `add_data_docs_site` is unavailable or does not persist, confirm the context mode and project root with `../contexts-and-configuration/SKILL.md`.

## Data Docs are configured but not updated

Symptoms:

- Old validation result is visible, but the latest run is missing.
- Notifications omit expected docs links.
- `notify_with` names a site that does not appear in docs URLs.

Fix:

- Add `UpdateDataDocsAction(name="update_docs", site_names=["local_site"])` to the checkpoint.
- Ensure `site_names` includes the site the user views, or leave it empty to build all configured sites.
- Call `context.build_data_docs(site_names=[...])` manually once to prove the site config works.
- Use `context.get_docs_sites_urls(only_if_exists=True)` to confirm built files exist.
- Check static hosting caches if the filesystem output is correct but the browser view is stale.

## Result format is too verbose

Symptoms:

- Validation results are large.
- Slack/email payloads include too much detail.
- Checkpoint runs become slow or memory-heavy after setting `COMPLETE`.

Fix:

- Change checkpoint `result_format` to `"SUMMARY"` for routine production runs.
- Use `"BASIC"` or `"BOOLEAN_ONLY"` for simple gates.
- Reserve `"COMPLETE"` or row-level result-format dicts for small, bounded debugging runs.
- Route unexpected-row extraction requirements to `../validations-and-results/SKILL.md` instead of making every checkpoint run verbose.

## Custom action payload mismatch

Symptoms:

- Custom action raises `KeyError` when reading `checkpoint_result.run_results`.
- Custom action expected unexpected rows but only summary data exists.
- Action works with `COMPLETE` but fails with `SUMMARY`.

Fix:

1. Inspect `checkpoint_result.describe_dict()` and one value from `checkpoint_result.run_results.values()` under the current result format.
2. Code defensively around optional fields such as `result`, `partial_unexpected_list`, and `unexpected_index_query`.
3. If the action requires row-level data, document and enforce a bounded `result_format` dict for that checkpoint.
4. Return a JSON-serializable action result that records missing fields rather than crashing when possible.

## Unknown action type during deserialization

Symptoms:

- Deserializing a checkpoint config raises an action registry retrieval error.
- Serialized action dict has no `type` key or uses a custom type that is not imported.

Fix:

- Include the built-in `type` key: `update_data_docs`, `slack`, or `email`.
- Ensure custom action classes are imported before parsing serialized checkpoint config.
- Avoid custom types that shadow built-ins; duplicate type registration raises an error.
