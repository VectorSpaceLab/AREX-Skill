# Extractor Troubleshooting

This runbook is for source-format and extractor-root-cause failures. If the user simply needs to build/update a graph, route to [graph-building](../../graph-building/SKILL.md). If the graph exists and the issue is query/path/explain interpretation, route to [query-navigation](../../query-navigation/SKILL.md).

## First safe checks

1. Inspect support without building a graph or executing user code:

   ```bash
   python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py path/to/file.ext
   python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py --recursive path/to/repo --max-files 2000
   ```

2. For an existing `graph.json` with duplicate/collapsed-edge symptoms, run the read-only CLI diagnostic:

   ```bash
   graphify diagnose multigraph --graph graphify-out/graph.json --max-examples 10
   graphify diagnose multigraph --graph graphify-out/graph.json --json --max-examples 10
   ```

3. If the output points to build/update/cache behavior rather than extractor output, stop here and use [graph-building](../../graph-building/SKILL.md).

## Symptom-to-cause table

| Symptom | Likely cause | Evidence to gather | Recovery / answer |
|---|---|---|---|
| `.tf`, `.tfvars`, or `.hcl` files are ignored or produce zero nodes | `terraform` extra missing (`tree_sitter_hcl` not importable) or files excluded before classification | Inspector should show `classification=code`, `extractor=extract_terraform`, `missing_extra=terraform` when parser is missing | Install `graphifyy[terraform]` in the Graphify runtime environment, then re-run the extraction/update flow via [graph-building](../../graph-building/SKILL.md). |
| `.sql` files contribute nothing | `sql` extra missing (`tree_sitter_sql` not importable) | Inspector: `missing_extra=sql`; extract warnings can mention missing dependency and `graphifyy[sql]` | Install `graphifyy[sql]`; then rerun focused SQL fixture/native test if maintaining extractor behavior. |
| `.dm` or `.dme` files fail on Linux/macOS | `dm` extra missing or `tree-sitter-dm` wheel unavailable for the platform, requiring source build toolchain | Inspector: `missing_extra=dm`; import check for `tree_sitter_dm` false | Explain optional extra/platform wheel boundary. Install `graphifyy[dm]` with a working compiler/Python headers, or document the capability as unavailable on that environment. |
| `.dmi`, `.dmm`, `.dmf` files work even though `tree_sitter_dm` is absent | These BYOND side formats use standard-library/parsing helpers, not `tree_sitter_dm` | Inspector should show extractor available and no hard missing extra | Do not tell the user to install `graphifyy[dm]` for these side formats unless `.dm`/`.dme` AST extraction is also needed. |
| `.pas`, `.pp`, `.dpr`, `.dpk`, `.lpr`, or `.inc` has fewer calls/inherits than expected | Parser extra absent, so Graphify used Pascal regex fallback, or the fallback could not infer the language-specific edge | Inspector should show `optional_ast_extra=pascal` and whether `tree_sitter_pascal` is importable | Install `graphifyy[pascal]` for AST-quality extraction. If already installed, use Pascal-focused tests and resolver checks. |
| `.r`, `.ejs`, or `.ets` classified as code but absent from graph | Detection knows the extension as code, but extractor dispatch has no AST route | Inspector: `status=code_without_ast_extractor` | State that Graphify currently lacks an AST extractor for that suffix. Do not promise support; open or implement language support. |
| MATLAB/Octave `.m` file missing | `.m` is only routed to Objective-C when Objective-C markers are present | Inspector likely reports `classification=code` and `status=code_without_ast_extractor` for marker-free `.m` | Explain Graphify intentionally avoids parsing MATLAB as Objective-C garbage. Add MATLAB support separately if needed. |
| C/C++/Objective-C header routed unexpectedly | `.h` is sniffed: Objective-C markers first, then C++ markers, otherwise C | Inspector reports the extractor chosen after reading a small header prefix | Inspect the file head for `@interface`, `@protocol`, `@implementation`, `#import`, `class`, `namespace`, `template`, `::`, etc. False positives should be fixed in sniffing tests. |
| Extensionless script classified as code but absent | Detection recognizes a shebang interpreter that extractor dispatch does not support | Inspector shows `classification=code` with no extractor | Supported shebang extractor interpreters include Python, Bash/sh family, Node, Ruby, Lua, PHP, and Julia. Perl/fish/tcsh/Rscript are classified but not AST-extracted. |
| Supported file produces `zero nodes` warning | Extractor accepted the file but returned no nodes; every supported file should emit at least a file node | Extract warning names up to a few files; focused fixture can reproduce | Re-run once because zero-node results are not cached. If persistent, add/repair fixture and extractor; do not stamp the file as successfully indexed. |
| Files stay stale after a missing-extra or zero-node failure | Manifest/cache kept old AST hashes before the failure was fixed, or update path did not requeue failed AST sources | Extract warnings may mention failed AST sources; manifest repair belongs to build/update flow | Route rebuild/update mechanics to [graph-building](../../graph-building/SKILL.md). The extractor fact is that failed AST sources should be retried after dependency fixes. |
| Duplicate nodes after update | Legacy pre-path-qualified IDs, absolute path slug leakage, or same label across files misunderstood as duplicate | Check whether IDs are path-qualified; `graphify` read-only commands can warn about pre-#1504 IDs; run ID canonical tests in maintainer checkout | Explain that current IDs are derived from repo-relative path stems. For actual legacy graph data, rebuild via graph-building guidance; for extractor code, use `make_id` and `root=` tests. |
| Edge points to a missing node | Extractor emitted dangling internal edge, optional external import edge, or build dropped an external/stdlib target | `validate.validate_extraction(result)` reports unmatched endpoints; fixture tests often assert no dangling edges | External/stdlib edges can be expected, but internal language edges should target emitted nodes or source-less stubs that can be rewired. Add focused language tests. |
| User says direction is wrong | Query/path traversal can walk reverse or an undirected graph can store `_src`/`_tgt`; extractor output may still be correct | Check raw/persisted `source`/`target` and relation semantics | Extractor edges should remain directional. If the complaint is display/traversal, route to [query-navigation](../../query-navigation/SKILL.md). |
| Same endpoint has multiple relations/contexts and output seems collapsed | Building an undirected simple graph can collapse parallel same-endpoint edges; Graphify has diagnostics for collapse risk | Run `graphify diagnose multigraph --graph ...` | Use diagnostic output to decide whether the producer must preserve relation/context/source-location or whether a MultiDiGraph-related change is needed. |
| Non-string IDs from generated/semantic data crash or disconnect edges | Loose producer emitted numeric IDs/endpoints/hyperedge members | Build tests cover numeric coercion; validation reports non-hashable IDs | New extractor output must emit string IDs. Builder coerces numeric scalars defensively, but lists/dicts/bools remain invalid. |
| Graph contains absolute local paths | Extractor or semantic producer emitted absolute `source_file`/IDs without root remap | ID canonical tests assert no scan-root slug in node IDs/endpoints | Pass the scan root to `extract()`, rely on source_file relativization, and avoid raw path strings as standalone IDs. |

