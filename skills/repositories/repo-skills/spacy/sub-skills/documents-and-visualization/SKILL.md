---
name: documents-and-visualization
description: "Work with spaCy Doc, Token, Span, DocBin, tokenization, matchers,
  serialization, scoring, and displaCy visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# documents-and-visualization

Use this sub-skill for the core spaCy document model: tokenization, `Doc`/`Token`/`Span` APIs, `DocBin` serialization, rule-based matching, `EntityRuler`/`SpanRuler`, scoring, and displaCy HTML rendering.

## Read first

- [references/doc-token-span-api.md](references/doc-token-span-api.md) for verified signatures and object-model details.
- [references/tokenization-language-data.md](references/tokenization-language-data.md) for blank pipelines, language classes, and tokenizer customization.
- [references/matching-and-rulers.md](references/matching-and-rulers.md) for `Matcher`, `PhraseMatcher`, `DependencyMatcher`, `EntityRuler`, and `SpanRuler`.
- [references/serialization-scoring-visualization.md](references/serialization-scoring-visualization.md) for `DocBin`, scoring, and displaCy output patterns.
- [references/troubleshooting.md](references/troubleshooting.md) when span offsets, matcher patterns, serialization, or HTML rendering go wrong.
- [scripts/doc_api_smoke.py](scripts/doc_api_smoke.py) for a safe blank-pipeline smoke that exercises the object model and matcher basics.
- [scripts/render_displacy_sample.py](scripts/render_displacy_sample.py) for a tiny manual HTML render check.

## What this sub-skill covers

- `spacy.blank()` and `spacy.load()` for processing text with an existing package or local pipeline.
- `nlp(text)` and `nlp.pipe()` for document streaming and `as_tuples` context.
- `Doc`, `Token`, `Span`, extension attributes, `char_span`, `retokenize`, and `DocBin` round-trips.
- Tokenizer behavior, language data, and blank-language caveats.
- Rule-based matching and entity/span rulers for token-pattern workflows.
- displaCy rendering for entities, dependencies, and spans.

## What to route elsewhere

- Install/import, version, CLI entry-point, missing model package, or backend questions: `install-and-inspect`.
- Custom pipeline factories/components, `add_pipe`, registry wiring, or pipe analysis: `pipeline-components`.
- `init config`, `debug config`, `convert`, `train`, `evaluate`, `package`, or `validate`: `training-and-cli`.
- `spacy project` clone/assets/run/push/pull/DVC workflows: `project-workflows`.

## Quick use pattern

1. Start from the object you need: `Doc`, `Span`, `Token`, matcher, ruler, or displacy.
2. Check the exact signature in the reference before assuming optional parameters.
3. Run the bundled smoke script if you need a safe no-download proof of behavior.
4. Use the troubleshooting reference when offsets, tokenization, or serialized artifacts do not line up.

## Evidence basis

This sub-skill is distilled from spaCy's public docs, verified installed-package signatures, core token/matcher/serialization source, and behavior-backed tests. It is self-contained and does not require reopening the source checkout.
