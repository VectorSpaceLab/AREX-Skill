# Tooling and Deployment Troubleshooting

## Docs build fails

- **Likely cause:** a public API change or a missing documentation update.
- **Recovery:** refresh the docs after the code change and rerun the docs build command.

## Formatting or lint hooks modify files unexpectedly

- **Likely cause:** generated code or formatting drift.
- **Recovery:** review the generated diff, keep the normalization, and rerun the hook until it is clean.

## Package install fails or dependency resolution changes unexpectedly

- **Likely cause:** an extra or dependency floor changed without matching the package metadata.
- **Recovery:** inspect the relevant `setup.py` and extension metadata before adjusting the installation guidance.

## Changelog fragment missing

- **Likely cause:** a public change was made without a package-specific fragment.
- **Recovery:** add the fragment under the touched package and use the correct bump suffix.

## Deployment helper is unsafe to run

- **Likely cause:** the helper targets a cluster, service, or remote resource and is not a local maintainer check.
- **Recovery:** treat it as reference-only and document the deployment assumptions before attempting execution.
