# PandasAI Security Model

## Purpose

Use this reference when a user wants to know what PandasAI executes, what the
sandbox protects, and what it does not protect.

## Execution model

PandasAI's chat layer asks an LLM to produce Python code, then executes that code
locally unless a sandbox is supplied. The package also validates the generated
code and applies SQL-safety checks when the generated code calls back into SQL
execution.

Security layers in the package:

1. **Code requirement validation** — the generated code must call
   `execute_sql_query(...)` when required by the PandasAI code-generation path.
2. **SQL sanitization** — query strings are scanned for mutating or dangerous
   statements and comments.
3. **Sandbox execution** — optional external isolation layer when the user passes
   a `Sandbox` instance.

These layers address different risks and do not replace each other.

## What the sandbox is for

Use a sandbox when:

- users can submit prompts you do not fully trust;
- the application handles sensitive data;
- the app is multi-tenant or public-facing;
- you want extra filesystem or network isolation around generated code.

## What the sandbox is not

- It is not automatic.
- It is not guaranteed to exist without installing the optional package.
- It does not replace LLM prompt hygiene.
- It does not remove the need to inspect dangerous generated code paths.

## Security recommendations

- Use `FakeLLM` for local tests that must not hit a provider.
- Keep real provider keys and database credentials out of source code.
- Use the smallest possible environment and filesystem surface for generated code.
- Prefer a sandbox for untrusted prompts even if the generated code appears
  benign.

## Common failure signals

- `Sandbox.start/stop` never called or `_started` stays false.
- `pandasai-docker` import fails because the optional package was not installed.
- Docker is installed but the daemon is not running.
- SQL sanitizer rejects a query because it is not a read-only SELECT-style query.
- Generated code reaches `execute_sql_query` but returns the wrong `result`
  dictionary shape.
