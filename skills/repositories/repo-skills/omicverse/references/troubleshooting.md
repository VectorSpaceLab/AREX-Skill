# OmicVerse Troubleshooting

Use this root troubleshooting guide for cross-cutting failures. For data- or workflow-specific failures, read the nearest sub-skill troubleshooting reference.

## Install and Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: omicverse` | Package is not installed in the active Python | Install `omicverse` in the same interpreter that runs the code, then run `python -c "import omicverse as ov; print(ov.__version__)"`. |
| `Failed to import omicverse.<module>` | OmicVerse lazy-loaded a submodule whose dependency failed | Import the submodule directly to see the original traceback, then install the narrow extra/backend needed by that workflow. |
| `pip check` reports missing packages | Partial or `--no-deps` install | Reinstall the base package normally with dependencies; avoid broad optional extras unless the selected workflow requires them. |
| Import warnings from `anndata` or plotting libraries | Upstream deprecation or backend warning | Confirm the workflow still runs; pin compatible versions only when warnings become errors. |
| A deep-learning/spatial/histology/backend import fails | Optional stack such as `scvi-tools`, `torch-geometric`, `lazyslide`, `spatialdata`, Vina/RDKit, or AIRR/genetics backends is absent | Install the relevant extra or backend for that sub-skill; do not install all extras just to fix one route. |

## Data and Configuration

- For AnnData workflows, inspect `adata.shape`, `obs`, `var`, `layers`, `obsm`, `obsp`, and `uns` before calling downstream analysis.
- For table workflows, verify unique feature/sample IDs, numeric abundance/count columns, and metadata design columns before model fitting.
- For spatial workflows, verify coordinate keys, image/scale-factor files, segmentation files, and `uns['spatial']` before plotting or deconvolution.
- For genetics/AIRR/alignment/molecular workflows, validate domain columns and external files before running downloads, binaries, docking, or expensive pipelines.

## CLI, MCP, and Services

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `omicverse --help` works but `omicverse-mcp` fails | MCP extra or transitive dependency is missing | Install `omicverse[mcp]` or the missing package named in the traceback; run `omicverse-mcp --help` again. |
| MCP stdio client hangs or JSON parse fails | Non-JSON logs/progress were printed to stdout | Keep stdout reserved for JSON-RPC; send diagnostics to stderr; test with `sub-skills/agentic-and-mcp/scripts/inspect_registry.py` before starting the server. |
| `omicverse claw` starts gateway instead of one-shot code | By design, `claw` defaults to gateway mode unless one-shot flags are supplied | Use `omicverse claw -q "..."` for one-shot prompts, or use gateway/JARVIS setup intentionally. |
| Provider/channel auth fails | Missing API key, OAuth token, bot token, or configured auth mode | Keep secrets outside skill files; supply credentials via the user's environment or documented config paths. |
| Web/gateway command fails to import web package | Optional `omicclaw`/web workspace is absent | Install the web extra/package or avoid web launch when only CLI/MCP inspection is needed. |

## Backend and Safety Gates

- Treat SRA downloads, dataset fetchers, model downloads, histology tiling, molecular structure fetches, docking, external binary auto-install, and long model training as explicit user-approved operations.
- Use `--help`, dry-run flags, tiny synthetic fixtures, and validators before running any command that binds a port, downloads data, writes large outputs, or invokes external tools.
- Prefer explicit binary paths and `auto_install=False` in scripted examples when a command might install tools or mutate the environment.

## Where to Go Next

- Core AnnData/plotting/report issue: `sub-skills/core-analysis/references/troubleshooting.md`.
- Single-cell annotation/integration/trajectory issue: `sub-skills/single-cell-workflows/references/troubleshooting.md`.
- Bulk/enrichment/metabol/protein/micro table issue: `sub-skills/multiomics-statistics/references/troubleshooting.md`.
- Spatial/histology/deconvolution issue: `sub-skills/spatial-integration/references/troubleshooting.md`.
- AIRR/genetics/alignment/molecular issue: `sub-skills/specialist-domains/references/troubleshooting.md`.
- CLI/MCP/JARVIS/agent issue: `sub-skills/agentic-and-mcp/references/troubleshooting.md`.
