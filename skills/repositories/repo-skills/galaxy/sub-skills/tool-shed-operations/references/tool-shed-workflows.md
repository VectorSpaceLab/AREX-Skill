# Tool Shed Workflows

Use this reference for Tool Shed repository operations and installed repository behavior. For local wrapper XML or workflow authoring, switch to `../workflows-and-tools/SKILL.md`; Tool Shed work starts when repository metadata, publishing, installation, or Tool Shed-side APIs are involved.

## Mental Model

Galaxy has two related but separate surfaces:

- **Tool Shed server**: hosts repositories, categories, users, repository metadata, repository dependency information, and Tool Shed search indexes.
- **Galaxy server with installed repositories**: consumes Tool Shed repositories, writes installed tools into the shed tool panel config, stores installed repository state, and exposes Galaxy-side Tool Shed repository APIs.

When diagnosing a problem, first decide which side owns the symptom:

| Symptom | Likely owner | First checks |
| --- | --- | --- |
| Category/user/repository cannot be created in a Tool Shed | Tool Shed server | Tool Shed URL, admin API key, `/api/categories`, `/api/users`, `/api/repositories` permissions |
| Repository has stale or missing metadata | Tool Shed server | repository id, metadata endpoint, reset metadata with dry-run/verbose first |
| Installed tool missing from Galaxy panel | Galaxy server | `shed_tool_conf.xml`, install state, tool id/guid, repository install response |
| Installed repository update or reinstall behaves oddly | Galaxy server plus Tool Shed metadata | installed changeset revision, Tool Shed install info, repository metadata revisions |
| Tool Shed search misses repositories/tools | Tool Shed server | Whoosh enabled, index directory, rebuild requirements, repository/tool indexing logs |
| Data manager installed from a shed does not reload tables | Galaxy server | shed data-manager configs, table reload API, repository installation logs |

## Repository Installation Into Galaxy

Repository installation is exercised by Galaxy integration tests through helper methods such as `install_repository(owner, name, changeset_revision)`, `uninstall_repository(...)`, `get_installed_repository_for(...)`, and `index_repositories(...)`. These tests show stable behavior to preserve:

1. A known installable changeset is selected from the Tool Shed.
2. Galaxy installs the repository and exposes the tool by its tool id/guid.
3. The installed repository is retrievable through Galaxy's Tool Shed repository API.
4. Uninstall removes the tool from the API-visible tool panel and removes the installed repository record.
5. Updates compare the installed changeset against Tool Shed metadata and may report a revision update before installing the newer revision.

For a future agent debugging installation, gather:

- Tool Shed host, repository owner, repository name, and changeset revision.
- Whether the target is a disposable local Galaxy, staging, or production.
- The installed repository id from Galaxy, if already installed.
- Whether the tool appears through `/api/tools/{tool_id}` and whether the tool id includes a Tool Shed-style guid.
- Relevant `shed_tool_conf.xml` and `integrated_tool_panel.xml` symptoms without manually editing generated Tool Shed entries first.

## Tool Panel And Installed Tool Configs

Galaxy stores tools installed from a Tool Shed in the file selected by `shed_tool_config_file`, defaulting to `shed_tool_conf.xml`. Built-in and local tools belong to `tool_config_file`; migrated Tool Shed tools can involve `migrated_tools_config`.

Important behavior:

- Tool Shed tools are added automatically to `shed_tool_conf.xml`; do not hand-author local wrapper XML there.
- Installed tools include Tool Shed metadata such as `tool_shed`, `repository_name`, `repository_owner`, `installed_changeset_revision`, and a Tool Shed-style `guid`.
- Uninstalling a repository removes corresponding entries from shed-related tool panel config and `integrated_tool_panel.xml`.
- `integrated_tool_panel.xml` is generated/maintained by Galaxy; prefer letting Galaxy update it instead of direct edits.
- Integration tests simulate update trouble by changing `shed_tool_conf.xml` and installed repository DB state, then using the Galaxy Tool Shed repository API to check for updates.

Route pure local tool XML questions to `../workflows-and-tools/SKILL.md`.

## Repository Metadata Reset

