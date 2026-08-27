# Cross-cutting troubleshooting

Use this for install, configuration, stale-skill, privacy, optional dependency,
and backend issues that affect multiple OpenMed workflows.

## Import or package metadata mismatch

**Symptoms**

- `import openmed` fails.
- `openmed.__version__` differs from the expected package version.
- A public API or CLI command mentioned by this skill is missing.

**Recovery**

1. Run `python -c "import openmed; print(openmed.__version__)"`.
2. Run `openmed --help` if the CLI is installed.
3. If working from a checkout, install the package in editable mode with the
   target extras.
4. Compare the checkout against `repo-provenance.md`; refresh this skill if the
   commit, version, or public entry points changed.

## Missing optional dependency

**Symptoms**

- `ModuleNotFoundError` for FastAPI, MCP, Transformers, torch, ONNX Runtime,
  MLX, CoreML tools, pydicom, pdfplumber, pandas, polars, DuckDB, or connector
  libraries.

**Recovery**

- Install only the extra needed for the current workflow.
- Re-run the nearest bundled probe script.
- If the dependency is a system binary or platform toolchain, confirm it is
  available before processing PHI.
- Do not silently fall back to CPU or a parser-only route when the user asked
  for a hardware/toolchain-specific behavior.

## Model download or offline-cache failure

**Symptoms**

- Model loader cannot resolve a model alias or local path.
- A workflow attempts network access in a no-network or PHI-sensitive context.
- Tokenizer/model files are incomplete.

**Recovery**

1. Decide whether downloads are allowed.
2. If allowed, prefetch artifacts before processing PHI.
3. If not allowed, configure local-only/offline behavior and point to a staged
   model directory.
4. Validate tokenizer, labels, and max sequence length before batch execution.

## PHI in logs, prompts, cache, or artifacts

**Symptoms**

- Raw clinical text appears in logs, exceptions, audit files, screenshots,
  model-card examples, or generated tests.

**Recovery**

- Stop and replace the example with synthetic text.
- Store offsets, hashes, labels, risk scores, and counts instead of plaintext.
- Keep re-identification mappings and vault keys out of de-identified outputs.
- Run privacy/no-raw-text checks before release or review.

## CLI command misuse

**Symptoms**

- A subcommand accepts input but emits an unexpected format.
- A long-running service command is used when a one-shot CLI/API call was safer.
- A command fails because an output path would overwrite an existing artifact.

**Recovery**

- Run `openmed <subcommand> --help` before constructing commands.
- Prefer JSON output for automation when available.
- Use synthetic input until command behavior is understood.
- Keep run IDs, output filenames, and logs free of patient identifiers.

## Backend-specific failure

**Symptoms**

- CUDA/MPS/MLX/CoreML/ONNX/OpenVINO/Torch imports fail or report unavailable
  devices.
- Quantized/mobile/browser output has span or recall drift.

**Recovery**

- Run the model runtime backend probe.
- Confirm package extras, hardware, driver/runtime, and Python version.
- Use CPU only when the task allows a full CPU substitute.
- For quantized/mobile/browser workflows, include a recall or span-parity check
  before trusting output.

## Restricted terminology or benchmark assets

**Symptoms**

- Grounding or evaluation asks for UMLS, SNOMED CT, CPT, MIMIC, i2b2, n2c2, or
  private EHR/terminology files.

**Recovery**

- Do not bundle or commit restricted data.
- Ask the user to provide licensed local assets or a permitted out-of-process
  terminology bridge.
- Record unverified restricted-path coverage explicitly.

## Stale generated skill

Refresh this skill when:

- The repository commit or package version differs from `repo-provenance.md`.
- Public APIs, CLI command names, optional extras, model manifest shape, service
  schema, or mobile/browser artifacts changed.
- Source evidence paths were removed, renamed, or substantially rewritten.
