# Site Maintenance and Contribution Workflow

## Purpose

Read this when the task is to create, revise, or triage ML Glossary documentation. This file bundles the repo's contribution style and Sphinx-maintenance facts so a future agent does not need to open the original README or docs configuration.

## Project shape

- The project is a Sphinx documentation site, not a Python package.
- Source pages were written mainly in reStructuredText (`.rst`) with Sphinx directives such as `.. toctree::`, `.. contents::`, `.. math::`, `.. image::`, `.. figure::`, `.. literalinclude::`, and `.. rubric::`.
- The source docs were organized around Basics, Math, Neural Networks, Algorithms, Resources, and Contributing.
- The site used the Read the Docs theme and MathJax. The original Sphinx configuration also loaded `sphinx.ext.githubpages` and a CommonMark parser for possible Markdown sources.

## Contribution style distilled from the repository

Every glossary entry should include at least:

1. **Concise explanation**: as short as possible, but no shorter.
2. **Citations**: papers, tutorials, books, or other reliable references.

Excellent entries may also include:

1. **Visuals**: diagrams, charts, animations, or images.
2. **Code**: small Python/NumPy snippets, classes, or functions.
3. **Equations**: formatted with LaTeX through Sphinx math support.

The project's teaching style is beginner-friendly and visual. When adding detail, preserve the accessible tone: start with intuition, then formula, then code or caveats. Do not turn entries into formal encyclopedia articles unless the user asks.

## RST authoring checklist

- Use a top-level title underlined with `=` and section headings with consistent underline characters.
- Prefer `.. contents:: :local:` on longer pages.
- Use explicit anchors for terms that other pages may reference, for example `.. _glossary_accuracy:` or `.. _activation_relu:`.
- Link internal concepts with `:ref:` when the target is an anchor and `:doc:` when the target is a page.
- Put formulas under `.. math::` rather than inline-only prose when the equation is central.
- Keep code snippets short. If the code needs many imports, data files, training time, or old APIs, summarize it and add a caveat instead of presenting it as runnable.
- When using `literalinclude` in a live checkout, verify the target function or line range still exists and parses under the Sphinx/Pygments version in use.
- Cite sources with `.. rubric:: References` and numbered citations when practical.

## Sphinx environment facts

The repository-native docs preview requires Sphinx and the Read the Docs theme. The historical instructions installed:

```bash
python -m pip install sphinx sphinx-autobuild sphinx_rtd_theme recommonmark
```

For a minimal non-watch build, `sphinx`, `sphinx-rtd-theme`, and `recommonmark` were sufficient in the verified production environment. `sphinx-autobuild` is useful only for live preview and is not required for a one-shot HTML build.

## Bundled helper

Use `../scripts/build_docs.sh` from the root runtime directory.

Examples:

```bash
# Verify Sphinx can build a tiny generated RST project; no checkout needed.
bash scripts/build_docs.sh --self-test

# When the user is actively maintaining their own checkout, build that checkout's docs.
bash scripts/build_docs.sh --docs-dir CHECKOUT_DOCS_DIR --build-dir BUILD_OUTPUT_DIR
```

The helper is intentionally self-contained. It does not assume the source checkout used to generate this skill exists.

## Expected build behavior

A successful Sphinx build can still emit warnings because the original docs contained legacy RST, external URLs, literalinclude snippets, and old code examples. Treat warnings as triage signals rather than automatic failure unless the user asks for warning-free output.

Common warning classes to investigate:

- Missing or invalid `literalinclude` targets after code snippets moved or stopped parsing.
- Duplicate or malformed anchors.
- RST title underline length mismatches.
- Bad inline markup around URLs, parentheses, or raw math.
- Images that are missing from the active checkout or not copied into a docs build.
- Theme API changes; older Sphinx code used `html_theme_path` and `app.add_css_file`.

## Maintainer workflow for a user-provided checkout

1. Confirm the user's desired change: new concept, typo fix, algorithm comparison, resource addition, or build-warning cleanup.
2. Use this runtime's sub-skills to determine the correct topic owner and terminology.
3. Edit the user's active checkout only; do not rely on or reference the generation checkout.
4. Keep the entry concise and add citations. If adding equations, verify they render with Sphinx math.
5. For code snippets, prefer Python 3 syntax and self-contained imports. Label pseudocode as pseudocode.
6. Run a Sphinx build only if the user wants validation. Do not run project tests, lint, or formatters unless separately requested.
7. Report whether warnings are from the edited content or pre-existing legacy pages.

## When not to overreach

- Do not modernize all old examples unless the user asks. Many examples are educational snapshots.
- Do not replace beginner explanations with advanced derivations if the requested entry is a glossary-style cheat sheet.
- Do not add heavy dependencies, datasets, notebooks, or training pipelines to prove a documentation-only change.
- Do not treat placeholder pages such as clustering/application subsections as complete coverage; either say they are placeholders or draft a concise starter entry.
