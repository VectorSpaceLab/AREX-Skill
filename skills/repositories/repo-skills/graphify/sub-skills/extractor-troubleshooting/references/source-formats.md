# Source Formats and Extractor Coverage

This reference is for extractor support decisions. It distinguishes **file detection** (`graphify.detect.classify_file`) from **extractor dispatch** (`graphify.extract`), because a file can be recognized as a document/media input without using the AST extractor registry, or recognized as code while still lacking an AST extractor.

## Package and dependency identity

- Install distribution: `graphifyy`.
- Import package and CLI: `graphify`.
- Base install includes the core `tree-sitter` runtime and default language wheels for Python, JavaScript/TypeScript, Go, Rust, Java, Groovy, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, PowerShell, Elixir, Objective-C, Julia, Verilog/SystemVerilog, Fortran, Bash, and JSON.
- Optional language-parser extras are install variants of the same package: `graphifyy[sql]`, `graphifyy[terraform]`, `graphifyy[dm]`, and `graphifyy[pascal]`.

Use the same package manager/environment that runs Graphify. For example, if Graphify was installed with `uv tool`, install the extra with the matching `uv tool install "graphifyy[terraform]"` style; if it was installed in a venv, use that venv's `pip install "graphifyy[terraform]"`.

## Detection versus extractor dispatch

Graphify has two relevant layers:

| Layer | Evidence-backed behavior | Why it matters for failures |
|---|---|---|
| File classification | `detect.classify_file(path) -> FileType | None` returns `code`, `document`, `paper`, `image`, or `video` when a path is part of the corpus. | Explains why an extension is ignored or routed to semantic/media extraction rather than AST. |
| AST/source dispatch | `extract.extract(paths, root=..., cache_root=...)` routes code-like files through `_get_extractor(path)` and the extractor dispatch map. | Explains zero-node files, missing parser extras, resolver behavior, and node/edge schema. |
| Special routing | Filename and content sniffing can override simple suffixes. | `.h`, `.m`, package manifests, MCP configs, `.blade.php`, and extensionless shebang scripts need more than suffix matching. |

Do not assume that every detected file has an AST extractor. At Graphify v0.9.39, `.r`, `.ejs`, and `.ets` are classified as code but have no AST extractor dispatch; extraction surfaces them as `code_without_ast_extractor`-style warnings rather than producing graph nodes.

## Source-code extractor registry

The installed package exposes an extractor dispatch table with these evidence-backed groups:

| Extractor route | Extensions / cases | Notes |
|---|---|---|
| Python | `.py`; extensionless `python`, `python2`, `python3` shebangs | Python import-guided resolver handles selected `from ... import ...` calls conservatively. |
| JavaScript / TypeScript | `.js .jsx .mjs .cjs .ts .tsx .mts .cts`; extensionless `node`/`nodejs` shebangs | JS/TS import resolution handles relative files, index files, barrel re-exports, tsconfig/jsconfig paths, workspace packages, Svelte/Astro/Vue script contexts. |
| Go / Rust / JVM | `.go .rs .java .groovy .gradle .kt .kts .scala` | JVM-family cross-language filtering allows Java/Kotlin/Scala/Groovy interop while blocking unrelated languages. |
| C-family / Apple | `.c .h .cpp .cc .cxx .hpp .cu .cuh .metal .m .mm .swift` | `.h` is sniffed for Objective-C or C++ markers; otherwise it stays C. `.m` is parsed as Objective-C only when it carries Objective-C markers, avoiding MATLAB/Octave garbage nodes. |
| Ruby / C# / PHP / Lua / Zig | `.rb .rake .cs .php .lua .luau .toc .zig`; extensionless `ruby`, `php`, `lua` shebangs | Ruby and C# have member-call resolver passes; PHP is case-insensitive for identifier lookup. |
| Shell / PowerShell / Elixir / Julia / Fortran | `.sh .bash .ps1 .psm1 .psd1 .ex .exs .jl .f .F .f90 .F90 .f95 .F95 .f03 .F03 .f08 .F08`; extensionless `bash`, `sh`, `dash`, `zsh`, `ksh`, `julia` shebangs | Extensionless shebang support is intentionally narrower than detection; `perl`, `fish`, `tcsh`, and `Rscript` can classify as code but have no AST extractor. |
| Frontend SFC / templates | `.vue .svelte .astro .razor .cshtml .xaml .blade.php` | `.blade.php` is matched by full filename suffix before generic `.php`. |
| Dart / Verilog / Salesforce Apex | `.dart .v .sv .svh .cls .trigger` | Apex is regex-based and handles classes, interfaces, enums, methods, triggers, SOQL/DML edges. |
| .NET/project graph files | `.sln .slnx .csproj .fsproj .vbproj` | Deterministic project/package/dependency extraction, not semantic text extraction. |
| JSON/config | `.json`, PowerShell `.psd1`, MCP config filenames | MCP configs are routed by filename before generic JSON. |
| Markdown-like deterministic route | `.md .mdx .qmd .skill` | Full pipeline classification can treat docs as semantic `document` inputs; the extractor registry also has a deterministic markdown route for headings/links when called through AST-style APIs. |

