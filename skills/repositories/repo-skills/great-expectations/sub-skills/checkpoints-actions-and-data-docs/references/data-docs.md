# Data Docs

Data Docs are rendered documentation for expectation suites and validation results. In checkpoint workflows, `UpdateDataDocsAction` keeps configured sites current after validations run.

## Configure a local site

For a file-backed GX project, configure Data Docs through the context:

```python
site_name = "local_site"
site_config = {
    "class_name": "SiteBuilder",
    "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
    "store_backend": {
        "class_name": "TupleFilesystemStoreBackend",
        "base_directory": "uncommitted/data_docs/local_site/",
    },
}

context.add_data_docs_site(site_name=site_name, site_config=site_config)
```

For existing sites:

```python
site_names = context.get_site_names()
site_configs = context.list_data_docs_sites()
context.update_data_docs_site(site_name="local_site", site_config=site_config)
context.delete_data_docs_site(site_name="old_site")
```

If the task involves project roots, context mode, or persisted configuration, read `../contexts-and-configuration/SKILL.md` first.

## Build and inspect docs

Build all configured sites:

```python
index_urls = context.build_data_docs()
```

Build selected sites:

```python
index_urls = context.build_data_docs(site_names=["local_site"])
```

Useful build options:

- `site_names`: `None` builds all sites; a list builds only named sites.
- `resource_identifiers`: optional list of expectation-suite or validation-result identifiers for incremental builds.
- `dry_run=True`: returns URLs that would be built without writing files.
- `build_index=False`: skips the site index page.

`context.get_docs_sites_urls(resource_identifier=..., site_name=..., site_names=..., only_if_exists=True)` returns site-name/URL dictionaries. `only_if_exists=False` can return the expected URL even before files exist, which is useful for diagnostics but not proof that docs were built.

## Open docs

```python
context.open_data_docs(site_name="local_site", only_if_exists=True)
```

`open_data_docs()` opens URLs in a local browser and raises `NoDataDocsError` when no URL exists. In automated agents, prefer printing URLs from `get_docs_sites_urls()` or `build_data_docs()` instead of opening a browser.

## Automate docs with checkpoints

Add an update action to the checkpoint:

```python
from great_expectations.checkpoint import UpdateDataDocsAction

actions = [UpdateDataDocsAction(name="update_local_docs", site_names=["local_site"])]
checkpoint = context.checkpoints.add_or_update(
    gx.Checkpoint(
        name="daily_orders_checkpoint",
        validation_definitions=[validation_definition],
        actions=actions,
        result_format="SUMMARY",
    )
)
result = checkpoint.run(batch_parameters={"year": "2026", "month": "06"})
```

During a checkpoint run, `UpdateDataDocsAction` builds docs for each validation result and its expectation suite. Notification actions that run later can include Data Docs links.

## Site names and action fields

- `site_name` is used by single-site context methods such as `open_data_docs(site_name="local_site")`.
- `site_names` is a list used by `build_data_docs(site_names=[...])` and `UpdateDataDocsAction(site_names=[...])`.
- Empty `UpdateDataDocsAction.site_names` means all configured sites.
- If a notification action has `notify_with=["local_site"]`, that site must be configured and should be updated before the notification runs.

## Output path and hosting considerations

For local filesystem sites, `base_directory` is interpreted by the configured store backend. In a standard file project, `uncommitted/data_docs/local_site/` is the default local pattern and should not be committed if it contains sensitive validation details.

When adapting to a networked filesystem or static hosting location:

1. Keep the Data Docs store backend path explicit and controlled by project configuration.
2. Ensure the scheduler or runtime user has write permissions to the target directory.
3. Build docs from the same context that stores validation results.
4. Treat generated docs as potentially sensitive because they may include expectation names, validation statistics, and unexpected values depending on result format.
5. Avoid cloud-storage or web-hosting credentials in code; route credentials through config variables.

## When docs are stale

Data Docs can be stale when:

- A checkpoint ran without `UpdateDataDocsAction`.
- `UpdateDataDocsAction.site_names` excludes the site the user is viewing.
- The context has no configured `data_docs_sites` or the wrong file project root is being loaded.
- A validation result exists, but docs were built before that run.
- `build_index=False` was used and the user is looking at the site index rather than a direct validation page.
- The docs output directory is being served from a cached location or an older deployment.

Refresh pattern:

```python
print(context.get_site_names())
print(context.build_data_docs(site_names=["local_site"]))
print(context.get_docs_sites_urls(site_name="local_site", only_if_exists=True))
```

If these calls show no configured sites, fix the context configuration instead of changing the checkpoint.

## Local vs Cloud boundaries

This skill covers GX Core local and file/network filesystem Data Docs workflows. Do not rely on Cloud UI-only workflows here. If the active context is Cloud-backed, some Data Docs URLs and action returns differ; keep Cloud credentials out of generated examples and route Cloud-only work to product-specific documentation outside this runtime skill.
