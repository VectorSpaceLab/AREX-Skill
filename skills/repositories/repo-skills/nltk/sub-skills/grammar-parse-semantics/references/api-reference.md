# API Reference: NLTK Grammar, Parsing, Chunking, Trees, Semantics

Version evidence from the prepared inspection facts: NLTK `3.10.2` on Python `3.13.14`. The APIs below are public package contracts distilled from `nltk/grammar.py`, `nltk/tree`, `nltk/chunk`, `nltk/parse`, `nltk/sem`, `nltk/inference`, doctests, focused unit tests, and security regressions. Examples are no-download unless explicitly marked as data/external dependent.

## Grammar construction

### Symbols and productions

```python
from nltk.grammar import Nonterminal, nonterminals, Production

S, NP, VP = nonterminals("S, NP, VP")
prod = Production(S, [NP, VP])
assert prod.lhs() == S
assert prod.rhs() == (NP, VP)
```

Contracts:

- `Nonterminal(symbol)` wraps a hashable node/category value; `symbol()` returns the wrapped value.
- `nonterminals("S, NP")` splits on commas or whitespace and returns `Nonterminal` objects in order.
- `Production(lhs, rhs)` expects a `Nonterminal` left-hand side and a sequence right-hand side. Do not pass a bare string as `rhs`; use `['word']` for lexical terminals.
- Terminals are hashable values that are not `Nonterminal` instances; examples normally use quoted strings.

### `CFG`

```python
from nltk import CFG

grammar = CFG.fromstring("""
% start S
S -> NP VP
NP -> 'I' | 'John'
VP -> V NP
V -> 'saw'
""")
```

Key contracts:

| API | Contract |
| --- | --- |
| `CFG(start, productions, calculate_leftcorners=True)` | Build from a `Nonterminal` start and a list of `Production` objects. |
| `CFG.fromstring(input, encoding=None)` | Parse one grammar string or a list of grammar lines. |
| `% start S` | Optional start directive; without it, the first production's left-hand side becomes the start symbol. |
| `grammar.start()` | Return the start `Nonterminal`. |
| `grammar.productions(lhs=None, rhs=None, empty=False)` | Return productions filtered by left-hand side, first right-hand-side symbol, or empty productions. |
| `grammar.check_coverage(tokens)` | Raise `ValueError` if any token is not licensed by a lexical production. |
| `grammar.leftcorners(cat)` / `is_leftcorner(cat, left)` | Left-corner relations used by optimized chart parsers. |
| `is_lexical()`, `is_nonlexical()`, `is_nonempty()`, `is_binarised()`, `is_chomsky_normal_form()` | Grammar-shape predicates. |
| `chomsky_normal_form(new_token_padding='@$@', flexible=False)` | Return a CNF-ish converted grammar; empty rules currently raise `ValueError`. |

Grammar string rules:

- Use `->` for productions and `|` for alternatives.
- Quote lexical terminals with single or double quotes: `N -> 'dog'`.
- Lines beginning with `#` and blank lines are ignored.
- A trailing backslash continues a grammar line.
- A malformed line raises `ValueError` with the line number and line text.

### `PCFG` and probabilistic productions

```python
from nltk.grammar import PCFG

pcfg = PCFG.fromstring("""
S -> NP VP [1.0]
NP -> 'I' [0.5] | 'John' [0.5]
VP -> V NP [1.0]
V -> 'saw' [1.0]
""")
```

Contracts:

- `PCFG` subclasses `CFG` and uses `ProbabilisticProduction` entries with `.prob()`.
- The probabilities for productions with the same left-hand side must sum to `1.0` within `PCFG.EPSILON` (`0.01`); otherwise construction raises `ValueError`.
- `PCFG.fromstring(...)` uses the same grammar string syntax plus bracketed probabilities such as `[0.7]`.
- `induce_pcfg(start, productions)` estimates probabilities from `Tree.productions()` counts.
- Use `ViterbiParser` for one-best PCFG parsing; use probabilistic chart parsers in `nltk.parse.pchart` when multiple ranked parses are needed.

### `FeatureGrammar`

```python
from nltk.grammar import FeatureGrammar

fg = FeatureGrammar.fromstring("""
% start S
S[SEM=<walk(john)>] -> 'John' 'walks'
NP[num=?n] -> Det[num=?n] N[num=?n]
Det[num=sg] -> 'a'
N[num=sg] -> 'dog'
""")
```

Contracts:

