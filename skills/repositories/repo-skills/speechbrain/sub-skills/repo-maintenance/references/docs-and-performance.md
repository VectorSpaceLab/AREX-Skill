# Documentation and performance maintenance

## Documentation build

SpeechBrain docs are Sphinx-based and include Markdown/RST pages, API autosummary, and notebooks. A docs-focused environment may need `docs/docs-requirements.txt` or `docs/readthedocs-requirements.txt` in addition to package requirements.

Typical build pattern:

```bash
cd docs
SPHINXOPTS="-j=auto" make html
```

Use a focused docs build or doctest when changing one API/docstring. Full docs generation can be expensive and may require notebook/doc tooling.

## Tutorial index maintenance

When adding or renaming a tutorial notebook, update the corresponding RST index/toctree and ensure the link target is correct. Keep notebook execution separate from ordinary import/doctest checks.

## Performance table generation

The repository's performance README is built from `tests/recipes/*.csv` performance fields and recipe metadata. The source helper reads CSV rows and emits Markdown tables grouped by dataset/task.

When changing performance metadata:

- Keep model/hparams paths correct.
- Keep result and Hugging Face links consistent with recipe README files.
- Do not claim a new benchmark result from a tiny debug run.
- Preserve empty/unknown performance fields instead of inventing values.

## Docs and API changes

For a public API change:

1. Update the docstring with arguments/returns/examples.
2. Update HyperPyYAML or recipe references.
3. Add or adjust a focused unit/doctest.
4. Update the relevant tutorial index or API exposure if needed.
5. Run docs/doctest checks appropriate to the change.

## Link/network checks

URL checks and Hugging Face checks can access external services. Run them only when link/model metadata changed and network budget is available. Record network failures separately from source or logic failures.
