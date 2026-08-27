---
name: grammar-parse-semantics
description: "Use NLTK grammars, parsers, chunkers, trees, dependency graphs,
  semantic logic, and inference APIs without reopening the source repo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Grammar Parse Semantics

Use this sub-skill when the task is about NLTK grammar authoring, parse-tree generation or inspection, regular-expression chunking, dependency graph handling, semantic interpretation, logic expressions, or theorem-proving/model-building wrappers.

Route away from this sub-skill when the task is mainly about:

- Installing or locating NLTK data packages, sample grammars, corpora, or model resources: use `../data-and-downloader/SKILL.md` first.
- Tokenization, POS tagging, stemming, lemmatization, or VADER preprocessing before parsing/chunking: use `../tokenize-tag-stem/SKILL.md` when available.
- Classifiers, language models, probability distributions, metrics, or translation/alignment: use `../ml-metrics-and-translation/SKILL.md`.

## Fast Paths

- For small grammar workflows, prefer in-memory `CFG.fromstring(...)`, `PCFG.fromstring(...)`, or `FeatureGrammar.fromstring(...)`; then parse already-tokenized input with `ChartParser`, `RecursiveDescentParser`, `ShiftReduceParser`, `ViterbiParser`, or feature chart parsers.
- When a parser returns no trees, first check exact terminal/token alignment with `grammar.check_coverage(tokens)`, casing, punctuation, and the grammar start symbol before changing parser strategy.
- For ambiguity, use `ChartParser` or chart strategy subclasses and count/inspect all returned trees. Use `ShiftReduceParser` only when a single heuristic parse is acceptable; it can miss parses in ambiguous grammars.
- For chunking, feed `RegexpParser` POS-tagged tuples such as `[('the', 'DT'), ('dog', 'NN')]`; chunk grammars operate over tags, not raw words.
- For tree manipulation, use `Tree.fromstring`, `label()`, `leaves()`, `treepositions()`, `subtrees()`, `productions()`, `pformat()`, `chomsky_normal_form()`, and `collapse_unary()` rather than manually traversing nested lists.
- For dependency input, start with a tiny Malt/CoNLL string and `DependencyGraph`; use `DependencyEvaluator` only after verifying equal token sequences.
- For semantics, parse expressions with `Expression.fromstring`, evaluate with `Valuation`, `Assignment`, and `Model`, and use `FeatureGrammar` `SEM` features when connecting parse trees to semantic representations.
- Treat CoreNLP, Stanford, Malt, BLLIP, Prover9, Mace4, Graphviz rendering, and trained transition-parser models as optional external-wrapper workflows. They require external services, Java/JARs, binaries, models, or trusted model files and are not part of the base no-download path.

## Reference Map

- Public grammar, parser, chunker, tree, dependency, semantics, inference, and optional wrapper API contracts: [`references/api-reference.md`](references/api-reference.md).
- Task recipes for CFG/PCFG/feature grammars, parser comparisons, chunking, tree transforms, dependency graphs, semantic models, DRT, and wrapper caveats: [`references/workflows.md`](references/workflows.md).
- Failure diagnosis for empty parses, malformed grammars, chunk regexes, tree parsing, dependency files, semantic logic, resource bounds, and optional wrappers: [`references/troubleshooting.md`](references/troubleshooting.md).
- Tiny in-memory no-download runtime check covering CFG/chart/RD/shift-reduce parsing, PCFG/Viterbi, feature grammar semantics, chunking, trees, dependency graphs, logic/model evaluation, and DRT: [`scripts/grammar_parse_smoke.py`](scripts/grammar_parse_smoke.py).

## Minimum Validation Pattern

1. Print `nltk.__version__`, Python version, and the parser or grammar class being used.
2. Keep tokenization/tagging explicit; for CFG/PCFG parsers, assert `grammar.check_coverage(tokens)` succeeds before interpreting an empty parse list.
3. For ambiguity-sensitive tasks, report parse count and the parser strategy; do not silently take the first tree unless the task says one-best is acceptable.
4. For `RegexpParser`, assert input is POS-tagged, run `tree2conlltags()` or inspect `Tree` subtrees, and document whether nested chunks are expected.
5. For semantic workflows, assert the parsed expression, valuation domain, assignment, and `Model.evaluate(...)` result; handle `'Undefined'` separately from `False`.
6. For external parser/prover wrappers, verify the exact external binary/JAR/service/model path and timeout/resource settings before invoking them.
7. Run the bundled no-download smoke from any current working directory in an environment with NLTK installed:

```bash
python /path/to/skills/disco/nltk/sub-skills/grammar-parse-semantics/scripts/grammar_parse_smoke.py --help
python /path/to/skills/disco/nltk/sub-skills/grammar-parse-semantics/scripts/grammar_parse_smoke.py --json
```
