---
name: gis-admin-content
description: "Operate ArcGIS GIS authentication, content, item resources, users,
  groups, organization administration, cloning, and safe backup workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GIS administration and content router

Use this sub-skill when the task involves the ArcGIS `GIS` object, authentication profiles, content and item lifecycle, item resources, user/group administration, organization settings, federated servers, collaborations, portal cloning or offline content backup.

Do **not** use this sub-skill for feature-layer analysis, Spatially Enabled DataFrames, mapping widgets/location services, raster/imagery analytics, deep learning, StoryMap/Experience/Knowledge-specific edits, or deployment packaging. Route those to the matching sibling sub-skill or the root skill.

## Operating rules

- Treat all authenticated ArcGIS Online/Enterprise calls as remote service calls. They are not safe to execute unless the user supplies the target portal/org, credentials or profile, required privileges, and explicit approval for the operation class.
- Never paste, log, persist, or echo passwords, tokens, certificate passwords, API keys, client secrets, or profile contents. If a password is needed interactively, prompt through secret input or ask the user to configure a profile outside the response.
- Keep `verify_cert=True` by default. Only use `verify_cert=False` for a controlled diagnostic against a known non-production/self-signed endpoint after warning about man-in-the-middle risk.
- Before any create, publish, share, clone, credit, server, collaboration, reassign, unprotect, or delete operation, perform the preflight and rollback checklist in [admin-content-workflows.md](references/admin-content-workflows.md).
- Do not run or copy bundled portal-population, cleanup, setup, teardown, or clone samples as runtime helpers. They are credentialed and destructive; use only the distilled safety patterns in the references.

## Reference map

- [Admin/content workflows](references/admin-content-workflows.md): connection modes, safe content CRUD, resources, users/groups, admin/server/collaboration, cloning, offline backup, and source-script safety boundaries.
- [API reference](references/api-reference.md): verified installed signatures and common object/method patterns for `GIS`, `Item`, content, resources, users, groups, admin, servers, and collaborations.
- [Troubleshooting](references/troubleshooting.md): missing credentials, profile/keyring failures, SSL/cert issues, privilege errors, clone/delete failures, offline backup issues, and recovery after partial mutations.

## First response pattern

1. Identify whether the user is asking for read-only inventory, reversible mutation, or destructive/admin mutation.
2. Ask for the minimum missing portal/profile/credential/privilege details; if missing, provide a dry-run plan only.
3. Use [api-reference.md](references/api-reference.md) for exact constructor and method parameters.
4. Use [troubleshooting.md](references/troubleshooting.md) when authentication or portal calls fail.
5. For destructive operations, require a human-readable target list, backup/rollback plan, and explicit confirmation before proceeding.