## Optional-extra diagnosis details

Use parser-module import facts, not guesswork:

| Extra | Module checked by inspector | Hard-missing behavior |
|---|---|---|
| `sql` | `tree_sitter_sql` | `.sql` extractor returns an error and contributes no nodes. |
| `terraform` | `tree_sitter_hcl` | `.tf`, `.tfvars`, `.hcl` extractor returns an error and contributes no nodes. |
| `dm` | `tree_sitter_dm` | `.dm`, `.dme` extractor returns an error and contributes no nodes. |
| `pascal` | `tree_sitter_pascal` | No hard failure; regex fallback runs, but AST-quality edges may be missing. |

If an optional parser is absent in the base environment, document it as an optional limitation unless the user specifically asks to install and verify that extra.

## Focused maintainer tests

When a source checkout is available, choose the smallest relevant subset:

```bash
# Registry mechanics and fault isolation
pytest tests/test_language_resolvers.py -q

# Language fixtures; use -k to avoid extras not installed in this environment
pytest tests/test_languages.py -k 'terraform or sql or dm or pascal' -q

# Python / JS / generic symbol resolution
pytest tests/test_python_import_resolution.py tests/test_js_import_resolution.py tests/test_symbol_resolution.py -q

# ID/source_file/zero-node invariants
pytest tests/test_node_id_canonical.py tests/test_non_string_node_ids.py tests/test_zero_node_no_cache.py tests/test_semantic_id_remap_root.py -q
```

Do not run optional parser-specific tests as a base verification gate unless the matching extra is installed.

## Hard synthetic cases to keep in review

1. A user says `.tf`, `.pas`, and `.dm` files are ignored on a fresh install. Expected diagnosis: `.tf` needs `graphifyy[terraform]`; `.dm`/`.dme` need `graphifyy[dm]` and may hit platform wheel/build-tool issues; `.pas` still has a regex fallback but `graphifyy[pascal]` improves AST-quality calls/inherits.
2. A user reports duplicate or zero-node outputs after an update. Expected diagnosis: separate zero-node non-cache retry from legacy/path-qualified ID migration; explain `source_file` root-relative normalization and route rebuild/update mechanics to [graph-building](../../graph-building/SKILL.md).
