# Troubleshooting

## Backend not available

**Symptom:** `Unknown backend: ...`

**Meaning:** The backend is not in the installed registry.

**Fix:** Use one of the built-ins or load the environment that provides the
missing backend before calling `create_config(...)`.

## Legacy CLI says a backend cannot build or report

**Symptom:** `Backend X does not support building projects.` or
`Backend X does not support reading reports.`

**Meaning:** The legacy CLI only dispatches a limited backend set.

**Fix:** Use the Python API for the backend instead of the legacy CLI.

## Vivado / Vitis

**Symptom:** `Vivado HLS installation not found. Make sure "vivado_hls" is on PATH.`

**Meaning:** The Vivado HLS shell is not loaded.

**Fix:** Load the Vivado environment first.

**Symptom:** `Vitis installation not found. Make sure "vitis-run" is on PATH.`

**Meaning:** The Vitis HLS shell is not loaded.

**Fix:** Load the Vitis environment first.

**Symptom:** `Vivado HLS header files not found...` or
`Vivado HLS libraries not found...`

**Meaning:** SymbolicExpression could not locate the HLS include or library
paths for math support.

**Fix:** Provide the HLS include and library paths explicitly, or source the
matching Vivado/Vitis environment so they can be inferred.

## Quartus

**Symptom:** `Intel HLS installation not found. Make sure "i++" is on PATH.`

**Meaning:** Intel HLS is not loaded.

**Fix:** Load the Intel HLS environment first.

**Symptom:** `Quartus installation not found. Make sure "quartus_sh" is on PATH.`

**Meaning:** FPGA synthesis was requested but Quartus is missing.

**Fix:** Load Quartus before requesting FPGA synthesis.

**Backend note:** Quartus only implements the resource strategy family. If you
ask for latency-style behavior, that is a backend limitation rather than a bug.

## Catapult

**Symptom:** `Catapult HLS installation not found. Make sure "catapult" is on PATH.`

**Meaning:** The Catapult executable is unavailable.

**Fix:** Load Catapult, or expose it through `MGC_HOME` or `CATAPULT_HOME`.

## oneAPI

**Symptom:** `Could not find icpx. Please configure oneAPI appropriately`

**Meaning:** The oneAPI compiler environment is not loaded.

**Fix:** Load a supported oneAPI release before compiling or building.

**Version note:** use a supported oneAPI release from the documented window;
2025.1 is known not to work.

**Backend note:** tracing and external BRAM-style behavior are not implemented
in the current oneAPI flow. If those features are missing, that is an expected
backend limitation.

## Libero / SmartHLS

**Symptom:** `Libero/SmartHLS installation not found. Make sure "shls" is on PATH.`

**Meaning:** SmartHLS is not available in the current shell.

**Fix:** Load the Libero/SmartHLS environment before calling `create_config`
or `build()`.

**Symptom:** `create_config(...)` fails before any synthesis step.

**Meaning:** The config constructor could not infer the SmartHLS install path.

**Fix:** Treat that as a prerequisite problem, not a package bug.

## SymbolicExpression

**Symptom:** `create_config(...)` fails while looking for Vivado/Vitis include
paths.

**Meaning:** The backend expects HLS math headers and libraries.

**Fix:** Provide explicit HLS paths or source the matching compiler environment.

## Report parser errors

**Symptom:** `Path ... does not exist` or `Project ... does not exist.`

**Meaning:** The project was not written or the synthesis tool has not produced
reports yet.

**Fix:** Check that the output directory exists and that the correct parser
matches the backend that produced the project.

## General safety reminders

- Do not launch vendor synthesis unless the user asked for it and the toolchain
  is ready.
- Do not treat missing external tools as package defects.
- If a generated project already has reports, parse them instead of rebuilding.
