# Cross-Cutting Troubleshooting

## Purpose

Read this for ML Glossary tasks involving installation, Sphinx/RST build warnings, legacy educational code snippets, or self-containment checks. Workflow-specific caveats also live in each sub-skill's `references/troubleshooting.md`.

## Quick triage table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `sphinx-build: command not found` | Sphinx is not installed in the active environment. | Install `sphinx`, `sphinx-rtd-theme`, and `recommonmark`, or run `bash scripts/build_docs.sh --self-test` after preparing an environment. |
| `No module named sphinx_rtd_theme` | Theme dependency missing. | Install `sphinx-rtd-theme`; in Python imports the module name uses underscores: `sphinx_rtd_theme`. |
| Build succeeds but emits many warnings | Legacy RST/literalinclude/URL/image issues in the project. | Separate warnings caused by the current edit from pre-existing warnings. Warnings alone were expected in production verification. |
| `literalinclude` warnings or skipped code blocks | Referenced code function/line no longer exists, code has Python 2 syntax, or parser cannot import/parse the file. | Convert important code into a small Python 3 snippet or use a bundled self-contained script. Do not tell users to run old snippets as production examples. |
| `print "..."` syntax error | Legacy Python 2 example. | Translate to `print(...)` if the user asks to modernize; otherwise document as legacy evidence. |
| Undefined `np`, `plt`, `log`, or similar | Educational snippet omitted imports or mixed `numpy`/`np` naming. | Add explicit imports in new code or use bundled demo scripts. |
| User asks for `docs/`, `code/`, or notebook details but checkout is unavailable | Runtime must be self-contained. | Use `references/site-map.md` and sub-skill references; do not require the original source tree. |
| User asks for a modern best practice that differs from repo text | Source material is older educational content. | Answer with a labeled split: repo-grounded explanation first, modern note second. |

## Sphinx build recovery

1. Confirm the task is actually about docs preview/build. If the task is concept explanation, no Sphinx environment is required.
2. For a self-contained environment check, run:

   ```bash
   bash scripts/build_docs.sh --self-test
   ```

3. For a user-provided checkout, pass explicit paths:

   ```bash
   bash scripts/build_docs.sh --docs-dir CHECKOUT_DOCS_DIR --build-dir BUILD_OUTPUT_DIR
   ```

4. If warnings occur, group them by source page and type. Do not promise warning-free historical docs unless you have fixed every warning.
5. If a warning is from `literalinclude`, decide whether the code should remain, be replaced by inline Python 3 code, or be summarized as pseudocode.

## Legacy code policy

The original `code/` directory was a teaching aid. It contained useful algorithm sketches, but also several issues:

- Logistic-regression examples used Python 2 print syntax and inconsistent imports.
- Optimizer snippets included a syntax issue in the source evidence.
- Some deep-learning examples require PyTorch, torchvision, datasets, and training loops that are not appropriate for a small docs-maintenance smoke check.
- Some snippets were intended for Sphinx `literalinclude`, not standalone execution.

For runnable educational examples, prefer these bundled replacements:

- `sub-skills/basics-and-math/scripts/linear_logistic_demo.py`
- `sub-skills/classical-algorithms/scripts/knn_demo.py`
- `sub-skills/neural-networks/scripts/activation_loss_demo.py`

## RST warning patterns

- **Title underline mismatch**: the underline must be at least as long as the title text.
- **Unknown target name**: the referenced anchor or URL label does not exist. Add or fix an explicit anchor.
- **Malformed hyperlink**: URLs with parentheses or mixed Markdown/RST syntax often need backticks and angle brackets.
- **Math parse errors**: keep LaTeX inside `.. math::` blocks and avoid unsupported Unicode in equations if MathJax/Sphinx complains.
- **Image missing**: copy the image into the user's active docs tree or replace with text if the task does not require visuals.

## Self-containment checks

Runtime Markdown should link only to files inside this skill tree or to optional external URLs. It must not tell future agents to open original source paths for knowledge. After editing runtime files, run:

```bash
python scripts/check_runtime_links.py .
```

If the checker flags a local path outside the runtime, either copy/distill the needed material into `references/` or remove the instruction.

## Stop conditions

Stop and ask the user before:

- Installing host-level Python or package managers.
- Mutating a user-owned environment in a way that may break it.
- Running network downloads, notebook execution, long training, GPU jobs, or project-wide tests/lint/formatters.
- Importing this skill into a live router. The creation request explicitly said not to import.
