# Tool Shed Troubleshooting

Use this reference after identifying whether the problem belongs to the Tool Shed server, a Galaxy server with installed Tool Shed repositories, or local tool authoring. Route local wrapper XML issues to `../workflows-and-tools/SKILL.md`, generic HTTP/API failures to `../api-automation/SKILL.md`, and server startup/config file location issues to `../configuration-and-admin/SKILL.md`.

## Fast Triage

1. **Classify the target**: Tool Shed server, Galaxy server, or local repository/tool source.
2. **Classify the operation**: publish/create repository, install/update/uninstall repository, reset metadata, copy users/categories, rebuild search index, or data-manager install.
3. **Check safety**: local/test vs staging/production, admin key scope, destructive potential, and backup/rollback plan.
4. **Prefer preview**: dry-run metadata reset, list/search endpoints, and dry-run planner before mutating operations.
5. **Collect identifiers**: Tool Shed URL, Galaxy URL, owner, repository name, changeset revision, encoded repository id, installed repository id, tool id/guid, and config file names.

## Metadata Generation Or Reset Fails

Common causes:

- Invalid tool XML or missing test components detected during metadata generation.
- Stored `tool_config` paths became stale after `file_path` or repository storage moved.
- Repository dependency definitions reference missing owners, missing names, invalid changeset revisions, or another Tool Shed.
- Repository has changeset gaps or revisions that are not downloadable/installable.
- Metadata reset is run against the wrong surface: Tool Shed repository metadata vs Galaxy installed-repository metadata.

Safe response:

1. For Tool Shed-side metadata, plan/reset one repository first with `dry_run=true` and `verbose=true`.
2. Compare before/after metadata snapshots if available.
3. Inspect per-changeset status for created/updated records, invalid tools, repository dependencies, and errors.
4. If only stored paths are stale, a non-dry-run reset can repair metadata to current repository paths after confirmation.
5. If tool XML is invalid, route XML fixes to `../workflows-and-tools/SKILL.md`, then regenerate metadata.
6. Avoid bulk reset until single-repository behavior is understood.

## Installed Repository Reset Confusion

The Galaxy installed-repository reset endpoint resets metadata for repositories installed into a Galaxy instance, not the Tool Shed repository records themselves. Use it when symptoms are in Galaxy after install:

- Installed tool is stale after a Tool Shed update.
- Galaxy's installed repository state is inconsistent with `shed_tool_conf.xml` or the installed repository record.
- Admin intentionally wants all installed Tool Shed repositories in a Galaxy instance refreshed.

Avoid it when the issue is publishing metadata in a Tool Shed repository. In that case use Tool Shed repository metadata reset instead.

## Repository Dependencies Fail

Symptoms include install-info errors, missing dependency repositories, prior-installation loops, or metadata warnings.

Check:

- `repository_dependencies.xml` has required `name` and `owner` on each `<repository>`.
- `toolshed` either points to the current Tool Shed or is omitted so it can default correctly.
- `changeset_revision` exists and is an installable metadata revision.
- `prior_installation_required` is intentionally true and not masking a circular dependency issue.
- The dependency is not pointing to another Tool Shed through a code path that only supports same-shed dependencies.
- The dependency repository is not deleted, deprecated, or missing downloadable metadata.

If the dependency XML itself needs editing, route wrapper/repository content authoring to `../workflows-and-tools/SKILL.md` for local XML validation and then return here to reset/publish metadata.

## Install, Update, Or Uninstall Fails In Galaxy

Check the Galaxy-side state:

- Is the target Tool Shed reachable from the Galaxy server?
- Does the repository owner/name/changeset match an installable Tool Shed revision?
- Does the Galaxy API show an installed repository id for the owner/name/revision?
- Does `/api/tools/{tool_id}` find the expected tool after install?
- Did uninstall remove the tool from API-visible tool panel results?
- Does `check_for_updates` report a revision update when expected?
- Does `shed_tool_conf.xml` contain the expected Tool Shed guid/repository metadata?

Do not manually rewrite `shed_tool_conf.xml` or `integrated_tool_panel.xml` as a first fix. Prefer reinstall/update/uninstall APIs or metadata repair workflows that let Galaxy maintain generated config entries.

## Whoosh Search Is Stale Or Empty

Symptoms include Tool Shed search missing repositories/tools, categories not appearing in results, or tool search returning old metadata.

Check:

- Tool Shed search is enabled in configuration.
- `whoosh_index_dir` is set and writable.
- The Tool Shed runtime environment has Whoosh and Mercurial dependencies.
- Database connection, `file_path`, `hgweb_config_dir`, and `hgweb_repo_prefix` match the running Tool Shed.
- Repositories are not deleted, deprecated, or of type `tool_dependency_definition`, which is excluded from indexing.
- Tool XML files under repository contents are parseable enough to be indexed.

Rebuild index only after confirming service/runtime requirements and production risk. Use the planner's `build-whoosh-index` command to produce a checklist before running deployment tooling.

## Permissions And Keys

Tool Shed operations have several permission layers:

- Category creation and user creation require Tool Shed admin permissions.
- Repository metadata reset requires repository management permission or admin privileges depending on route and target.
- Bulk metadata reset can be restricted to repositories writable by the current user when not admin, or by `my_writable` when admin.
- Repository push/admin permissions are repository-specific, not the same as generic Galaxy admin status.
- Galaxy installed-repository reset requires a Galaxy admin API key.

If a request returns unauthorized/forbidden, verify that the API key belongs to the correct service. A Tool Shed key is not a Galaxy key, and a Galaxy key is not a Tool Shed key.

## Production Vs Test Shed Risk

High-risk operations:

- Creating users with synthetic passwords.
- Mirroring public-shed users/categories/repositories.
- Resetting metadata for many repositories.
- Rebuilding or deleting search indexes.
- Installing/uninstalling repositories in a production Galaxy instance.
- Pushing Mercurial repository content into a Tool Shed.

Use a local or disposable test shed for bootstrap/mirroring tasks. For production, require a scoped plan, backup/rollback, maintenance window when relevant, and explicit user confirmation.

## Data Manager Or `.loc` Side Effects

If a Tool Shed repository install affects data tables:

- Confirm whether the repository is a data manager or just ships `.loc` files.
- Non-data-manager `.loc` files should land under a shed subdirectory under the tool data path, not overwrite admin-managed root `.loc` files.
- Shed data table config should avoid inappropriate repository stamping for non-data-manager table entries.
- Table reload/execution behavior may require Galaxy admin API checks; separate install-state diagnosis from local data-manager tool authoring.

## Useful Dry-Run Planner Commands

```bash
python scripts/tool_shed_api_plan.py reset-repository-metadata --tool-shed http://localhost:9009 --repository-id ENCODED_ID --dry-run --verbose
python scripts/tool_shed_api_plan.py reset-installed-metadata --galaxy-url http://localhost:8080
python scripts/tool_shed_api_plan.py categories --from-tool-shed https://source.example.org --to-tool-shed http://localhost:9009
python scripts/tool_shed_api_plan.py users --from-tool-shed https://source.example.org --to-tool-shed http://localhost:9009
python scripts/tool_shed_api_plan.py build-whoosh-index --config config/tool_shed.yml
```

These commands are dry-run unless `--execute` and all required credentials are supplied. Keep credentials in environment variables and avoid shell history exposure for real keys.
