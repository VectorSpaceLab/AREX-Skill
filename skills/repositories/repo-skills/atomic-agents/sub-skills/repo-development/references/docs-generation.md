# Docs and llms.txt Generation

The repository includes a maintainer helper that generates `llms.txt` bundles for documentation, source, examples, and a combined corpus. Treat it as maintainer documentation, not as an end-user runtime path.

## What the generator does

- Creates `llms.txt` as a compact navigation/index file.
- Creates `llms-docs.txt` from the built single-page documentation output.
- Creates `llms-source.txt` from framework source files.
- Creates `llms-examples.txt` from example READMEs and source files.
- Creates `llms-full.txt` by combining docs, source, and examples.
- Copies generated files into the HTML build directory if that directory already exists.

## Prerequisites

- Documentation dependencies must be available.
- The docs single-page HTML output should be built first if `llms-docs.txt` or `llms-full.txt` should contain rendered docs.
- The helper uses BeautifulSoup and markdownify-style HTML-to-Markdown conversion.

## Safe maintenance flow

1. Build the docs output required by the generator.
2. Run the repo-maintained generator from a maintainer checkout only when the task is to update docs bundles.
3. Review generated text files for accidental secrets, huge generated noise, or stale public links.
4. Do not use the generator as a normal application runtime helper.

## Why this file exists

The generator is reference-only for this skill because it writes documentation artifacts and depends on maintainer checkout state. The operating guidance here records its purpose and safety constraints without copying the whole source script into the runtime skill.
