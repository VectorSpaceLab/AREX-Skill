# Troubleshooting

Use this guide when app cloning, dependency discovery, Knowledge Graph access, or AI utility imports fail.

## 1) Missing modules or version mismatch

### Symptoms

- `ModuleNotFoundError: No module named 'arcgis.apps.dashboards'`
- `ModuleNotFoundError: No module named 'arcgis.ai'`
- Dashboard notebooks mention manager-style APIs that are not importable

### What to check

1. Run `scripts/check_apps_modules.py`.
2. Confirm whether `arcgis.apps.dashboard` is present even if `arcgis.apps.dashboards` is not.
3. Confirm whether the target runtime actually includes the AI utility surface before routing any AI request there.
4. Compare the notebook or user request against the confirmed module surface in `references/app-api-reference.md`.

### Safe response

- Report the exact missing module name.
- Do not invent alternate APIs when the probe says the module is absent.
- If a notebook expects `DashboardManager` but only `arcgis.apps.dashboard` is present, treat the request as version-sensitive and explain the gap.

## 2) StoryMap / Briefing / Collection cloning or editing failures

### Symptoms

- A clone succeeds but embedded maps, images, or linked items disappear.
- `duplicate()` works but the copied story is missing resources.
- `save(publish=True)` changes sharing or item state unexpectedly.

### What to check

1. Inspect the item dependency graph before cloning or publishing.
2. Confirm the target owner, folder, and item privileges.
3. Verify that resource files and relationships were preserved.
4. Distinguish between `duplicate()` for a full local copy and `copy_content()` for selected nodes.

### Safe response

- Keep the original item until the clone opens and renders correctly.
- Preserve dependent item IDs and resource folders when moving content across orgs.
- If a story or experience depends on another item, verify the nested item references before publishing.

## 3) Experience Builder clone/edit problems

### Symptoms

- `preview()` renders but `clone()` or `save()` produces broken references.
- Template-based experiences open but dependent maps or widgets are missing.
- A local path and a portal item are being mixed up.

### What to check

1. Confirm whether the workflow starts from a portal item or a local experience path.
2. Verify dependent web maps, layers, and private resources.
3. Check the destination owner and folder mapping.
4. Confirm whether the request needs `save(duplicate=True)` or a cross-org `clone()`.

### Safe response

- Use `preview()` first.
- Treat cloning as a content-graph operation, not a single-item copy.
- Do not publish a clone until the dependencies are valid.

## 4) Hub site/page/initiative issues

### Symptoms

- Site cloning copies pages unexpectedly.
- Deleting a site removes linked content or breaks page navigation.
- A site or page cannot be found by ID.

### What to check

1. Confirm site, page, and initiative ownership.
2. Check whether the site has linked pages or catalog content that should be preserved.
3. Verify that the user has the privilege to update or delete the target item.
4. Use the manager `search()` or `get()` methods before mutating anything.

### Safe response

- Never delete a site or page until the relationships are mapped.
- Call out that site/page clone and delete operations are destructive.
- Keep the response focused on item relationships and access, not generic content CRUD.

## 5) Tracker / Workforce / Survey123 URL and app launch issues

### Symptoms

- The generated URL opens the wrong app or a blank page.
- Workforce or Survey123 deep links do not respect the expected item.
- The target app is not available to the user.

### What to check

1. Confirm the correct helper: Tracker, Workforce, Survey123, Collector, Explorer, Field Maps, or Navigator.
2. Verify `portal_url`, `url_type`, `webmap`, `assignment`, and `survey` arguments.
3. Confirm that the underlying item is shared and the target app is enabled for the user.

### Safe response

- Explain that the URL helpers only build links; they do not grant access.
- Ask for the target app, portal context, and item identifier when the input is incomplete.

## 6) Item dependency graph confusion

### Symptoms

- A graph is built but missing items are not repaired.
- An app item still has broken embedded IDs after graph creation.
- The graph includes outside-organization references that are hard to interpret.

### What to check

1. Use `create_dependency_graph(gis, item_list, outside_org=True)` to discover dependencies first.
2. Inspect whether the graph is missing broken IDs, external references, or nested resources.
3. Use `ItemGraph.update()` or `item.remap_data()` only after the target replacements are known.

### Safe response

- Explain that dependency graphs reveal structure; they do not fix content automatically.
- Use explicit remapping only when the replacement item IDs are confirmed.

## 7) Knowledge Graph service failures

### Symptoms

- `KnowledgeGraph(url, gis=...)` cannot connect.
- `query_data_model()` fails.
- `apply_edits()` or schema updates are rejected.

### What to check

1. Confirm the URL points to a Knowledge Graph service endpoint, not a portal item page.
2. Confirm the service is enabled and the user has the required privileges.
3. Check whether the graph is read-only or whether edits are allowed.
4. Validate the data model before schema changes or bulk edits.

### Safe response

- Stop if the service endpoint is wrong.
- Separate read/query failures from edit/schema failures.
- Treat cascade deletes and schema mutations as high-risk operations.

## 8) AI utility import failures

### Symptoms

- `arcgis.ai` cannot be imported.
- The notebook expects `analyze_image`, `analyze_text`, or `translate`, but the runtime does not expose them.

### What to check

1. Run `scripts/check_apps_modules.py`.
2. Compare the reported module availability with the notebook or user request.
3. Confirm whether the user is asking for a target-runtime feature that is unavailable in the current environment.

### Safe response

- State that the AI surface is not verified in this runtime if the import probe fails.
- Avoid inventing a substitute module or claiming the feature is available.

## 9) When to stop and ask for more information

Stop and ask for:

- a portal/organization credentialed session
- the target app item ID
- the intended owner or folder
- the knowledge graph service URL
- the dashboard module version expectation
- the exact module name if an import fails

If credentials or service access are missing, return a safe, non-destructive diagnostic checklist instead of a live fix.