## Optional language extras

| Extra | Parser module | Extensions | Hard failure when missing? | Notes |
|---|---|---|---|---|
| `sql` | `tree_sitter_sql` | `.sql` | Yes | Extracts tables, views, functions/procedures, triggers, foreign-key/reference-style edges. Missing parser produces an extractor error and a warning recommending `graphifyy[sql]`. |
| `terraform` | `tree_sitter_hcl` | `.tf .tfvars .hcl` | Yes | Extracts resources, data sources, modules, variables, outputs, providers, locals, `references`, and `depends_on`. Node IDs are module-directory scoped because Terraform resources are directory/module scoped. |
| `dm` | `tree_sitter_dm` | `.dm .dme` | Yes | Extracts BYOND DreamMaker types, procs, includes, calls, and instantiations. Wheels may not exist for every platform; source builds can require a C compiler and Python headers. |
| none for BYOND side formats | standard library parsers | `.dmi .dmm .dmf` | No | `.dmi` reads BYOND icon metadata, `.dmm` reads map tile type paths, `.dmf` reads interface windows/controls. These do not require `tree_sitter_dm`. |
| `pascal` | `tree_sitter_pascal` | `.pas .pp .dpr .dpk .lpr .inc` | No hard failure | Graphify falls back to a regex Pascal/Delphi extractor when the parser is absent or parse setup fails. Install `graphifyy[pascal]` for the more accurate AST path and richer calls/inherits edges. |

## Deterministic special files

| Case | Routing rule | Debug note |
|---|---|---|
| Package manifests | `apm.yml`, `pyproject.toml`, `go.mod`, `pom.xml` classify as code and create canonical package/dependency nodes. | Filename wins over `.yml`/`.toml` document intuition. |
| MCP configs | `.mcp.json`, `mcp.json`, `mcp_servers.json`, `claude_desktop_config.json` route to MCP-aware config extraction. | Generic JSON extraction would miss server/package/env-var semantics. |
| `.h` headers | Sniff Objective-C markers first, then C++ markers, else parse as C. | A wrong-looking C header with `class`/`namespace` routes to C++ intentionally. |
| `.m` files | Sniff Objective-C markers; without markers, no AST extractor is returned. | MATLAB/Octave `.m` files are currently not parsed to avoid Objective-C garbage nodes. |
| Extensionless shebangs | Detection recognizes many interpreters; extractor dispatch supports Python, Bash/sh family, Node, Ruby, Lua, PHP, and Julia. | Perl/fish/tcsh/Rscript shebang files can be classified as code but skipped by extractor dispatch. |

## Non-code and semantic/media formats

Graphify also handles non-code inputs, but those are not extractor-maintainer AST bugs unless a deterministic code route is involved.

| Family | Extensions / input | Dependency or runtime boundary | Route if the task is not extractor-specific |
|---|---|---|---|
| Documents | `.txt .rst .html .yaml .yml` plus markdown-like docs in the full pipeline | Semantic extraction can require a configured model/backend unless `--code-only` skips docs. | [graph-building](../../graph-building/SKILL.md) for build choices; [query-navigation](../../query-navigation/SKILL.md) for interpreting an existing graph. |
| PDFs | `.pdf` | `graphifyy[pdf]` for PDF text extraction in package-managed flows. | [graph-building](../../graph-building/SKILL.md). |
| Office | `.docx .xlsx` | `graphifyy[office]`; resource caps guard zip/XML bombs. | [graph-building](../../graph-building/SKILL.md). |
| Google Workspace shortcuts | `.gdoc .gsheet .gslides` | opt-in `gws` auth and `--google-workspace`; Sheets need `graphifyy[google]`. | [graph-building](../../graph-building/SKILL.md). |
| Images | `.png .jpg .jpeg .gif .webp .svg` | Semantic/vision path when enabled; note `.svg` is also an export extra for output generation. | [graph-building](../../graph-building/SKILL.md) or [exports-integrations](../../exports-integrations/SKILL.md) depending on input vs output. |
| Video/audio/URLs | `.mp4 .mov .webm .mkv .avi .m4v .mp3 .wav .m4a .ogg` and video URLs | `graphifyy[video]`, model cache/network boundaries. | [graph-building](../../graph-building/SKILL.md). |

## Safe support inspection

Use the bundled script before guessing:

```bash
python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py suspicious.tf suspicious.pas suspicious.dm
python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py --recursive path/to/repo --max-files 2000
```

The script reports classification, extractor name, optional-extra status, and parser module availability. It does not execute user files and does not build a graph.
