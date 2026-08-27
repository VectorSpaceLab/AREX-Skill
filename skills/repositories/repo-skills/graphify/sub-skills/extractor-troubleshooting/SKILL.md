---
name: extractor-troubleshooting
description: "Troubleshoot Graphify source-format support, language extractors,
  resolver behavior, node IDs, and extractor-specific graph failures."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Extractor Troubleshooting

Use this sub-skill when a Graphify user or maintainer needs to explain why a file type was or was not extracted, debug language-specific AST output, reason about resolver-created edges, or investigate zero-node/duplicate-ID extractor symptoms.

Start from the root router when the task is not clearly extractor-specific: [graphify](../../SKILL.md).

## Use this when

- A source file extension is ignored, classified as code without an AST extractor, or requires an optional language extra.
- A `.tf`, `.tfvars`, `.hcl`, `.sql`, `.pas`, `.pp`, `.dpr`, `.dpk`, `.inc`, `.dm`, `.dme`, `.dmi`, `.dmm`, or `.dmf` report needs parser/extra guidance.
- A maintainer is adding, migrating, or debugging a language extractor or resolver.
- Graph output has zero-node warnings, duplicate/legacy node IDs, wrong `source_file` normalization, dangling extractor edges, or same-endpoint edge-collapse risk.
- A focused native test list is needed for language extractor or resolver changes.

## Route elsewhere

- Ordinary build, update, cache, manifest, `--code-only`, or `graphify-out/` creation workflow: [graph-building](../graph-building/SKILL.md).
- Query/path/explain interpretation, user-facing traversal direction, ambiguous query labels, or MCP serving: [query-navigation](../query-navigation/SKILL.md).
- Assistant install, packaged skill, hooks, or always-on troubleshooting: [agent-integration](../agent-integration/SKILL.md).
- Export formats, multi-repo merge, database pushes, affected/god-node command usage outside extractor root-cause analysis: [exports-integrations](../exports-integrations/SKILL.md).

## Read order

1. [references/source-formats.md](references/source-formats.md) for extension support, extractor ownership, detection-versus-dispatch distinctions, and optional extras.
2. [references/troubleshooting.md](references/troubleshooting.md) for symptom-to-cause diagnosis and safe commands.
3. [references/extractor-development.md](references/extractor-development.md) for maintainer workflows, node-ID/source-file rules, resolver registration, and focused tests.
4. Run [scripts/inspect_file_support.py](scripts/inspect_file_support.py) when you need source-free classification and parser-availability evidence for user-provided paths.

## Quick diagnostic flow

From the installed runtime skill directory, inspect suspicious paths without executing user code:

```bash
python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py path/to/file.tf path/to/file.pas
python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py --recursive path/to/repo
python sub-skills/extractor-troubleshooting/scripts/inspect_file_support.py --json path/to/file.dm
```

Interpretation:

- `classification=code` plus an `extractor=...` value means Graphify has an extractor route for that path.
- `status=missing_optional_extra` means an extractor is wired but a parser package is not importable; install the named `graphifyy[...]` extra in the same environment that runs Graphify.
- Pascal has two paths: the optional `graphifyy[pascal]` tree-sitter parser and a regex fallback. Missing `tree_sitter_pascal` lowers extractor quality but is not a hard unsupported-file result.
- `.dmi`, `.dmm`, and `.dmf` are BYOND side formats handled without `tree-sitter-dm`; `.dm` and `.dme` need `graphifyy[dm]` for AST extraction.
- `status=code_without_ast_extractor` means detection calls the file code, but Graphify currently has no AST extractor for that suffix or shebang; open/implement language support rather than telling the user it should appear in the graph.

## Maintainer guardrails

- Do not execute user source code to diagnose extraction; Graphify extractors parse/read files only.
- Preserve Graphify's schema: nodes require `id`, `label`, `file_type`, `source_file`; edges require `source`, `target`, `relation`, `confidence`, `source_file`.
- Preserve `source -> target` semantics. If a user-facing command traverses or renders the reverse direction, route interpretation to [query-navigation](../query-navigation/SKILL.md).
- Use canonical IDs from `graphify.ids.make_id` / extractor helpers; do not invent a separate normalizer.
- Keep local machine paths out of graph IDs and generated guidance. Extraction relativizes `source_file` to the scan root and remaps absolute-path-derived IDs.
- Treat optional language extras as optional install variants, not as required accelerator/backend capabilities; no GPU or accelerator backend is required for this maintainer scope.

## Focused native candidate

Primary native candidate for this sub-skill: `native.language-extractors-core`, centered on language extractor and resolver tests. Optional extractor-specific tests should be selected only when a user or maintainer focuses on that extra.
