# Extractor Development and Resolver Debugging

Use this reference for maintainer-style work: adding a language, repairing extractor output, or explaining resolver-created edges. It is intentionally source-checkout agnostic: the procedures describe what to inspect in a Graphify source tree without depending on the original distillation checkout.

## Development decision checklist

Before changing code or telling a user that support exists, establish:

1. **Classification:** Does `detect.classify_file(path)` return `code` for the file, or is it a document/media input?
2. **Dispatch:** Does `_get_extractor(path)` return an extractor function for the exact suffix/content case?
3. **Dependency:** Is the parser module importable, or does the suffix require an optional extra?
4. **Output:** Does the extractor emit at least a file node, valid node/edge fields, and no dangling internal edges?
5. **Resolution:** Are cross-file `calls`, `imports`, `inherits`, `implements`, `references`, or member-call edges handled in the per-file extractor or in a registered resolver pass?
6. **Portability:** Are `source_file` fields scan-root relative, forward-slash normalized, and free of machine-specific absolute paths after `extract()` returns?
7. **Verification:** Which focused tests prove the exact behavior without requiring optional extras or live services?

The bundled inspector covers steps 1-3 safely:

```bash
python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py path/to/file.ext
```

## Required extraction schema

Every extractor fragment should be a dict with at least:

```json
{
  "nodes": [
    {"id": "unique_string", "label": "human name", "file_type": "code", "source_file": "relative/or/raw/path", "source_location": "L42"}
  ],
  "edges": [
    {"source": "id_a", "target": "id_b", "relation": "calls", "confidence": "EXTRACTED", "source_file": "relative/or/raw/path"}
  ]
}
```

Validation facts:

- Required node fields: `id`, `label`, `file_type`, `source_file`.
- Required edge fields: `source`, `target`, `relation`, `confidence`, `source_file`.
- Valid `file_type` values include `code`, `document`, `paper`, `image`, `rationale`, and `concept`.
- Valid confidence labels are `EXTRACTED`, `INFERRED`, and `AMBIGUOUS`.
- `edges` is canonical; legacy `links`, `from`/`to`, and selected legacy field aliases are tolerated by the builder, but new extractors should emit canonical keys.
- Numeric IDs from loose producers are coerced downstream for robustness, but new extractor output should use string IDs.

## Node-ID and `source_file` conventions

Use Graphify's shared normalizer rather than inventing IDs:

- `graphify.ids.normalize_id(s)` performs NFKC normalization, replaces runs of non-word characters with `_`, collapses repeated underscores, strips edges, and casefolds.
- `graphify.ids.make_id(*parts)` joins parts and applies the same normalization.
- Extractor helpers such as `_make_id` and `_file_stem` use the same recipe; use the local helper pattern already used by adjacent extractors.
- A file node should be present for supported source files. Zero-node results are anomalous and are not cached.
- After `extract(..., root=<scan_root>)`, `source_file` should be portable and root-relative when the source is inside the scan root. Backslashes are normalized to forward slashes.
- Absolute-path-derived node IDs and edge endpoints are remapped after extraction. Tests assert that no temporary/root slug leaks into node IDs or endpoints.
- Pre-#1504 legacy file IDs used only a short file stem and can collide across directories; current IDs are path-qualified. Read-only commands may warn that an existing graph should be rebuilt to get path-qualified IDs.

When diagnosing duplicate IDs, compare both `id` and `source_file`; same labels in different files are expected, same canonical IDs for different files are usually a bug.

## Edge direction rules

Extractor output uses directional edge semantics:

| Relation family | Direction to preserve |
|---|---|
| `contains` / `method` / `case_of` | container or file `source` -> contained symbol `target` |
| `calls` / `indirect_call` / script invocation | caller `source` -> callee `target` |
| `imports`, `imports_from`, `re_exports` | importing/re-exporting source -> imported target/file/symbol |
| `inherits`, `implements`, `mixes_in` | derived/implementing type -> base/protocol/trait |
| `references`, `depends_on`, `uses`, `instantiates` | referring owner -> referred dependency/target |

Graphify may build an undirected NetworkX graph for backward compatibility, but it stores the original endpoints in `_src`/`_tgt` and export restores `source`/`target`. Do not reverse extractor output to match a traversal display. If the user is confused by `query`, `path`, or `explain` rendering, route to [query-navigation](../../query-navigation/SKILL.md).

## Resolver registry

Some edges require whole-corpus or language-specific resolution after per-file extraction. `graphify.resolver_registry` defines:

- `LanguageResolver(name, suffixes, resolve)`, where `resolve(per_file, all_nodes, all_edges) -> None` mutates lists in place.
- `register(resolver)` to append to the ordered global registry.
- `run_language_resolvers(paths, per_file, all_nodes, all_edges)` to run only resolvers whose suffix appears in the current corpus.

