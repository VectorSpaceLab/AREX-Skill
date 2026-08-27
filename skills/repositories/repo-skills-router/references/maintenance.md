# Router maintenance

This router is generated from the fixed area -> family taxonomy and the v2 `references/repo-routing-metadata.json` fragment attached to each repository skill. The compact fragment contains only identity, taxonomy hash, status, and exact assignments. Full classification evidence belongs in the external production routing decision artifact, not in the runtime skill graph.

## Import contract

1. Finish and independently verify the generated repository skill.
2. Classify it against the exact taxonomy using repository evidence plus the generated skill as navigation context.
3. Write the external routing decision with assignment-specific rationale, evidence, and assignment-level confidence (`high`, `medium`, or `low`).
4. Write the minimal v2 metadata fragment only after the decision is made; confidence remains in the central assignment index and is not copied into runtime metadata.
5. Run the verified importer/updater under the shared lock so the skill, metadata, indexes, and router are updated together.

The central `repositories.jsonl` index preserves canonical repository identity, optional `legacy_repo_id`, source provenance, target skill root, aliases, content digest, and root description. The central `assignments.jsonl` index preserves canonical identity, optional `legacy_repo_id`, skill ID, exact area/family path, and confidence. These generated indexes are validated together with the per-skill metadata; unknown fields, duplicate identities, stale digests, and mismatched assignments are errors.

`unclassified` is valid only when no exact family is supported. Ask the user whether to import it; if they want it included, propose a taxonomy extension and wait for approval/correction before changing the canonical taxonomy. `blocked` and `failed` are processing outcomes and must not be imported as routable skills.

## Current generated scope

- Areas in taxonomy: 20
- Routable repository skills: 1000
- Taxonomy memberships: 2204

Use `node update_repo_skills_router.mjs --library-root <library-root>` for a full rebuild, or `--include-skill <skill-id>` with `--output-router-dir <dir>` for a filtered export.
