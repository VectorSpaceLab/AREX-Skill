# Custom Languages

## Purpose

Read this when the repo uses a language that is not covered by the built-in parser list and you want to add support through `.code-review-graph/languages.toml`.

## How it works

CRG can load additional tree-sitter grammar mappings from `.code-review-graph/languages.toml` in the target repository.

A minimal entry looks like this:

```toml
[languages.erlang]
extensions = [".erl"]
grammar = "erlang"
function_node_types = ["function_clause"]
class_node_types = ["record_decl"]
import_node_types = ["import_attribute"]
call_node_types = ["call"]
```

The parser then treats those files like built-in source files for search, flows, communities, review context, and other downstream graph features.

## Validation rules

The loader is intentionally conservative:

- built-in extensions always win;
- built-in language names cannot be shadowed;
- every extension must start with a dot;
- invalid grammar names are skipped with a warning;
- malformed TOML disables custom-language loading for that build;
- at least one node-type list must be non-empty;
- only a limited number of custom languages are loaded per repo.

## Recommended workflow

1. Add one language at a time.
2. Use a tiny fixture file and rebuild the graph.
3. Check `status` or a targeted query to confirm that the nodes appeared.
4. Only then expand the TOML entry to cover additional node types.

## Common failure modes

- The extension collides with a built-in parser.
- The grammar name is not shipped by `tree_sitter_language_pack`.
- The grammar’s definition name is nested in an unusual field and needs a `name_field` hint.
- A language is accepted but emits too few edges because the generic walker cannot resolve exotic call shapes or import paths.

## When to stop

Stop and ask for help if the language needs deeper framework-specific enrichment than a generic tree-sitter mapping can provide.
