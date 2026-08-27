# Cross-cutting troubleshooting

Use the nearest sub-skill troubleshooting reference for source, grammar, or AST
detail. Use this file for installation and boundary failures that affect more
than one workflow.

## Package imports but parsing is absent

**Symptoms:** `openqasm3.ast` imports, but `openqasm3.parse` is missing; importing
`openqasm3.parser` reports a missing `antlr4` runtime.

**Cause:** the AST/printer package can be installed without its optional parser
dependencies.

**Recovery:**

```bash
python -m pip install 'openqasm3[parser]'
python -c "import openqasm3.parser; from openqasm3 import parse; print('parser ready')"
```

Install `openqasm3[tests]` only when the focused test dependencies are needed.

## ANTLR-generated parser mismatch

**Symptoms:** an import reports no generated parser or no generated variant for
the installed `antlr4-python3-runtime` version.

**Cause:** `openqasm3` dynamically selects generated modules by the ANTLR
runtime major/minor. A source checkout may not contain generated modules, or a
partial/stale distribution may not contain the matching `_4_<minor>` variant.

**Recovery:**

1. Inspect `importlib.metadata.version("antlr4-python3-runtime")`.
2. Reinstall a complete `openqasm3[parser]` distribution whose generated
   variants cover that runtime.
3. If developing from source, generate parser files from the matching grammar
   with an ANTLR tool whose major/minor matches the runtime, and use a version
   listed as supported by that source revision.
4. Do not treat changing only the Python runtime package as a durable repair;
   verify `import openqasm3.parser` and parse a tiny program afterward.

## Same package version, different API

**Symptoms:** two installations report `openqasm3` 1.0.1 but differ in
`parse_version`, comment extraction, AST node classes, parser options, or error
location fields.

**Cause:** a repository snapshot may evolve without an immediate package-version
change; an older wheel can therefore differ from current same-version source.

**Recovery:** inspect the active runtime (`inspect.signature`, `ast.__all__`,
`spec.supported_versions`) and align code with the intended source snapshot.
Do not combine Python files from one snapshot with generated grammar artifacts
from another. Run [check_install.py](../scripts/check_install.py) before
following API-specific guidance.

## Unsupported or malformed version

**Symptoms:** the parser rejects `OPENQASM 2.0;`, `OPENQASM 4.0;`, or a header
with too many components.

**Cause:** the verified parser supports 3.0 and 3.1 and applies a version gate
before grammar construction.

**Recovery:** choose the correct parser/toolchain for the declared language.
Use `ignore_version=True` only as an explicit diagnostic experiment; it does not
prove that the source follows or means the requested version.

## Include parsed but gates remain unavailable

**Symptoms:** `include "stdgates.inc";` parses, but a compiler cannot locate the
file or resolve gates.

**Cause:** reference parsing recognizes include syntax but does not search for,
read, or merge the file. Search paths and implementation-provided standard
libraries belong to the downstream toolchain.

**Recovery:** configure the consumer's include path and compatible library.
Validate library/version compatibility separately. Do not ship a random copy of
`stdgates.inc` to mask a toolchain mismatch.

## Parse succeeds but the result cannot compile or run

**Symptoms:** strict parsing returns `Program`, yet names are unresolved, types
or widths fail, calibration payloads are rejected, or a simulator/provider does
not support the program.

**Cause:** parser acceptance is only one layer. Includes, full semantic/type
rules, supported instruction subsets, mapping, extern linkage, pulse grammar,
calibration values and hardware are outside it.

**Recovery:** read
[syntax versus semantics](../sub-skills/grammar-conformance/references/syntax-semantics-boundary.md),
identify the first unverified layer, and run the compiler/provider check that
owns it. Report only the validation actually performed.

## No simulator, GPU, or QPU is detected

This is not an installation failure for the reference skill. Language authoring,
grammar checks and AST tooling are CPU-only. Select and configure a separate
simulator or provider stack only when execution is part of the downstream task.
Never infer access to quantum hardware from successful parsing.