- `FeatureGrammar.fromstring(input, features=None, logic_parser=None, fstruct_reader=None, encoding=None)` parses feature-structured nonterminals.
- Feature grammars use `FeatStructNonterminal` internally; labels can contain feature values such as `num=?n`, boolean features like `-pl`, and semantic expressions in `SEM`.
- `FeatureGrammar.productions(lhs=None, rhs=None, empty=False)` indexes by the nonterminal `TYPE` feature when available.
- `FeatureGrammar.leftcorners()` and `leftcorner_parents()` are not implemented; use feature chart parsers rather than left-corner-specific assumptions for feature grammars.
- Connecting syntax to semantics typically reads `tree.label()['SEM']` on a feature parse tree or uses `nltk.sem.util.root_semrep`.

## Parser APIs

### Common parser interface

All parser classes implement `ParserI` patterns:

| API | Contract |
| --- | --- |
| `parse(sent, *args, **kwargs)` | Return an iterator of `Tree` objects. Materialize with `list(...)` only when parse counts are bounded. |
| `parse_sents(sents, ...)` | Return an iterator over per-sentence parse iterators. |
| `parse_all(sent, ...)` | Return `list(parse(sent))`. |
| `parse_one(sent, ...)` | Return the first parse or `None`. |
| `grammar()` | Return the parser's grammar when implemented. |

Always pass token lists such as `['I', 'saw', 'John']`, not untokenized strings, to CFG/PCFG parsers.

### Recursive descent and shift-reduce

```python
from nltk.parse import RecursiveDescentParser, ShiftReduceParser

rd = RecursiveDescentParser(grammar, trace=0)
sr = ShiftReduceParser(grammar, trace=0)
```

| Parser | Behavior | Use/caveat |
| --- | --- | --- |
| `RecursiveDescentParser(grammar, trace=0)` | Top-down parser; recursively expands the frontier and yields all parses it finds. | Good for explaining derivations on tiny grammars. Left recursion and broad ambiguity can be very slow. |
| `SteppingRecursiveDescentParser(grammar, trace=0)` | Exposes `initialize`, `step`, `expand`, `match`, `backtrack`, and `parses`. | Educational/debug workflow. |
| `ShiftReduceParser(grammar, trace=0)` | Bottom-up parser using shift and reduce; reduces before shifting when possible and uses earliest matching production. | Returns at most one parse and can miss parses or fail on ambiguous inputs. |
| `SteppingShiftReduceParser(grammar, trace=0)` | Exposes stack, remaining text, `shift`, `reduce`, `undo`, and current parses. | Debug/teaching workflow. |

Both `RecursiveDescentParser.parse` and `ShiftReduceParser.parse` call `grammar.check_coverage(tokens)` and raise `ValueError` on uncovered tokens.

### Chart and Earley parsers

```python
from nltk.parse import ChartParser, BottomUpChartParser

parser = ChartParser(grammar, trace=0)
chart = parser.chart_parse(tokens)
trees = list(chart.parses(grammar.start()))
```

| API | Contract |
| --- | --- |
| `ChartParser(grammar, strategy=BU_LC_STRATEGY, trace=0, trace_chart_width=50, use_agenda=True, chart_class=Chart)` | Generic chart parser; default strategy is bottom-up left-corner. |
| `chart_parse(tokens, trace=None)` | Return a final `Chart` with edges and child pointers. |
| `parse(tokens, tree_class=Tree)` | Return an iterator over trees extracted from the chart. |
| `TopDownChartParser`, `BottomUpChartParser`, `BottomUpLeftCornerChartParser`, `LeftCornerChartParser` | Strategy-specific convenience wrappers. `LeftCornerChartParser` requires a non-empty grammar. |
| `EarleyChartParser`, `Incremental*ChartParser` | Incremental/Earley-family chart parsers in `nltk.parse.earleychart`. |
| `SteppingChartParser` | Stepwise chart parsing with strategy switching and chart inspection. |

Safety/resource guard: `nltk.parse.chart.MAX_PARSE_TREES` defaults to `1_000_000` parse-tree nodes. Highly ambiguous grammars such as `S -> S S | 'a'` can yield exponentially many parses; extracting trees above the cap raises `ValueError` instead of running unbounded.

### Probabilistic parsers

```python
from nltk.parse import ViterbiParser

tree = next(ViterbiParser(pcfg).parse(tokens))
probability = tree.prob()
```

