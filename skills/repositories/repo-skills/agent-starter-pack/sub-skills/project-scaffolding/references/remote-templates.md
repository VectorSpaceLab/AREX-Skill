# Remote templates

Remote templates let `create` generate a project from a local path or from a Git repository instead of a built-in template.

## Accepted forms
- `local@/path/to/template` for a local source tree.
- `adk@sample-name` for the official ADK samples repository.
- `adk-py@sample-name` for contributing samples from the ADK Python repository.
- `github.com/org/repo/path@branch` shorthand for a GitHub source.
- A full `https://github.com/...` URL, including `/tree/<ref>/...` forms.

## What the parser is doing
The remote-template parser distinguishes:
- local vs remote sources
- repo URL vs template subdirectory
- branch/tag/ref selection
- ADK-samples shortcuts

If the input is not recognized as remote, `create` should treat it as a local template selection instead of forcing remote behavior.

## Version locking
Remote templates can ship a lock that requires a matching Agent Starter Pack version.

Practical implications:
- The CLI may re-run itself with a version-pinned `uvx agent-starter-pack@<version>` invocation.
- A missing `uvx` installation becomes a real blocker for locked remote templates.
- `--locked` prevents the version-lock path from recursing.

## Base-template overrides
`--base-template` only applies to remote templates.

Use it when the remote template wants one built-in foundation, but the user wants a different one.
This may trigger dependency installation prompts because the base template defines required extras.

## ADK samples heuristics
For ADK-samples sources, the CLI may infer missing template metadata and still produce a usable project.
That means the generated code can be correct even when the remote sample is less explicit than a normal template repo.

## What to read in the generated project guidance
Remote templates still produce a generated project with the normal output structure and can be combined with:
- `--in-folder`
- `--prototype`
- data ingestion prompts
- session prompts
- deployment target selection

## Trouble spots
- Unknown Git URL formats.
- Missing `uvx` when version locking is required.
- Incorrect `--base-template` choice causing dependency prompts.
- Remote paths that point at the wrong subdirectory inside a repo.
- ADK sample inference that seems inconsistent; fall back to the bundled troubleshooting reference if the output looks surprising.
