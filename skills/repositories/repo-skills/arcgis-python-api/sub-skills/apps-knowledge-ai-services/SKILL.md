---
name: apps-knowledge-ai-services
description: "Route StoryMaps, Experience Builder, Hub, dashboard surfaces,
  Tracker/Workforce/Survey URLs, item dependency graphs, Knowledge Graph
  operations, and AI-powered ArcGIS services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Apps, knowledge, and AI services

Use this sub-skill for ArcGIS app automation and service-backed app workflows:

- StoryMaps, Briefing, Collection, and other story content blocks
- Experience Builder and web experience cloning/editing
- Hub sites, pages, initiatives, and event-aware site workflows
- Dashboard surfaces and version-sensitive dashboard manager behavior
- Tracker, Workforce, Survey123, Collector, Explorer, Field Maps, and Navigator URL helpers
- Item dependency graphs and app-item remapping
- Knowledge Graph query, edit, schema, and backup flows
- AI-powered utility services when the module surface is present

## Route away when the request is about

- generic GIS content CRUD, users, groups, or admin/server operations
- geocoding, routing, map display, geoenrichment, or other location services
- deep learning model training, inference, or GPU notebook workflows

## Entry checklist

1. Run `scripts/check_apps_modules.py` to confirm which app/graph/AI modules are actually available.
2. Read `references/apps-knowledge-workflows.md` for the workflow pattern that matches the task.
3. Read `references/app-api-reference.md` for confirmed module names, signatures, and version caveats.
4. Use `references/troubleshooting.md` before proposing a fix for clone, publish, dependency, or service errors.

## Safety rules

- Treat `save`, `publish`, `clone`, `duplicate`, `copy_content`, `remap_data`, `apply_edits`, `enable`, `disable`, and `delete` as mutating operations.
- Preserve item resources, relationships, ownership, and dependent IDs when cloning StoryMaps or Experience Builder items.
- Do not assume `arcgis.apps.dashboards` or `arcgis.ai` exist; confirm with the probe first.
- Do not execute live service calls unless the user has provided the required credentials, privileges, and target environment.
- Do not use this sub-skill for raw portal content maintenance, map analysis, or model training.

## Start here

- [`references/apps-knowledge-workflows.md`](references/apps-knowledge-workflows.md)
- [`references/app-api-reference.md`](references/app-api-reference.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`scripts/check_apps_modules.py`](scripts/check_apps_modules.py)
