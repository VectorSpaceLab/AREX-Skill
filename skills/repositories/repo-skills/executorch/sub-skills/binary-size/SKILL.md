---
name: binary-size
description: "Measure, compare, and reduce ExecuTorch binary size using
  size-optimized builds, stripped binaries, bloaty/nm analysis, and safe
  reporting constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# binary-size

Use this sub-skill when the user asks about ExecuTorch binary size, stripped runtime size, `size_test`, `size_test_all_ops`, `bloaty`, linker symbols, `EXECUTORCH_OPTIMIZE_SIZE`, or size-regression workflows.

## Workflow

1. Establish a baseline from a clean source checkout and release/size-optimized build.
2. Measure stripped binaries, not only unstripped debug outputs.
3. Use symbol/section analysis to identify `.text`, `.rodata`, static initializers, logging strings, and template bloat.
4. Make one logical change at a time and record before/after numbers.
5. Run relevant correctness tests; do not trade functionality or latency for unverified size savings.

## References and Helper

- Read [binary-size workflow](references/binary-size-workflow.md) for measurement and analysis details.
- Read [troubleshooting](references/troubleshooting.md) for misleading size results and tool issues.
- Compare two files safely:

```bash
python scripts/compare_binary_sizes.py --before old.bin --after new.bin
```

