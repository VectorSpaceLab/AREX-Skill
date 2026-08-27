# Troubleshooting

## Stale external links and network issues

- The README is a legacy curated link collection, so some URLs may redirect, disappear, require JavaScript, or be blocked by the network available to the runtime.
- Prefer the topic family label plus a short description over the exact historical URL when a link looks stale.
- If a user wants a live external tutorial and the link is broken, say it is likely stale and offer the nearest family from `topic-index.md` instead of inventing a replacement URL.
- Do not assume internet access is available when answering.

## Python 2 syntax in the legacy snippets

- Replace bare `print x, y` forms with `print(x, y)`.
- Keep the list-comprehension patterns, but update variable names and formatting to Python 3 style.
- Treat `str.find()` as a method that returns `-1` when no match is found.
- If the user asks for a general data-science column operation, prefer pandas or NumPy guidance over the plain list-of-lists snippet.

## Ambiguous tutorial-vs-code requests

- If the request says "tutorial", "resources", "where can I learn", or "reading list", answer with the best README family and one supporting resource.
- If the request says "show code", "modernize", or "convert", answer with the Python 3 snippet from `python-basics.md`.
- If the request asks for executable regression or modeling work, route to `../../statsmodels-logit-workflow/` or `../../kaggle-linear-models/` instead of staying in this router.
- If the request mentions Twitter ingestion, streaming, or JSON capture, route to `../../twitter-json-workflow/`.
- If the intent is still mixed after those cues, ask a single clarifying question that separates learning resources from runnable workflow help.
