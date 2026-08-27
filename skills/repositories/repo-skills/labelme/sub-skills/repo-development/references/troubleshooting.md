# Repository Development Troubleshooting

## Tests fail before collection

Confirm the uv/venv environment has the project and test dependencies. Run a
single focused test path, then inspect the first import error. Do not install
all optional converter or network dependencies unless the changed workflow
needs them.

## Qt platform plugin or no-display failure

Separate headless unit tests from GUI tests. On Linux use Xvfb and the platform
libraries documented by CI. A GUI failure should not block annotation JSON,
config, or conversion checks that are designed to run headlessly.

## Network/model test is unavailable

Keep `network` tests excluded unless explicitly requested and network/model cache
access is available. Use fake OSAM sessions to test prompt routing and response
handling, but record that real model quality/runtime remains unverified.

## Translation check changes files

`tools/update_translate.py` can update generated catalogs. Review the diff and
run the check target before committing. Do not hand-edit generated `.qm` files.

## Changelog or terminology review fails

Check `AGENTS.md`, `CONTEXT.md`, and the relevant ADR. Put user-facing changes
under `[Unreleased]` with the right subsection and use the glossary's exact
terms. Surface any ADR contradiction in the change discussion.
