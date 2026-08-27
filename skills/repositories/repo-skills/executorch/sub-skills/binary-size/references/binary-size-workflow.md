# Binary Size Workflow

## Baseline Build

Use a release build with size optimization enabled for size experiments. The size-oriented workflow uses stripped binaries such as a minimal runtime `size_test` and an all-ops variant to separate core runtime size from operator/kernel registration costs.

## Analysis Tools

| Tool | Use |
| --- | --- |
| `strip` | Remove symbol/debug information before comparing deployable size. |
| `bloaty -d symbols` | Find largest symbols. |
| `bloaty -d sections` | Separate `.text`, `.rodata`, unwind, and debug sections. |
| `bloaty after -- before` | Diff two binaries. |
| `nm -S` | Sort symbols by size when bloaty is unavailable. |
| `strings` | Inspect large string literals and embedded paths. |

## Common Reduction Areas

- Duplicate template instantiations and large inline functions.
- Logging/error strings in release builds.
- Static initialization and registration tables.
- Linker configuration that keeps unused object files.
- Feature flags accidentally enabling optional kernels/backends.

## Reporting Format

Record one logical change per report with both per-change and cumulative deltas for the minimal runtime and all-ops runtime. Include build flags, compiler, platform, and exact before/after artifact names.