- `ViterbiParser(PCFG, trace=0)` returns the single most likely parse as a `ProbabilisticTree`.
- `nltk.parse.pchart` exports `InsideChartParser`, `RandomChartParser`, `UnsortedChartParser`, `LongestChartParser`, and `BottomUpProbabilisticChartParser` for ranked/probabilistic chart workflows.
- Probabilistic parsers still require exact lexical coverage from the PCFG.

### Feature chart parsers

```python
from nltk.parse import FeatureChartParser, FeatureTopDownChartParser

trees = list(FeatureChartParser(fg).parse(tokens))
```

- `FeatureChartParser(grammar, strategy=BU_LC_FEATURE_STRATEGY, trace_chart_width=20, chart_class=FeatureChart, **parser_args)` handles feature unification while chart parsing.
- Convenience wrappers: `FeatureTopDownChartParser`, `FeatureBottomUpChartParser`, `FeatureBottomUpLeftCornerChartParser`, plus Earley/incremental feature parsers.
- Feature variables are renamed across productions where needed; compare frozen trees if you need set equality.

## Chunking APIs

### `RegexpParser`

```python
from nltk.chunk import RegexpParser

chunker = RegexpParser("""
NP: {<DT>?<JJ>*<NN.*>+}
""")
tree = chunker.parse([('the', 'DT'), ('small', 'JJ'), ('dog', 'NN')])
```

Contracts:

- `RegexpParser(grammar, root_label='S', loop=1, trace=0)` returns a chunk parser built from one or more stage clauses.
- Input must be a list/tree of tagged tuples or chunk `Tree` objects. Raw strings are not tags.
- Each stage begins with `LABEL:` and contains ordered rules. Earlier rules can affect later rule matches.
- Rule bodies use tag patterns, not raw regex over words.

Chunk rule forms:

| Rule form | Meaning |
| --- | --- |
| `{<DT>?<JJ>*<NN.*>+}` | Chunk matching tag sequence. |
| `}<VBD|IN|\.>{` | Strip matching tags from inside an existing chunk. |
| `<DT><NN>}{<DT><NN>` | Split a chunk between left and right tag patterns. |
| `<DT|JJ>{}<NN.*>` | Merge adjacent chunks ending/starting with matching tags. |
| `<A>{<B>}<C>` | Chunk `<B>` only in left/right context. |

`tag_pattern2re_pattern(tag_pattern)` converts tag patterns to regular expressions and raises `ValueError` for bad tag patterns. Curly-brace quantifiers such as `{<N.*>{4,}}` are supported by the focused unit tests.

### Chunk scoring and format conversions

```python
from nltk.chunk import ChunkScore, tagstr2tree, tree2conlltags, conlltags2tree
```

| API | Contract |
| --- | --- |
| `tagstr2tree(s, chunk_label='NP', root_label='S', sep='/', ...)` | Parse bracketed tagged text such as `[ the/DT dog/NN ] barked/VBD`. |
| `tree2conlltags(tree)` | Convert a shallow chunk tree to `(word, tag, iob)` triples; raises `ValueError` for too-deep/nested chunk trees. |
| `conlltags2tree(sentence, chunk_types=('NP','PP','VP'), root_label='S', strict=False)` | Convert IOB triples to a chunk tree. |
| `conllstr2tree(s, chunk_types=('NP','PP','VP'), root_label='S')` | Convert CoNLL-2000-style text to a chunk tree. |
| `tree2conllstr(tree)` | Serialize a chunk tree to CoNLL lines. |
| `ChunkScore().score(gold, guessed)` | Accumulate chunk precision/recall/F-measure and tag accuracy. |
| `accuracy(chunker, gold)` | Rechunk flattened gold trees and compute IOB-tag accuracy. |

Named entity chunking via `ne_chunk` is data-dependent and routes through data/downloader if the required model and words resources are missing.

## Tree APIs

```python
from nltk.tree import Tree, ParentedTree, ImmutableTree

t = Tree.fromstring('(S (NP I) (VP (V saw) (NP John)))')
```

Core methods:

