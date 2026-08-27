# App, graph, and AI API reference

This file records the runtime facts that were confirmed by import inspection in the current environment.

## Environment facts

- `arcgis` version: `2.4.1.3`
- `arcgis-mapping` version: `4.31.0`
- Base imports succeeded for the ArcGIS package family used by this sub-skill.
- `arcgis.learn` is not part of this sub-skill and was not used for verification here.
- `arcgis.apps.dashboards` is absent in this environment.
- `arcgis.ai` is absent in this environment.
- `arcgis.apps.dashboard` is present in this environment.

## Confirmed module availability

| Module | Status | Notes |
| --- | --- | --- |
| `arcgis.apps.storymap` | present | StoryMap / Briefing / Collection workflows |
| `arcgis.apps.expbuilder` | present | WebExperience workflows |
| `arcgis.apps.itemgraph` | present | Dependency graph workflows |
| `arcgis.apps.hub` | present | Hub site/page/initiative/event workflows |
| `arcgis.apps.tracker` | present | Location tracking and track views |
| `arcgis.apps.survey123` | present | Survey manager / survey item workflows |
| `arcgis.apps.workforce` | present | Workforce project and assignment workflows |
| `arcgis.apps.dashboard` | present | Component-based dashboard builder |
| `arcgis.apps.dashboards` | absent | Version-sensitive notebook surface; do not assume it exists |
| `arcgis.graph` | present | Knowledge Graph service surface |
| `arcgis.ai` | absent | AI utility surface is not available in this inspection runtime |

## `arcgis.apps` URL helper signatures

Confirmed helpers:

- `build_collector_url(webmap=None, center=None, feature_layer=None, fields=None, search=None, portal=None, action=None, geometry=None, callback=None, callback_prompt=None, feature_id=None)`
- `build_explorer_url(webmap=None, search=None, bookmark=None, center=None, scale=None, wkid=None, rotation=None, markup=None, url_type='Web')`
- `build_field_maps_url(portal=None, action=None, webmap=None, scale=None, bookmark=None, wkid=None, center=None, search=None, feature_layer=None, fields=None, geometry=None, use_antenna_height=None, use_loc_profile=None, feature_id=None, callback=None, callback_prompt=None, anonymous=None)`
- `build_navigator_url(start=None, stops=None, optimize=None, navigate=None, travel_mode=None, callback=None, callback_prompt=None, url_type='Web', webmap=None, route_item=None)`
- `build_survey123_url(survey=None, center=None, fields=None)`
- `build_tracker_url(portal_url=None, url_type='Web')`
- `build_workforce_url(portal_url=None, url_type='Web', webmap=None, assignment=None, assignment_status=None)`

These helpers build app launch links; they do not perform service edits.

## StoryMap surface

`arcgis.apps.storymap` exports:

- `StoryMap(item=None, gis=None)`
- `Briefing(item=None, gis=None)`
- `Collection(item=None, gis=None)`
- `Map(item=None, **kwargs)`
- `ExpressMap(**kwargs)`
- block/content classes such as `Text`, `Image`, `Video`, `Audio`, `Gallery`, `Sidecar`, `Swipe`, `Timeline`, `Code`, `Table`, `Button`, `Cover`, and `Embed`

Important methods:

- `StoryMap.add(content=None, caption=None, alt_text=None, display=None, position=None)`
- `StoryMap.copy_content(target_story, node_list)`
- `StoryMap.duplicate(title=None)`
- `StoryMap.save(title=None, tags=None, access=None, publish=False, make_copyable=None, no_seo=None)`
- `StoryMap.delete_story()`
- `Briefing.add(layout, sublayout=None, title=None, subtitle=None, section_position=None, position=None)`
- `Briefing.copy_content(target_briefing, content)`
- `Briefing.duplicate(title=None)`
- `Briefing.save(...)`
- `Collection.add(item, title=None, thumbnail=None, position=None)`
- `Collection.remove(index)`
- `Collection.save(...)`

## Experience Builder surface

`arcgis.apps.expbuilder` exports:

- `WebExperience(item=None, path=None, gis=None, template=None, name=None, folder=None)`
- `Templates`
- `expbuilder`

Important methods:

- `WebExperience.preview(width=800, height=500)`
- `WebExperience.save(title=None, tags=None, access=None, publish=False, duplicate=False, include_private=None, item_properties={})`
- `WebExperience.clone(target, owner, **kwargs)`
- `WebExperience.delete()`

## Hub surface

`arcgis.apps.hub` exports:

