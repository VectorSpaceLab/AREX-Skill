# Matching and NLI Troubleshooting

## QA or reading request accidentally routes here

If the user wants spans, passages, yes/no answers, or cloze completion, switch
to `qa-reading`. Stay here only for pairwise relevance or semantic matching.

## Legal CAIL task shape mismatch

CAIL SCM uses relative similarity among documents and should not be treated as a
simple two-sentence paraphrase dataset without upstream format inspection.

## Finance matching access issues

AFQMC and competition/finance portals may require accounts or have moved pages.
Treat links as access clues and verify current rules before use.

## Label semantics unclear

Some rows omit label names. Ask for or inspect the downloaded files before
choosing binary classification, ranking loss, regression, or NLI metrics.
