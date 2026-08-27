# Workflows: NLTK Grammar, Parsing, Chunking, Trees, Semantics

These recipes are safe starting points for a Researcher using NLTK grammar/parsing/semantics APIs. They use in-memory grammars and tiny strings unless a section explicitly says an external resource or binary is required.

## 1. Author a tiny CFG and verify token coverage before parsing

Use this whenever a task starts from a hand-written grammar or an empty parse result.

```python
from nltk import CFG
from nltk.parse import ChartParser

cfg = CFG.fromstring("""
% start S
S -> NP VP
NP -> 'I' | 'John'
VP -> V NP
V -> 'saw'
""")
tokens = "I saw John".split()

cfg.check_coverage(tokens)       # raises ValueError if a terminal is missing
trees = list(ChartParser(cfg).parse(tokens))
assert len(trees) == 1
print(trees[0])
print(trees[0].leaves())
```

Checklist:

- Grammar terminals must exactly match tokens, including case and punctuation.
- `CFG.fromstring` start defaults to the first production unless `% start ...` is present.
- An empty parse list after `check_coverage` succeeds usually means the grammar shape cannot derive that token sequence, not that NLTK data is missing.

## 2. Compare parser behavior on an ambiguous grammar

Use this to explain why chart parsers enumerate ambiguity while shift-reduce can miss parses.

```python
from nltk import CFG
from nltk.parse import ChartParser, RecursiveDescentParser, ShiftReduceParser

ambiguous = CFG.fromstring("""
S -> NP VP
NP -> 'I' | Det N | Det N PP
VP -> V NP | V NP PP
PP -> P NP
Det -> 'the'
N -> 'dog' | 'park'
V -> 'saw'
P -> 'in'
""")
tokens = "I saw the dog in the park".split()

chart_trees = list(ChartParser(ambiguous).parse(tokens))
rd_trees = list(RecursiveDescentParser(ambiguous).parse(tokens))
sr_trees = list(ShiftReduceParser(ambiguous).parse(tokens))

print(len(chart_trees))  # 2 PP-attachment readings
print(len(rd_trees))     # 2 on this tiny grammar
print(len(sr_trees))     # 0 here: shift-reduce heuristics choose the wrong path
```

Interpretation rules:

- Use `ChartParser`/strategy subclasses when all parses matter.
- Use `RecursiveDescentParser` for small explanatory derivations; avoid left-recursive grammars and long inputs.
- Use `ShiftReduceParser` for a simple one-parse demonstration only; production order and ambiguity matter.
- If a highly ambiguous chart parse raises `ValueError` during tree extraction, inspect `nltk.parse.chart.MAX_PARSE_TREES` and reduce ambiguity or input length before raising the cap.

## 3. Use a PCFG and get a one-best probabilistic parse

Use this when the user needs probabilities or a preferred parse.

```python
from nltk.grammar import PCFG
from nltk.parse import ViterbiParser

pcfg = PCFG.fromstring("""
S -> NP VP [1.0]
NP -> 'I' [0.5] | 'John' [0.5]
VP -> V NP [1.0]
V -> 'saw' [1.0]
""")

tree = next(ViterbiParser(pcfg).parse("I saw John".split()))
print(tree)
print(tree.prob())
```

Checklist:

- For each left-hand side, probabilities must sum to `1.0` within `PCFG.EPSILON` (`0.01`).
- `ViterbiParser` returns one best tree, not all ambiguous parses.
- For treebank-induced PCFGs, derive productions from parsed `Tree` objects with `tree.productions()` and `induce_pcfg(start, productions)`; this requires parsed corpus data if the trees come from a corpus.

## 4. Parse a feature grammar and extract root semantics

Use this when feature unification or `SEM` values are part of the task.

```python
from nltk.grammar import FeatureGrammar
from nltk.parse import FeatureChartParser

fg = FeatureGrammar.fromstring("""
% start S
S[SEM=<see(speaker,john)>] -> 'I' 'saw' 'John'
""")

tree = next(FeatureChartParser(fg).parse("I saw John".split()))
semrep = tree.label()["SEM"]
print(tree)
print(semrep)       # see(speaker,john)
```

For grammar files, `nltk.sem.util.interpret_sents(...)` and `evaluate_sents(...)` can connect feature parse trees to semantic representations, but path/resource errors route through the data/downloader sub-skill.

## 5. Chunk POS-tagged tokens with `RegexpParser`

Use this after tokenization and POS tagging are already complete.

```python
from nltk.chunk import RegexpParser, tree2conlltags

sent = [("the", "DT"), ("quick", "JJ"), ("dog", "NN"), ("saw", "VBD"), ("John", "NNP")]
chunker = RegexpParser("""
NP: {<DT>?<JJ>*<NN.*>+}
""")

tree = chunker.parse(sent)
print(tree)
print(tree2conlltags(tree))
```

Rules:

- Tag patterns see `DT`, `JJ`, `NNP`, etc.; they do not see the words.
- Validate chunk output with `tree2conlltags`, `ChunkScore`, or direct subtree inspection.
- `tree2conlltags` supports shallow chunk trees; nested chunks raise `ValueError`.

## 6. Handle long noun-tag runs and curly-brace quantifiers

Use this for the difficult supplementary pattern from the focused unit test.

```python
from nltk.chunk import RegexpParser, tree2conlltags

sent = [
    ("The", "AT"), ("September-October", "NP"), ("term", "NN"), ("jury", "NN"),
    ("had", "HVD"), ("been", "BEN"), ("charged", "VBN"), ("by", "IN"),
    ("Fulton", "NP-TL"), ("Superior", "JJ-TL"),
    ("Court", "NN-TL"), ("Judge", "NN-TL"), ("Durwood", "NP"), ("Pye", "NP"),
]
chunker = RegexpParser("CHUNK: {<N.*>{4,}}")
tree = chunker.parse(sent)
print(tree)
print(tree2conlltags(tree)[-4:])
```