- `Hub(gis)`
- `SiteManager`, `InitiativeManager`, `PageManager`, `EventManager`
- `Site`, `Initiative`, `Page`, `Event`

Important methods:

- `SiteManager.add(title, subdomain=None)`
- `SiteManager.clone(site, pages=True, title=None)`
- `SiteManager.get(site_id)`
- `SiteManager.search(title=None, owner=None, created=None, modified=None, tags=None)`
- `InitiativeManager.add(title, description=None, site=None)`
- `InitiativeManager.clone(initiative, title=None)`
- `PageManager.add(title, site=None)`
- `PageManager.clone(page, site=None)`
- `EventManager.add(event_properties)`
- `Site.add_content(items_list)`
- `Site.add_catalog_group(group_id)`
- `Site.update_layout(layout)`
- `Site.update_theme(theme)`
- `Site.delete()`
- `Page.delete()`
- `Initiative.delete()`

## Tracker and Workforce surface

`arcgis.apps.tracker` exports:

- `LocationTrackingManager(gis)`
- `TrackView(item)`
- `TrackViewerManager(track_view)`
- `MobileUserManager(track_view)`

Important methods:

- `LocationTrackingManager.enable(tracks_layer_shards=6, lkl_layer_shards=3, tracks_layer_rolling_index_strategy='Monthly')`
- `LocationTrackingManager.disable()`
- `LocationTrackingManager.create_track_view(title)`
- `TrackView.delete()`
- `TrackViewerManager.add(viewers)` / `delete(viewers)` / `list()`
- `MobileUserManager.add(users)` / `delete(users)` / `list()`

`arcgis.apps.survey123` exports:

- `SurveyManager(gis, baseurl=None)`
- `Survey(item, sm, baseurl=None)`

Important methods:

- `SurveyManager.create(title, folder=None, tags=None, summary=None, description=None, thumbnail=None)`
- `SurveyManager.get(survey_id)`
- `Survey.publish(...)`
- `Survey.download(export_format, save_folder=None)`
- `Survey.create_report_template(...)`
- `Survey.create_sample_report(...)`

`arcgis.apps.workforce` exports:

- `create_project(title, summary=None, major_version=None, gis=None)`
- `Project(item)`
- `Assignment`, `Worker`, `Dispatcher`, `AssignmentType`, `Track`, `Integration`

## Dashboard surface

The confirmed dashboard module in this environment is `arcgis.apps.dashboard`, not `arcgis.apps.dashboards`.

Confirmed objects:

- `Dashboard`
- `add_row(elements, height=1)`
- `add_column(elements, width=1)`
- `Header`, `Indicator`, `Details`, `Gauge`, `List`, `PieChart`, `SerialChart`, `CategorySelector`, `DatePicker`, `EmbeddedContent`, `MapLegend`, `RichText`

Confirmed save method:

- `Dashboard.save(title, description='', summary='', tags=None, gis=None, overwrite=False)`

Notebook evidence also references a plural `arcgis.apps.dashboards` manager-style API with `DashboardManager`, `DependencyOptions`, `ItemMapping`, `LayerMapping`, and `FieldMapping`, but that import is absent in the inspection runtime. Treat that surface as version-sensitive.

## Item dependency graph surface

`arcgis.apps.itemgraph` exports:

- `ItemGraph(gis=None, digraph=None)`
- `ItemNode(graph, itemid, item=None)`
- `create_dependency_graph(gis, item_list, outside_org=True, **kwargs)`
- `load_from_file(path, gis=None, include_items=True)`

Important methods:

- `ItemGraph.add_dependencies(item_list, outside_org=True, **kwargs)`
- `ItemGraph.add_item(itemid, item=None)`
- `ItemGraph.add_relationship(parent, child)`
- `ItemGraph.update(edges=None, nodes=None)`
- `ItemGraph.to_directed()` / `to_undirected()`

## Knowledge Graph surface

Confirmed class:

- `KnowledgeGraph(url, *, gis=None)`

Confirmed methods:

- `query(query)`
- `query_streaming(query, input_transform=None, bind_param={}, include_provenance=False, as_dict=True)`
- `search(search, category='both', as_dict=True)`
- `query_data_model(as_dict=True)`
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

## AI utilities

`arcgis.ai` could not be imported in this inspection runtime, so the AI utility surface is not verified here.

The notebook evidence references:

- `analyze_image(image=..., prompt=...)`
- `analyze_text(text=..., prompt=...)`
- `translate(text=..., to_language=..., from_language=...)`
- `AIUtilsResponse`

Treat those as target-runtime dependent and probe first before relying on them.
