# Repository skills router maintenance

The router is generated from the fixed area -> family taxonomy and the v2
`references/repo-routing-metadata.json` fragment attached to each repository
skill. The compact fragment contains only identity, taxonomy hash, routing
status, and exact assignments. Full classification evidence belongs in the
external production routing-decision artifact, not in the runtime skill graph.

## Import contract

1. Finish and independently verify the generated repository skill.
2. Classify it against the exact taxonomy using repository evidence plus the
   generated skill as navigation context.
3. Write the external routing decision with assignment-specific rationale,
   repository-relative evidence, and assignment-level confidence (`high`,
   `medium`, or `low`).
4. Write the minimal v2 metadata fragment only after the decision is made;
   confidence remains in the central assignment index and is not copied into
   runtime metadata.
5. Run the verified importer/updater under the shared lock so the skill,
   metadata, repository index, assignment index, and router are updated
   together.

The normal importer passes the verified external handoff to the updater with
`--routing-entry`. That handoff supplies the canonical source URL, source
commit, source/target skill roots, and portable skill content digest for the
repository index. Do not infer those fields from a repository name when a
verified handoff is available.

The central `repositories.jsonl` index preserves canonical repository identity,
optional `legacy_repo_id`, source provenance, target skill root, aliases,
content digest, and root description. The central `assignments.jsonl` index
preserves canonical identity, optional `legacy_repo_id`, skill ID, exact
area/family path, and confidence. Unknown fields, duplicate identities, stale
digests, and mismatches with the per-skill metadata are validation errors.

`unclassified` is valid only when no exact family is supported. Ask the user
whether to import it; if they want it included, propose a taxonomy extension
and wait for approval/correction before changing the canonical taxonomy.
`blocked` and `failed` are processing outcomes and must not be imported as
routable skills.

## Generated files

- `references/index/taxonomy.json`: canonical taxonomy snapshot and hash.
- `references/index/repositories.jsonl`: one record per routable repository
  skill, including `repo_id`, `skill_id`, source identity when available, and
  the runtime target root.
- `references/index/assignments.jsonl`: exact `repo_id`, `skill_id`, area, and
  family memberships.
- `references/index/build-metadata.json`: counts, taxonomy hash, index
  digests, and the optional production router run identifier.
- `references/areas/*.md`: one progressive-disclosure page per populated
  area.
- `references/families/<area>/<family>.md`: candidate repository comparison
  pages for populated families.

Use `scripts/update_repo_skills_router.mjs --library-root <library-root>` for a
full rebuild, or `--include-skill <skill-id> --output-router-dir <dir>` for a
filtered export. Use `scripts/import_repo_skill.mjs` for transactional skill
replacement and router updates. Do not edit generated Markdown directly.

For an initial or collection-wide rebuild, use
`verify-repo-skill/scripts/build_repo_skills_collection.mjs` with an
explicit source import manifest, terminal repository manifest, assignment
ledger, canonical taxonomy, and new staging directory. The builder validates
the complete input set before copying any graph, writes the v2 metadata
projection, runs the router updater once, and leaves the staged collection for
the managed library transaction. It must not be emulated by invoking the
single-repository importer once per repository.

The importer stages the replacement and restores both the previous skill and router if the transaction fails.

Do not hand-edit router Markdown as the import mechanism; regenerate it from
the validated metadata and taxonomy instead.
