---
name: tutorial-resource-map
description: "Route tutorial-navigation requests for the DataSciencePython
  README and modernized Python 3 snippets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tutorial-resource-map

Use this sub-skill for learning-oriented questions about the repo's curated resource map and for small Python 3 modernizations drawn from the bundled basics reference. These bundled references are the source of truth for this router.

## Use this route for
- Finding the best README family for Python, data science, pandas, scikit-learn, machine learning, NLP, text mining, sentiment analysis, pickle, regex, shell scripting, or course recommendations.
- Mapping a user question to a compact list of curated tutorial directions rather than a full build or run workflow.
- Modernizing the small Python 2-era snippets in the bundled basics reference: `enumerate`, string joins, `str.find`, and 2D-list column extraction.
- Returning a local example pointer when it helps, while keeping the answer short and educational.

## Do not use this route for
- Executable modeling, training, evaluation, or notebook-style workflow guidance. Route to `../statsmodels-logit-workflow/` or `../kaggle-linear-models/` instead.
- Twitter JSON or streaming implementation. Route to `../twitter-json-workflow/` instead.
- Environment repair, package installation, or repo maintenance.

## Read first
- `references/topic-index.md`
- `references/python-basics.md`
- `references/troubleshooting.md`

## Answer pattern
- Name the best matching README family.
- Give one short reason.
- Add the nearest local example or sibling skill only when it clarifies the handoff.
- For snippet modernization, answer in Python 3 and mention the legacy Python 2 form only as context.