| API | Contract |
| --- | --- |
| `Tree(label, children)` | Construct a tree from a node label and a list of children. |
| `Tree.fromstring(s, brackets='()', read_node=None, read_leaf=None, node_pattern=None, leaf_pattern=None, remove_empty_top_bracketing=False)` | Parse bracketed tree strings; raises helpful `ValueError`/`TypeError` for malformed input. |
| `label()` / `set_label(label)` | Read or update the node label. |
| `leaves()` / `flatten()` / `height()` | Inspect leaves and tree shape. |
| `treepositions(order='preorder')`, `leaf_treeposition(i)`, `treeposition_spanning_leaves(start, end)` | Work with tree-position tuples. |
| `subtrees(filter=None)` | Iterate subtrees, optionally filtered. |
| `productions()` | Generate CFG productions from a string-labeled tree. |
| `pos()` | Extract leaf/POS pairs from preterminal labels. |
| `copy(deep=False)`, `freeze(leaf_freezer=None)`, `convert(tree)` | Copy, hash/freeze, or convert tree subclasses. |
| `pformat(...)`, `pprint(...)`, `pretty_print(...)`, `pformat_latex_qtree()`, `pformat_latex_forest()` | Serialize/print trees. |
| `chomsky_normal_form(...)`, `un_chomsky_normal_form(...)`, `collapse_unary(...)` | Tree transformations used before grammar induction or parser training. |

Subclass caveats:

- `ParentedTree` maintains parent pointers (`parent()`, `parent_index()`, `left_sibling()`, `right_sibling()`, `root()`, `treeposition()`). Do not mix plain `Tree` and `ParentedTree` inside the same structure.
- `ImmutableTree` cannot be modified and is useful as a set/dictionary key or comparison artifact.
- `Tree.draw()` and rich SVG display require GUI/rendering dependencies; treat as optional.

## Dependency graph APIs

```python
from nltk.parse import DependencyGraph, DependencyEvaluator

dg = DependencyGraph("""
I PRP 2 SBJ
saw VBD 0 ROOT
John NNP 2 OBJ
""")
```

Contracts:

| API | Contract |
| --- | --- |
| `DependencyGraph(tree_str=None, cell_extractor=None, zero_based=False, cell_separator=None, top_relation_label='ROOT')` | Parse Malt-TAB/CoNLL-like dependency text. Supports 3, 4, 7, or 10 cells per line by default. |
| `DependencyGraph.load(filename, zero_based=False, cell_separator=None, top_relation_label='ROOT')` | Load one or more blank-line-separated graphs from a file through NLTK path security. |
| `nodes`, `root` | Node storage and root node. Node `0` is a dummy top node. |
| `tree()` | Build an NLTK `Tree` rooted at the dependency root; dependency labels are omitted. |
| `triples(node=None)` | Yield `((head_word, head_tag), rel, (dep_word, dep_tag))` triples. |
| `to_conll(style)` | Serialize to 3-, 4-, or 10-column CoNLL format. |
| `to_dot()` / `_repr_svg_()` / `nx_graph()` | Graphviz/networkx representations; optional dependencies/binaries may be needed. |
| `contains_cycle()` | Return `False` or a cycle path. Current implementation is linear-time in graph size. |
| `DependencyEvaluator(parsed_sents, gold_sents).eval()` | Return `(LAS, UAS)` and ignore punctuation. Requires equal sentence lengths and matching word sequences. |

Rule-based dependency grammars are built with `DependencyGrammar.fromstring(...)` using single-quoted heads and modifiers, e.g. `'saw' -> 'I' | 'John'`, then parsed with `ProjectiveDependencyParser` or `NonprojectiveDependencyParser` for small examples. Projective parsing has a `MAX_TOKENS` guard because its chart is O(n²) memory/O(n³) time.

## Semantics and logic APIs

### Logic expressions

```python
from nltk.sem.logic import Expression

read_expr = Expression.fromstring
expr = read_expr('exists x.(dog(x) & bark(x))')
```

Contracts:

- `Expression.fromstring(s, type_check=False, signature=None)` parses first-order logic and lambda expressions.
- Operators include negation `-`, conjunction `&`, disjunction `|`, implication `->`, equivalence `<->`, equality `=`, inequality `!=`, existential `exists`, universal `all`, and lambda `\`.
- Use `.simplify()` for beta conversion, `.typecheck(signature)` or `type_check=True` for typed logic, `.free()`, `.constants()`, `.predicates()`, and `.variables()` for symbol inspection.
- `expr.equiv(other, prover=None)` uses a theorem prover; without an explicit prover it constructs `Prover9()` and therefore requires the external Prover9 binary.
- `LogicParser.MAX_PARSE_DEPTH` defaults to `200`; pathologically deep expressions raise `LogicalExpressionException` rather than causing unbounded recursion.

### Model-theoretic evaluation

```python
from nltk.sem import Valuation, Model, Assignment

