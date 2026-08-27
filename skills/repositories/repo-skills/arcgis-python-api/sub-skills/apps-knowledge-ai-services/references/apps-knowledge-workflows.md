# Apps, knowledge, and AI workflow guide

This guide distills the notebook evidence into safe operating patterns for app automation, dependency graphs, Knowledge Graph work, and AI utility probes.

## Fast decision map

| Request type | Use this pattern | Mutates portal or service? |
| --- | --- | --- |
| StoryMap / Briefing / Collection creation or edit | `StoryMap`, `Briefing`, `Collection`, then `add`, `duplicate`, `copy_content`, `save` | Yes |
| Experience Builder item work | `WebExperience`, `preview`, `save`, `clone`, `Templates` | Yes |
| Hub site/page/initiative work | `Hub`, `sites`, `pages`, `initiatives`, `events` managers | Yes |
| Tracker / Workforce / Survey123 launch URLs | `build_tracker_url`, `build_workforce_url`, `build_survey123_url`, related helpers | Usually no, but target apps still need access |
| Dashboard surface support | `arcgis.apps.dashboard` first; probe for `arcgis.apps.dashboards` only if the version supports it | Yes for saves/clones |
| Item dependency graphs | `create_dependency_graph`, `ItemGraph`, `remap_data` | Usually yes when remapping items |
| Knowledge Graph | `KnowledgeGraph`, `query`, `query_streaming`, `apply_edits`, schema methods | Yes for edits/schema |
| AI utility services | `arcgis.ai` functions if the module exists in the target runtime | Usually service-backed |

## StoryMaps, Briefing, and Collection

### When to use

Use the StoryMap family when the user needs to create or modify narrative content items with embedded maps, media, text blocks, or slide-style layouts.

### Core objects

- `StoryMap(item=None, gis=None)`
- `Briefing(item=None, gis=None)`
- `Collection(item=None, gis=None)`

### Important content blocks

StoryMap content commonly uses:

- `Text`
- `Image`
- `Video`
- `Audio`
- `Map`
- `ExpressMap`
- `Gallery`
- `Sidecar`
- `Swipe`
- `Timeline`
- `Code`
- `Table`
- `Embed`
- `Button`
- `Cover`

### Common actions

- `StoryMap.add(content, caption=None, alt_text=None, display=None, position=None)`
- `StoryMap.duplicate(title=None)`
- `StoryMap.copy_content(target_story, node_list)`
- `StoryMap.save(title=None, tags=None, access=None, publish=False, make_copyable=None, no_seo=None)`
- `StoryMap.delete_story()`

For briefings:

- `Briefing.add(layout, sublayout=None, title=None, subtitle=None, section_position=None, position=None)`
- `Briefing.copy_content(target_briefing, content)`
- `Briefing.save(...)`
- `Briefing.delete_briefing()`

For collections:

- `Collection.add(item, title=None, thumbnail=None, position=None)`
- `Collection.remove(index)`
- `Collection.save(...)`
- `Collection.delete_collection()`

### Practical notes

- `duplicate()` is the safest way to preserve structure before editing.
- `copy_content()` is the better fit when only selected nodes or sections should move into a target story.
- `save(publish=True)` can change sharing and item state; treat it as a mutating action.
- Preserve dependent resources such as images, embedded items, and linked maps when cloning or copying.
- If a story depends on content from another item, inspect the item graph before publishing.

## Experience Builder

### When to use

Use the Experience Builder surface when the user needs to clone, preview, or publish a web experience item, especially when the target item may contain embedded resources or linked web maps.

### Core object

- `WebExperience(item=None, path=None, gis=None, template=None, name=None, folder=None)`

### Common actions

- `preview(width=800, height=500)`
- `save(title=None, tags=None, access=None, publish=False, duplicate=False, include_private=None, item_properties={})`
- `clone(target, owner, **kwargs)`
- `delete()`

### Practical notes

- Use `preview()` to inspect a template or existing experience before saving or cloning.
- `path` is for local experience content; `item` is for portal items.
- `clone()` is version-sensitive and may need target-owner and item mapping context.
- Verify dependent web maps, layers, and private resources before cloning across orgs.
- When a user needs a new experience based on an existing one, choose between `save(duplicate=True)` and `clone()` depending on whether the target is the same org or a different destination.

## Hub sites, pages, initiatives, and events

### When to use

Use Hub workflows for site/page/initiative management, cloning, and cleanup tasks.

### Core objects

- `Hub(gis)`
- `SiteManager`, `InitiativeManager`, `PageManager`, `EventManager`
- `Site`, `Initiative`, `Page`, `Event`

### Common actions

- `sites.add(title, subdomain=None)`
- `sites.clone(site, pages=True, title=None)`
- `sites.get(site_id)`
- `sites.search(...)`
- `initiatives.add(title, description=None, site=None)`
- `initiatives.clone(initiative, title=None)`
- `pages.add(title, site=None)`
- `pages.clone(page, site=None)`
- `events.add(event_properties)`

Site and page objects support:

- `add_content(items_list)`
- `add_catalog_group(group_id)` / `delete_catalog_group(group_id)`
- `update(site_properties=None, subdomain=None)`
- `update_layout(layout)`
- `update_theme(theme)`
- `delete()`

### Practical notes

- Cloning a site can also copy pages; verify what is copied before deleting the original.
- Site/page/initiative deletions are destructive.
- Hub workflows often depend on ownership and sharing settings more than on raw item creation.
- Keep catalog groups and content lists in sync with the site design before publishing.

## Tracker, Workforce, Survey123, Collector, Explorer, Field Maps, Navigator

### URL helpers

The apps module provides URL builders for app launch and deep links:

