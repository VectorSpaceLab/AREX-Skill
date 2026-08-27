---
name: command-wrappers
description: "Guides agents using pysam samtools and bcftools command wrappers,
  PysamDispatcher calls, stdout/stderr capture, usage messages, aliases, and
  SamtoolsError troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# command-wrappers

Use this sub-skill when a task asks to run bundled `samtools` or `bcftools` functionality from Python with `pysam.samtools`, `pysam.bcftools`, or top-level `pysam` aliases such as `pysam.view`, `pysam.sort`, `pysam.index`, `pysam.idxstats`, or `pysam.faidx`.

## Read first

- `references/command-reference.md` for the dispatcher contract, command inventory, aliases, return types, and error model.
- `references/workflows.md` for translating shell `samtools`/`bcftools` commands into safe Python calls.
- `references/troubleshooting.md` for `SamtoolsError`, stdout/stderr capture, `save_stdout`, binary output, invalid arguments, and notebook capture issues.
- `scripts/command_wrapper_smoke.py` for a source-free JSON smoke helper that checks dispatchers and safe commands when a working pysam install is available.

## Scope

This sub-skill owns bundled command invocation through `pysam.utils.PysamDispatcher`: `pysam.samtools.*`, `pysam.bcftools.*`, top-level samtools aliases imported into `pysam`, `catch_stdout`, `save_stdout`, `split_lines`, `raw`, `usage()`, `get_messages()`, and `pysam.SamtoolsError`.

Use sibling sub-skills instead for object-level `AlignmentFile`/`AlignedSegment` workflows, `VariantFile`/`VariantRecord` workflows, tabix/FASTA object APIs, or build/install troubleshooting.

## Defaults that prevent common mistakes

- Pass command-line tokens as separate Python string arguments, not as one shell string.
- Keep output redirection explicit: use captured return values for text output, `save_stdout=...` for stdout-to-file, or command-native `-o` plus `catch_stdout=False` for commands that write files.
- Use `catch_stdout=False` when the command writes binary data or owns stdout redirection; otherwise pysam may capture data the command expected to write elsewhere.
- Read `dispatcher.usage()` before guessing required arguments, and catch `pysam.SamtoolsError` around user-supplied command inputs.
- After a command call, inspect the same dispatcher’s `get_messages()` for captured stderr warnings or diagnostics.
- Remember non-identifier command aliases: `pysam.samtools.cram_size` maps to `samtools cram-size`, and `pysam.samtools.fqimport` maps to `samtools import`.
