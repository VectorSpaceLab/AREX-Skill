# Pattern engines

This reference is for the CoreNLP pattern and rewrite helpers that sit on top of Stanza or CoreNLP.

## Quick chooser

| Need | Use | Input | Output |
| --- | --- | --- | --- |
| Token-level pattern matching on raw text | `client.tokensregex(...)` or `stanza.server.tokensregex.process_doc(...)` | text or `Document` | JSON matches |
| Dependency-graph pattern matching | `client.semgrex(...)` or `stanza.server.semgrex.process_doc(...)` | text or `Document` | JSON matches |
| Constituency-tree pattern matching | `client.tregex(...)` or `stanza.server.tsurgeon.process_trees(...)` | text or `Tree` objects | JSON matches or rewritten trees |
| Dependency-graph rewriting | `stanza.server.ssurgeon.process_doc(...)` | `Document` | `SsurgeonResponse` / updated `Document` |
| Lemma helper for English words | `stanza.server.morphology.process_text(...)` | word list + XPOS tags | `MorphologyResponse` |

## TokensRegex

Best for token-sequence matching on server-annotated text.

Examples from the installed tests/demos:
- `"Opal"`
- `"[ner: GEM]"`
- `"([ner: PERSON]+) /wrote/ /an?/ []{0,3} /sentence|article/"`

Notes:
- Use this when the server already tokenized the text and you want a token-pattern result.
- `to_words=True` flattens the JSON result into indexed-word dictionaries.
- `filter=True` asks the server to return filtered matches instead of all matches.

## Semgrex

There are two important semgrex paths:

1. `client.semgrex(text, pattern, ...)` — raw text through the CoreNLP server.
2. `stanza.server.semgrex.process_doc(doc, *patterns, enhanced=False)` — Stanza `Document` dependency graphs.

Examples from the installed tests/demos:
- `{word:wrote} >nsubj {}=subject >obj {}=object`
- `{cpos:PROPN}=source <=zzz {ner:GEM}=target`
- `{cpos:NOUN}=thing <obj {cpos:VERB}=action`

Notes:
- Use `enhanced=True` when you want to run against enhanced dependency graphs from the `Document`.
- The doc-based helper can annotate sentences with comments via `annotate_doc(...)`.
- `matches_only` and `exclude_matches` are useful when you want to keep only matching or non-matching sentences.

## Tregex and Tsurgeon

Tregex works on constituency trees.

Examples from the installed tests/demos:
- `PP < NP`
- `WP=wp`
- `s1_4 > (__=home > (__=parent > __=grandparent)) . (s1_3 > (__=move > =grandparent))`

Tsurgeon operations:
- `relabel wp WWWPPP`
- `move move $+ home`

Notes:
- `client.tregex(..., trees=...)` can accept tree objects directly.
- `stanza.server.tsurgeon.process_trees(trees, (tregex, tsurgeon, ...))` rewrites trees in-process.
- Each tsurgeon operation must include a tregex pattern plus one or more edit commands.

## Ssurgeon

Ssurgeon rewrites dependency graphs and is usually the most delicate helper in this sub-skill.

Examples from the installed tests/demos:
- `{}=source >nsubj {} >csubj=bad {}` + `relabelNamedEdge -edge bad -reln advcl`
- `"{word:antennae}=antennae !> {word:blue}"` + `addDep ...`
- `"{word:It}=it . {word:/'s/}=s"` + `EditNode ... -is_mwt true`

Important details:
- It can add or rewrite MWT spans, roots, and dependency edges.
- The conversion helper preserves `SpaceAfter`, `SpacesAfter`, `SpacesBefore`, and other misc fields when possible.
- It is built for graph surgery after a Stanza `Document` has already been parsed.

## Morphology helper

`stanza.server.morphology.process_text(words, xpos_tags)` and `Morphology.process(...)` call the Java morphology engine directly.

Use it when:
- you only need lemmas for `(word, XPOS)` pairs,
- you already know the input is English,
- and you want a small, direct helper instead of a full server round trip.

Do not use UPOS here; the helper expects PTB/XPOS tags.

## Practical guardrails

- Choose the helper that matches your input type before choosing a pattern syntax.
- `client.semgrex` and `client.tokensregex` are live server calls; the doc-based helpers are still Java-backed but operate on Stanza `Document` objects.
- If you only need a pattern syntax explanation, use the bundled script and this reference rather than the original demos.
