---
name: ml-glossary
description: "Routes self-contained ML Glossary knowledge for machine-learning
  concepts, cheat-sheet authoring, Sphinx documentation maintenance, and
  educational code-snippet caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ML Glossary Repo Skill

Use this self-contained runtime skill for tasks about **ML Glossary / ML Cheatsheet** content: explaining machine-learning terms, building beginner-friendly cheat sheets, comparing algorithms, maintaining glossary-style RST documentation, or triaging educational code snippets from the project lineage. The runtime contains distilled domain knowledge from the repository; do **not** reopen the original `docs/`, `code/`, or `notebooks/` directories to answer ordinary user questions.

## First decision

1. Identify whether the user wants a **concept explanation**, an **algorithm comparison**, a **neural-network workflow**, a **resource recommendation**, or **documentation maintenance**.
2. Read the closest route below and only then open the linked bundled references or sub-skill.
3. If the task is about editing a live checkout, use this runtime for style, terminology, and warning triage; only the user's active checkout should be edited, and the original source checkout used to generate this skill is not required.

## Route map

| User intent | Read next | Why |
| --- | --- | --- |
| Term lookup, beginner glossary, feature/label/model/loss/epoch/overfit concepts | `sub-skills/basics-and-math/SKILL.md` | Owns glossary, notation, linear/logistic regression, calculus, linear algebra, probability/statistics basics, gradient descent, and loss bridges. |
| Derivations or formulas for MSE, gradient descent, sigmoid/log-loss, matrix dimensions, chain rule | `sub-skills/basics-and-math/references/formula-cheatsheet.md` | Compact self-contained formula and code-reference map. |
| Decision trees, ID3/C4.5/CART, KNN, random forests, boosting, SVM, regression variants, clustering/RL placeholder status | `sub-skills/classical-algorithms/SKILL.md` | Owns non-neural algorithm families and their repo-specific caveats. |
| Neural network concepts, weighted inputs, layers, activation/loss/optimizers, forward/backpropagation, regularization, CNN/RNN/GAN/VAE/autoencoder/MLP examples | `sub-skills/neural-networks/SKILL.md` | Owns neural-network conceptual and architecture workflows. |
| Dataset, library, paper, course, blog, application, or learning-resource selection | `references/resources-catalog.md` | Distills the repository's large resource catalogs into usable categories and representative picks. |
| Site map, source-content ownership, or what each original content family represented | `references/site-map.md` | Provides a self-contained map of the docs/code/notebook evidence without requiring the original files. |
| Contributing, RST style, Sphinx build setup, docs preview, or glossary entry authoring | `references/site-maintenance.md` and `references/troubleshooting.md` | Captures contribution style, Sphinx dependencies, build caveats, and legacy warning patterns. |
| Staleness or refresh checks | `references/repo-provenance.md` | Records the source commit, branch, dirty state, and evidence baseline. |

## Bundled scripts

- `scripts/build_docs.sh` is a safe Sphinx helper. Run `bash scripts/build_docs.sh --self-test` to validate that Sphinx can build a tiny bundled RST project. When actively maintaining a user-provided checkout, pass `--docs-dir PATH_TO_DOCS` and `--build-dir PATH_TO_OUTPUT`; the script never assumes the generated source checkout still exists.
- `scripts/check_runtime_links.py` checks that Markdown links inside this runtime resolve within the skill tree or are explicit external URLs. Use it after editing runtime references.
- Sub-skill scripts provide educational, self-contained code examples: `sub-skills/basics-and-math/scripts/linear_logistic_demo.py`, `sub-skills/classical-algorithms/scripts/knn_demo.py`, and `sub-skills/neural-networks/scripts/activation_loss_demo.py`.

## Operating rules for future agents

- Treat this as an **educational reference and maintainer guide**, not an installable Python library. The repository has no package metadata or public Python distribution.
- Prefer plain-language explanations with formulas and toy examples. The original project prioritized concise explanations, citations, visuals, code snippets, and equations.
- Do not claim the legacy `code/` examples are production-ready. Several snippets use Python 2 print syntax, missing imports, old APIs, or partial pseudocode. Use bundled scripts when a runnable toy example is needed.
- If asked to edit glossary content, keep entries short, accessible, cited, and supported by visuals/equations/code when practical. Use RST/Sphinx conventions from `references/site-maintenance.md`.
- If asked to verify a docs build, do not run project tests, lint, or formatters unless the user separately requests them. A Sphinx build is the relevant repository-native check.
- If a user asks for modern best practices beyond the repository content, separate **repo-grounded ML Glossary facts** from **modern additions** and label the latter clearly.

## Known scope limits

- Many applications, clustering, training, and some reinforcement-learning subsections were placeholders in the source material. This runtime records that status rather than inventing full coverage.
- The original docs used many images; this runtime distills their teaching intent in text so the original image files are not required.
- External URLs in resource references are optional leads. The explanations and routing needed to answer common tasks are included inside this runtime.
