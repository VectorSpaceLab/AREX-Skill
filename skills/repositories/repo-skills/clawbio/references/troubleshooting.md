# Cross-cutting troubleshooting

Read this when a failure crosses runner, routing, integrations, and validation.
For a route-specific symptom, prefer the nearest sub-skill troubleshooting
reference.

## `No input provided`

Use exactly one of `--demo`, `--input <file>`, or `--profile <json>` for an
ordinary registered run. Confirm the path exists and is readable. A profile
stores the original input path; it does not embed a missing source file as a
replacement. For a fresh genotype file, create the profile with `clawbio
upload` first.

## Unknown or non-runnable skill

Run `clawbio list` and inspect the catalog. The directory name, catalog `name`,
and runnable `cli_alias` may differ. An agent-readable-only entry has a
`SKILL.md` contract but no CLI entry point; use its guidance or choose a
registered alias rather than inventing a command. If the catalog and registry
look inconsistent, repair source metadata/registration and regenerate the
catalog; do not hand-edit generated catalog JSON.

## Output collision or partial output

The runner resolves relative paths from the caller's current directory and
rejects an existing regular file at the requested output path. Choose a new
writable directory. If a previous run partially wrote outputs, inspect
`result.json`, `report.md`, and any logs before deleting anything; preserve the
failure for reproducibility and never overwrite valuable patient results
silently.

## Optional dependency, credential, or binary failure

Separate importability from readiness. `clawbio[mcp]` is required for the MCP
transport; bots require their platform packages and secrets; provider bridges
require their documented credentials; nf-core wrappers require Nextflow,
containers/Conda as selected, references, and often network access. Run the
relevant bundled diagnostics with `--help` first, then report the missing
component and whether it is optional. Do not substitute a CPU import for a
required accelerator or pipeline runtime.

## Local-file access is refused by MCP

The MCP server is demo-only by default. `CLAWBIO_MCP_ALLOW_LOCAL_FILES=1` (or
`true`/`yes`) is an explicit opt-in for local input/output access. This is a
privacy boundary, not an ordinary parser error. Do not place patient paths or
secrets in an MCP client configuration.

## Flags are rejected or disappear

Use the selected skill's documented flags. The launcher applies a per-skill
`allowed_extra_flags` policy; bypassing it is unsafe. For nf-core wrappers,
`--help` is delegated to the wrapper so schema-derived flags are visible.
Unknown flags should be diagnosed as a registration/wrapper mismatch, not
solved by passing arbitrary shell text.

## Result looks successful but evidence is missing

Check `success`, `exit_code`, `stderr`, `output_dir`, and `files`, then inspect
structured result fields and the report. A PASS status requires the expected
artifact and provenance evidence. Network, credentials, GPU, large data, and
long-running cases may be SKIP or BLOCKED; do not report them as verified.

## Medical or privacy boundary

ClawBio is a research and educational tool, not a medical device and not a
source of clinical diagnoses. Keep genetic data local unless the user
explicitly chooses a documented external service and its privacy implications
are understood. Use the selected domain skill's cited methodology; never fill
missing evidence with guessed gene-drug associations or thresholds.