Tool Shed repository metadata is generated from repository contents and includes tools, invalid tools, repository dependencies, tool dependencies, datatypes, workflows, malicious/downloadable flags, and downloadable revision information. Recent Galaxy code supports reset metadata preview behavior:

- Single repository reset accepts `repository_id`, `dry_run`, and `verbose`.
- `dry_run=True` regenerates metadata in memory without persisting DB changes.
- `verbose=True` can include per-changeset details plus before/after metadata snapshots.
- Dry-run plus verbose is the safest first step for stale metadata, corrupted `tool_config` paths, or suspected dependency metadata changes.
- Successful non-dry-run reset can repair stored tool config paths after a Tool Shed file path or repository location changes.

Preferred investigation order:

1. Identify whether the affected object is a Tool Shed repository or a repository installed into Galaxy.
2. For Tool Shed-side metadata, get the repository id and run/plan a single-repository dry-run reset with verbose output.
3. Inspect `changeset_details`, invalid tool messages, before/after tool config paths, and repository dependency changes.
4. Only run a persisting reset after the user confirms the target shed is safe and the preview looks correct.
5. For a Galaxy server with installed repositories, use Galaxy's installed-repository reset endpoint only when the user intentionally wants to reset installed repository metadata for that Galaxy instance.

## Repository Dependencies

Tool Shed repository dependencies are represented by `<repository>` tags, commonly in `repository_dependencies.xml` or as nested dependency tags in tool dependency definitions. Metadata generation validates and normalizes these attributes:

- `name` and `owner` are required.
- `toolshed` defaults to the current Tool Shed when omitted during population.
- `changeset_revision` is filled with the latest installable revision when possible.
- `prior_installation_required="True"` is preserved when meaningful; false values may be removed during normalization.
- Repository dependencies are currently supported only within the same Tool Shed during this dependency resolution path.
- Circular dependencies and update-to-latest-installable behavior are handled by the repository dependency relation builder.

Troubleshoot dependency failures by checking missing owner/name, invalid changeset revision, dependency pointing at another Tool Shed, circular/prior-installation requirements, and whether the referenced repository has an installable metadata revision.

## Data Managers From Tool Shed Repositories

Data managers can be defined locally or installed through the Tool Shed. Tool Shed install behavior has special table/config side effects:

- Galaxy searches installed repository contents for data-manager config files during installation.
- Non-data-manager repositories that ship `.loc` files should place those files under a shed-specific subdirectory rather than the root `tool_data_path`.
- Shed data table config entries should avoid stamping a `<tool_shed_repository>` sub-element for the non-data-manager `.loc` case covered by integration tests.
- Data-manager table reload and execution still route through Galaxy tools and admin behavior; use this sub-skill for the install/source issue and `../workflows-and-tools/SKILL.md` or admin guidance for the tool/test side.

## Whoosh Search Index

The Tool Shed search index uses Whoosh and indexes repositories plus tools from repository contents. The index build flow:

1. Loads Tool Shed configuration to resolve database connection, `hgweb_config_dir`, `hgweb_repo_prefix`, `whoosh_index_dir`, and `file_path`.
2. Opens two indexes: repository index and tool index under the configured Whoosh directory.
3. Iterates non-deleted, non-deprecated, non-`tool_dependency_definition` repositories ordered by last update time.
4. Reads category names, repository owner/name/description/readme-like fields, lineage from Mercurial, and tool XML metadata from repository files.
5. Deletes/replaces stale indexed documents and commits both writers.

The source index script is service-required: it expects a Tool Shed runtime environment, database access, Mercurial repository paths, and a configured Whoosh index directory. Use the bundled planner to prepare a checklist; do not rebuild a production index without downtime/rollback awareness.

## Service-Required Operations

Some repository scripts are intentionally not bundled as executable replacements because they require a live Tool Shed/Galaxy service and database-backed runtime:

- Test shed bootstrap creates categories/users/repositories, mirrors selected public-shed content, clones Mercurial repositories, pushes to a target shed, and resets metadata.
- Whoosh index build reads Tool Shed config and DB state and writes an index directory.
- Installed repository metadata reset calls a live Galaxy admin endpoint.

For these, produce a dry-run plan, confirm target safety, then use the user's checked-out Galaxy tooling or deployment procedures if execution is explicitly requested.
