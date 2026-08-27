# Ghidra Refinement Data Formats

## Pseudo-code dump format

The bundled Ghidra postscript writes one block per function:

```text
/* function_name @ 0xADDRESS */
<decompiled C code>
```

The exact address and function name are important because later scripts use them to recover the per-function mapping.

## Demo input shape

The demo runner expects:

- a compiled binary or a source file that can be compiled into one,
- a Ghidra headless binary path,
- a postscript path,
- a target output file for the pseudo-code dump,
- a model path for the V2 refinement checkpoint.

## Prompt shape

After extraction, the pseudo-code is wrapped with the repo's standard prompt banner:

```text
# This is the assembly code:
<pseudo-code>
# What is the source code?
```

## Validation checks

- Function delimiters are present.
- The pseudo-code file contains at least one recoverable function body.
- The Ghidra headless analyzer path and Java 17 runtime are both available.