Behavior pinned by tests:

- Suffix gating: a resolver runs only when at least one matching suffix is present.
- Order preservation: registered resolvers run in registration order.
- Fault isolation: a failing resolver logs a warning and later resolvers still run.
- In-place mutation: resolvers append or adjust nodes/edges directly.

Known registered resolver names in the verified package:

| Resolver | Suffixes | Purpose |
|---|---|---|
| `swift_member_calls` | `.swift` | Swift member-call resolution. |
| `python_member_calls` | `.py` | Python import/member/alias-guided calls. |
| `ruby_member_calls` | `.rb .rake` | Ruby member-call resolution. |
| `typescript_member_calls` | `.js .jsx .mjs .cjs .ts .tsx .mts .cts` | JS/TS member/import-aware calls and workspace/barrel resolution support. |
| `cpp_member_calls` | `.c .h .cpp .cc .cxx .hpp .cu .cuh .metal` | C/C++/CUDA/Metal member-call handling. |
| `objc_member_calls` | `.m .mm .h` | Objective-C member/message resolution. |
| `csharp_member_calls` | `.cs` | Receiver-typed C# member calls. |
| `java_member_calls` | `.java` | Java member-call handling. |
| `pascal_inherited_calls` | `.pas .pp .dpr .dpk .inc` | Cross-file inherited-method calls for Pascal/Delphi generated-base/manual-descendant patterns. |
| `kotlin_qualified_calls` | `.kt .kts` | Kotlin fully qualified calls such as `com.pkg.Fn()` / object method calls. |

Shared symbol-resolution helpers enforce conservative behavior: skip member calls in the generic raw-call pass, skip ambiguous duplicate labels unless a tie-breaker is decisive, require code nodes for callable targets, and avoid cross-language phantom edges.

## Adding or repairing a language extractor

Follow this minimal workflow in a Graphify source checkout:

1. Reproduce the support claim with a tiny fixture and the bundled inspector. Determine whether the issue is classification, dispatch, missing extra, parser behavior, or resolver output.
2. If adding a new suffix, update all relevant registries: detection code extensions, extractor dispatch, watch/update watched extensions, optional dependency metadata if the parser is optional, and documentation/source-format tables.
3. Emit a file node before symbol nodes. A supported file that produces zero nodes is treated as anomalous and retried on the next run instead of being cached.
4. Emit canonical node/edge fields only. Include `source_file` and `source_location` where possible.
5. Use `make_id`/extractor helper ID generation. Avoid raw absolute paths in IDs; pass the scan root to `extract()` in tests so relativization is exercised.
6. Keep same-file extraction and cross-file resolver logic separate when language knowledge requires whole-corpus context. Register a `LanguageResolver` instead of adding another ad hoc tail block.
7. Add focused tests under `tests/fixtures/` and `tests/test_languages.py` or a resolver-specific test. Prefer a small fixture that asserts nodes, edges, confidence/context, and no dangling endpoints.
8. If moving an existing extractor into `graphify/extractors/`, preserve behavior: one language per change, keep facade re-exports from `extract.py`, do not invert import direction (`extract.py` may import `extractors/`, but extractor modules should not import `graphify.extract`), and use registry identity tests for the move.

## Focused test commands

Run only the subset that proves the change. Examples:

```bash
# Core extractor and resolver registry behavior
pytest tests/test_language_resolvers.py -q

# Language fixtures; narrow with -k to the affected language when optional extras are absent
pytest tests/test_languages.py -q
pytest tests/test_languages.py -k 'python or js or terraform or dm or pascal' -q

# Import/call/symbol resolution surfaces
pytest tests/test_python_import_resolution.py tests/test_js_import_resolution.py tests/test_symbol_resolution.py -q

# Portability, legacy IDs, non-string IDs, zero-node cache behavior
pytest tests/test_node_id_canonical.py tests/test_non_string_node_ids.py tests/test_zero_node_no_cache.py tests/test_semantic_id_remap_root.py -q
```

Optional-parser cases (`sql`, `terraform`, `dm`, AST-quality `pascal`) require their extras in the test environment. If the extra is not installed, verify metadata/help and route live parser tests to a focused optional verification case instead of failing the base skill.

## Pre-merge review checklist

- Inspector output for the new/changed suffix is correct.
- Extraction of a tiny fixture returns at least one file node and no schema errors.
- `validate.validate_extraction(result)` returns no real schema errors for the fixture.
- Every non-external edge endpoint refers to an emitted node after build-time normalization.
- Direction matches the relation semantics above.
- Optional missing parser behavior is explicit and actionable.
- No source checkout path or temporary directory slug appears in node IDs, edge endpoints, or persisted `source_file` values.
- Focused tests pass; skipped optional tests are documented with the missing extra/service reason.
