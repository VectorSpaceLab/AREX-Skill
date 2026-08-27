# Conversation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| model not shown in dropdown | `LLM_MODEL` not in `AVAIL_LLM_MODELS` or config precedence override | update `config_private.py`, restart, inspect with `scripts/inspect_runtime.py --repo-root <checkout>` |
| immediate API-key error | wrong key for selected provider or stale env var | match provider-specific key to model prefix; strip whitespace; avoid printing key |
| search returns 429 or no results | public SearXNG overloaded or blocked | configure private `SEARXNG_URLS`, lower frequency, or ask user for URLs |
| search can fetch pages but answer is weak | query too broad or page extraction poor | refine query; provide trusted URLs; use stronger model for synthesis |
| RAG build fails on file | unsupported file type, too large, missing reader dependency, or path not server-visible | upload again, convert format, split large files, or use `academic-docs` for PDF/document extraction |
| RAG answer ignores injected data | vector store not built/injected or embedding provider failed | rebuild knowledge base, verify embedding key, ask a question with specific terms from the source |
| conversation archive cannot load | expired upload path or incompatible archive | re-upload archive; use save/load plugins rather than browser-local paths |
| Mermaid output does not render | malformed Mermaid syntax from model | ask model to output only one diagram block; simplify diagram type and labels |
| core prompt button gives irrelevant output | wrong input kind or model not suited | use a domain sub-skill for documents/code/media; switch to stronger model for nuanced tasks |
