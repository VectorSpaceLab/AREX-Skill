# Ghidra Refinement Troubleshooting

## Java runtime missing

- **Symptom**: Ghidra refuses to start or `java -version` fails.
- **Likely cause**: Java 17 is not installed in the environment.
- **Recovery**: install Java 17 before trying the Ghidra flow.

## Headless analyzer path problems

- **Symptom**: the demo cannot find `analyzeHeadless`.
- **Likely cause**: the Ghidra unzip path or the headless executable path is wrong.
- **Recovery**: confirm the Ghidra archive has been unpacked and pass the exact headless path via an env var or CLI flag.

## Postscript / backend mismatch

- **Symptom**: the example backend fails even though the script path is correct.
- **Likely cause**: the repo examples mix Ghidra naming with decompiler-specific postscript APIs.
- **Recovery**: verify the exact backend pair before running and treat the supplied postscript as backend-specific rather than assuming a pure Ghidra context.

## No function found in the pseudo-code dump

- **Symptom**: the demo reports that no target function was found.
- **Likely cause**: the function name does not match the binary, or the function delimiters were removed during post-processing.
- **Recovery**: verify the function name, inspect the dump, and keep the `/* name @ address */` markers intact.

## Refinement model output looks wrong

- **Symptom**: the V2 output is empty or nonsensical.
- **Likely cause**: the pseudo-code prompt is malformed or the model path is mismatched.
- **Recovery**: confirm the prompt banner, the pseudo-code extraction, and the V2 checkpoint selection.