val = Valuation([('fido', 'd1'), ('dog', {'d1'}), ('bark', {'d1'})])
model = Model(val.domain, val)
g = Assignment(val.domain)
assert model.evaluate('exists x.(dog(x) & bark(x))', g) is True
```

Contracts:

| API | Contract |
| --- | --- |
| `Valuation(list_of_pairs)` / `Valuation.fromstring(s)` | Map non-logical constants to individuals, booleans, or relations. Sets of strings become unary relations. |
| `val.domain`, `val.symbols` | Domain inferred from values and sorted constant names. |
| `Assignment(domain, assign=None)` | Map individual variables to domain values. `.add(var, val)` and `.purge(var=None)` update it. |
| `Model(domain, valuation)` | Domain must contain `valuation.domain`. |
| `model.evaluate(expr_string, assignment, trace=None)` | Return truth value, semantic value, or string `'Undefined'` for unresolved symbols. |
| `model.satisfy(parsed_expr, assignment, trace=None)` | Evaluate an already parsed `Expression`; may raise `Undefined` or resource-bound `Error`. |
| `model.satisfiers(parsed_expr, variable, assignment, trace=None)` | Return the set of domain values satisfying an open formula. |

`Model.MAX_SATISFY_OPERATIONS` defaults to `1_000_000` and refuses formulas whose nested quantifier/lambda path would explore too many domain-value combinations.

### Syntax-to-semantics utilities

`nltk.sem.util` provides file/grammar helpers:

- `parse_sents(inputs, grammar, trace=0)` parses whitespace-split sentences with a `FeatureGrammar` or grammar resource path.
- `root_semrep(syntree, semkey='SEM')` extracts root semantics from a feature-tree label.
- `interpret_sents(inputs, grammar, semkey='SEM', trace=0)` returns `(syntax_tree, semantic_expression)` pairs.
- `evaluate_sents(inputs, grammar, model, assignment, trace=0)` adds model-evaluation results.

When `grammar` is a path such as `grammars/sample_grammars/sem2.fcfg`, route missing data/resource errors through data/downloader. Use in-memory `FeatureGrammar` objects for no-download tests.

### DRT

```python
from nltk.sem.drt import DrtExpression

drs = DrtExpression.fromstring('([x],[dog(x), bark(x)])')
fol = drs.fol()
```

- `DrtExpression.fromstring(s)` parses DRT expressions.
- `DRS` objects support `.fol()` conversion to first-order logic, `.pretty_format()`, `.resolve_anaphora()`, and `.eliminate_equality()` where applicable.
- `DrtExpression.equiv(other, prover=None)` can call a theorem prover through FOL conversion.

## Inference APIs and external prover caveats

| API | Contract/caveat |
| --- | --- |
| `ResolutionProver`, `ResolutionProverCommand` | In-process first-order resolution. `ResolutionProver.TIMEOUT` defaults to `60`; `0` disables the wall-clock bound. |
| `TableauProver`, `TableauProverCommand` | In-process tableau prover. `TIMEOUT` defaults to `60`; `MAX_TABLEAU_DEPTH` defaults to `200`. |
| `Prover9`, `Prover9Command` | External Prover9 binary wrapper. `Prover9(timeout=60)` adds `assign(max_seconds, timeout)` to input. Needs binary discovery/config. |
| `Mace`, `MaceCommand` | External Mace4 model builder wrapper. `Mace(end_size=500)` bounds model size; needs Mace4/interpformat binaries. |
| `BaseProverCommand`, `BaseModelBuilderCommand` | Store goals/assumptions, cache results, and expose proof/model strings. |

Do not invoke Prover9/Mace in a base smoke unless the task has verified the external binaries and resource bounds.

## Optional parser wrappers

These are routeable caveats, not minimum verified base workflows:

| Wrapper | Requirement/caveat |
| --- | --- |
| `CoreNLPParser`, `CoreNLPDependencyParser`, `CoreNLPServer` | Stanford CoreNLP JAR/model JARs, Java, local server/HTTP requests, port management. |
| `StanfordParser`, `StanfordDependencyParser`, `StanfordNeuralDependencyParser` | Stanford parser JAR/model JARs and Java classpath. |
| `MaltParser` | MaltParser directory/JARs, optional model `.mco`, Java, temp files. Relative parser directories are intentionally not resolved from CWD. |
| `BllipParser` | `bllipparser` Python module/model directory; not thread-safe and rejects non-ASCII tokens. |
| `TransitionParser` | Optional `numpy`, `scipy`, `sklearn`; training writes a pickle model, parsing loads with an allowlisted unpickler. Use trusted/current model files only. |
| Graphviz rendering from `DependencyGraph._repr_svg_()` | `dot` binary; NLTK uses validated binary discovery rather than bare CWD execution. |