- `build_collector_url(...)`
- `build_explorer_url(...)`
- `build_field_maps_url(...)`
- `build_navigator_url(...)`
- `build_survey123_url(...)`
- `build_tracker_url(...)`
- `build_workforce_url(...)`

### High-level guidance

- Use these helpers to create app launch URLs, not to perform service edits.
- `portal_url`, `url_type`, `webmap`, `assignment`, `assignment_status`, `survey`, and `center` are the common decision points.
- If the URL opens the wrong app, inspect the `url_type` and portal context first.
- If the user lacks the target app privilege or the underlying item is not shared, the URL alone will not fix access.

### Tracker and Workforce objects

- `LocationTrackingManager(gis)` supports `enable()`, `disable()`, and `create_track_view(title)`.
- `TrackView(item)` manages track-view users and mobile users.
- `TrackViewerManager.add/delete/list` and `MobileUserManager.add/delete/list` manage membership.
- `create_project(title, summary=None, major_version=None, gis=None)` creates a Workforce project.
- `Project(item)` loads an existing Workforce project.

### Practical notes

- Location tracking configuration and track-view management are mutating administrative actions.
- Workforce projects are item-backed and include assignments, workers, dispatchers, integrations, and tracks.
- Keep URL helpers in the runtime guidance even when live app editing is not available.

## Dashboards and version-sensitive surfaces

### Important version caveat

The inspection environment confirms `arcgis.apps.dashboard` is available, but `arcgis.apps.dashboards` is not. The dashboard notebook evidence uses the plural module and manager-style APIs, so dashboard support must be treated as version-sensitive.

### Confirmed `arcgis.apps.dashboard` surface

- `Dashboard`
- `add_row(elements, height=1)`
- `add_column(elements, width=1)`
- component builders such as `Header`, `Indicator`, `Details`, `Gauge`, `List`, `PieChart`, `SerialChart`, `CategorySelector`, `DatePicker`, `EmbeddedContent`, `MapLegend`, and `RichText`
- `Dashboard.save(title, description='', summary='', tags=None, gis=None, overwrite=False)`

### Practical notes

- If a user asks for `arcgis.apps.dashboards` or `DashboardManager`, first run the module probe and report the exact runtime gap.
- Do not invent missing dashboard manager classes when the probe says they are absent.
- Treat dashboards as an item-editing workflow, not a generic content CRUD workflow.

## Item dependency graphs

### When to use

Use item graph workflows when a story, web experience, survey, or other app item depends on nested items, broken IDs, or outside-organization references.

### Core API

- `create_dependency_graph(gis, item_list, outside_org=True, **kwargs)`
- `ItemGraph(gis=None, digraph=None)`
- `ItemNode(graph, itemid, item=None)`

### Useful methods

- `ItemGraph.add_dependencies(item_list, outside_org=True, **kwargs)`
- `ItemGraph.add_item(itemid, item=None)`
- `ItemGraph.add_relationship(parent, child)`
- `ItemGraph.update(edges=None, nodes=None)`
- `ItemGraph.to_directed()` / `to_undirected()`
- `load_from_file(path, gis=None, include_items=True)`

### Practical notes

- The graph helps surface dependencies; it does not repair missing portal content automatically.
- `outside_org=True` is useful when the item graph must capture external references.
- For app items with broken embedded IDs, pair the graph with item remapping before saving again.
- `item.remap_data(mapping, force=True)` is a companion pattern when fixing embedded item references in app items.

## Knowledge Graph

### When to use

Use Knowledge Graph workflows for graph-backed entity/relationship services, schema updates, query exploration, streaming query results, and backup/restore-style documentation.

### Service prerequisite

- The service URL should point to a Knowledge Graph service endpoint, typically ending in `KnowledgeGraphServer`.
- A portal connection is still required through `GIS`.

### Core object

- `KnowledgeGraph(url, gis=...)`

### Read/query operations

- `query(query)`
- `query_streaming(query, input_transform=None, bind_param={}, include_provenance=False, as_dict=True)`
- `search(search, category='both', as_dict=True)`
- `query_data_model(as_dict=True)`

### Mutating operations

- `apply_edits(adds=[], updates=[], deletes=[], input_transform=None, cascade_delete=False, cascade_delete_provenance=False, as_dict=True)`
- `named_object_type_adds(...)`
- `named_object_type_delete(...)`
- `named_object_type_update(...)`
- `graph_property_adds(...)`
- `graph_property_delete(...)`
- `graph_property_index_adds(...)`
- `graph_property_index_deletes(...)`
- `graph_property_update(...)`
- `constraint_rule_adds(...)`
- `constraint_rule_deletes(...)`
- `constraint_rule_updates(...)`
- `update_search_index(adds={}, deletes={}, as_dict=True)`
- `sync_data_model(as_dict=True)`

### Backup-oriented guidance

- Separate the data model, entity types, relationship types, and provenance when documenting backups.
- Validate the graph service and data model before trying to write edits.
- Use streaming queries when the user wants row-by-row consumption or provenance-aware output.
- Be explicit that schema edits and cascade deletes can have broad service impact.

## AI-powered utility services

### When to use

Use this section only when the runtime probe confirms the AI module exists and the target service is available.

### Notebook surface

The notebook evidence uses:

- `analyze_image(image=..., prompt=...)`
- `analyze_text(text=..., prompt=...)`
- `translate(text=..., to_language=..., from_language=...)`
- `AIUtilsResponse`

### Practical notes

- AI utility calls are service-backed and version-sensitive.
- If `arcgis.ai` is missing, report the gap instead of guessing a substitute module.
- Treat the AI section as a compatibility check first and a workflow only if the import probe succeeds.