Expected signal: only the final four `N.*` tags are chunked because they are the first run of four or more matching noun-like tags.

## 7. Inspect and transform parse trees

Use this for parse-tree post-processing, grammar induction prep, or output formatting.

```python
from nltk.tree import Tree

t = Tree.fromstring("(S (NP I) (VP (V saw) (NP John)))")
print(t.label())
print(t.leaves())
print(t.treepositions())
print(t.productions())
print(t.pformat(margin=40))

cnf = t.copy(deep=True)
cnf.chomsky_normal_form()
cnf.collapse_unary(collapsePOS=False)
print(cnf)
```

Checklist:

- Use tree-position tuples for robust edits: `t[1, 1]`, `t.leaf_treeposition(0)`, `t.treeposition_spanning_leaves(0, 2)`.
- For parent pointers, convert the whole tree with `ParentedTree.convert(t)`; do not mix `Tree` and `ParentedTree` children.
- Use `freeze()` before putting trees in sets or using them as dictionary keys.

## 8. Build and evaluate dependency graphs

Use this for Malt/CoNLL-like dependency data or dependency-parser output.

```python
from nltk.parse import DependencyGraph, DependencyEvaluator

record = """
I PRP 2 SBJ
saw VBD 0 ROOT
John NNP 2 OBJ
"""
gold = DependencyGraph(record)
parsed = DependencyGraph(record)

print(gold.tree())
print(list(gold.triples()))
print(gold.to_conll(4))
print(DependencyEvaluator([parsed], [gold]).eval())  # (LAS, UAS)
```

Checklist:

- Default parsing supports 3, 4, 7, and 10 columns. Set `cell_separator='\t'` when whitespace inside fields matters.
- `DependencyEvaluator` requires equal node counts and matching word sequences; punctuation is ignored in LAS/UAS.
- `DependencyGraph.load(path)` reads through NLTK path security. If it rejects a path, use an allowed data root rather than bypassing the guard.

## 9. Evaluate first-order logic in a finite model

Use this for truth-conditional semantics examples and open-formula satisfiers.

```python
from nltk.sem import Assignment, Model, Valuation
from nltk.sem.logic import Expression

val = Valuation([
    ("fido", "d1"),
    ("dog", {"d1"}),
    ("bark", {"d1"}),
])
model = Model(val.domain, val)
g = Assignment(val.domain)

expr = Expression.fromstring("exists x.(dog(x) & bark(x))")
print(model.evaluate(str(expr), g))
print(sorted(model.satisfiers(Expression.fromstring("dog(x)"), "x", g)))
```

Interpretation checklist:

- `Model.evaluate(...)` returns the string `'Undefined'` for unresolved constants; do not confuse this with `False`.
- Keep domains tiny for examples. Nested quantifier/lambda paths are bounded by `Model.MAX_SATISFY_OPERATIONS`.
- Use `Expression.fromstring(..., type_check=True, signature={...})` when typed logic matters.

## 10. Convert a DRS to first-order logic

Use this when a semantic task mentions DRT/discourse representations.

```python
from nltk.sem.drt import DrtExpression

drs = DrtExpression.fromstring("([x],[dog(x), bark(x)])")
print(drs)
print(drs.fol())
print(drs.pretty_format())
```

`DrtExpression.equiv(...)` can use a theorem prover. Treat that as an inference-wrapper task and verify the prover first.

## 11. Use in-process theorem provers with explicit bounds

Use this only when a task explicitly asks for proof search and formulas are small.

```python
from nltk.inference import ResolutionProverCommand, TableauProverCommand
from nltk.sem import Expression

read = Expression.fromstring
goal = read("mortal(socrates)")
assumptions = [read("all x.(man(x) -> mortal(x))"), read("man(socrates)")]

print(ResolutionProverCommand(goal, assumptions).prove())
print(TableauProverCommand(goal, assumptions).prove())
```

Safety rules:

- `ResolutionProver.TIMEOUT` and `TableauProver.TIMEOUT` default to `60` seconds; `TableauProver.MAX_TABLEAU_DEPTH` defaults to `200`.
- Keep formulas and assumptions small. First-order proof search can be non-terminating or explosive.
- For Prover9/Mace, verify external binaries and timeout/model-size settings before invoking.

## 12. Route optional external parser/prover wrappers

Use wrappers only after verifying external requirements:

- CoreNLP: Java, CoreNLP JAR, models JAR, local server URL/port, `requests`, startup/stop lifecycle.
- Stanford parser: Java, Stanford parser/coreNLP JARs, model path, classpath.
- MaltParser: MaltParser directory, dependencies (`log4j.jar`, `libsvm.jar`, `liblinear-1.8.jar`), model `.mco` or training path, Java temp-file workflow.
- BLLIP: `bllipparser`, parser/reranker models, ASCII-only token caveat, not thread-safe.
- Prover9/Mace4: external binaries discoverable by NLTK or configured paths; timeouts/resource caps set.
- TransitionParser trained models: use trusted/current model files; NLTK loads through an allowlisted unpickler, but model provenance still matters.

## 13. Run the bundled no-download smoke

From any working directory in an environment with NLTK installed:

```bash
python /path/to/skills/disco/nltk/sub-skills/grammar-parse-semantics/scripts/grammar_parse_smoke.py --json
```

Expected signal: exit code `0` plus deterministic parse counts, chunk count, dependency LAS/UAS, semantic truth value, and DRT/FOL summary. The script performs no downloads, reads no NLTK data files, and invokes no external services or binaries.
