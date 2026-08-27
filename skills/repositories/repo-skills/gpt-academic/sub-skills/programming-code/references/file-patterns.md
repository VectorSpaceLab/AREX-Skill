# File Pattern Reference

Use this when a project is large, mixed-language, or contains generated/vendor files.

## Built-in language routes

| Plugin family | Typical files |
| --- | --- |
| Python | `.py` |
| Java | `.java`, `.xml`, `.jar`, `.sh` |
| C/C++ | `.cpp`, `.hpp`, `.c`, `.h` |
| Frontend | `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.css`, `.less`, `.sass`, `.json` |
| Go | `.go`, `go.mod`, `go.sum`, `go.work` |
| Rust | `.rs`, `.toml`, `.lock` |
| Lua | `.lua`, `.xml`, `.json`, `.toml` |
| CSharp | `.cs`, `.csproj` |
| Matlab | `.m` |

## Manual pattern syntax

GPT Academic docs describe comma-separated patterns with optional `^` prefix for exclusion, such as:

```text
*.py, *.yaml, ^*.pyc, ^node_modules, ^__pycache__
```

Use manual patterns when the source tree mixes languages or when tests/examples should be excluded to stay within the file limit.

## Exclude by default

Exclude large or low-signal paths unless the user explicitly asks for them: `.git`, `node_modules`, dependency lock snapshots except when relevant, minified bundles, model/data caches, generated docs/build output, binary assets, and temporary notebooks with huge outputs.
