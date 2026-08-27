# Troubleshooting: NLTK Grammar, Parsing, Chunking, Trees, Semantics

Use this when a grammar/parser/chunker/tree/dependency/semantic workflow fails after routing to this sub-skill. Start with tiny in-memory reproductions and no-download checks before adding corpora, sample grammar files, GUI renderers, Java wrappers, or theorem-prover binaries.

## Empty parses and token/grammar mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `list(parser.parse(tokens)) == []` | Grammar does not derive the token sequence even though all terminals exist. | Use `ChartParser` for diagnostics, print `grammar.start()`, `grammar.productions()`, and test a shorter derivable token sequence. |
| `ValueError: Grammar does not cover some of the input words` | One or more tokens are missing lexical productions. | Call `grammar.check_coverage(tokens)` before parsing; align case, punctuation, tokenization, and quoted terminals exactly. |
| A sentence string is parsed as characters or fails unexpectedly | Parser expected a token list, but received a raw string. | Pass `sentence.split()` or an explicit token list. Tokenization itself routes to the tokenizer sub-skill. |
| A grammar looks correct but starts from the wrong symbol | No `% start ...` directive and the first production is not the desired root. | Add `% start S` or construct `CFG(Nonterminal('S'), productions)`. |
| A data grammar path such as `grammars/...` fails | The grammar file is an NLTK data resource, not part of the base in-memory API. | Route missing resource/path diagnosis to data/downloader; for no-download checks, use `CFG.fromstring` or `FeatureGrammar.fromstring`. |

## Ambiguity and parser performance

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ChartParser` returns multiple trees | The grammar/text is ambiguous. | Report parse count and inspect the distinct attachments/subtrees; use PCFG/Viterbi if one-best ranking is required. |
| `ShiftReduceParser` returns zero or one tree where chart parsing returns more | Shift-reduce uses deterministic heuristics and production order. | Do not use shift-reduce as an exhaustive parser; use chart/recursive descent for all parses. |
| Recursive descent hangs or grows very slowly | Left recursion, broad top-down expansion, or high ambiguity. | Use a chart parser, refactor left recursion, or constrain grammar/input length. |
| Tree extraction raises `ValueError` about highly ambiguous grammar or parse-tree node limit | The chart forest exceeded `nltk.parse.chart.MAX_PARSE_TREES` (`1_000_000` by default). | Reduce ambiguity/input length, inspect chart edges before trees, or raise the cap only after confirming memory/time budget. |
| Probabilistic grammar construction raises probability sum error | A left-hand side's PCFG productions do not sum to 1.0 within `PCFG.EPSILON`. | Group productions by LHS and normalize probabilities. |
| Viterbi returns no tree | PCFG coverage or derivation failure. | First run `pcfg.check_coverage(tokens)`, then test a minimal derivable token sequence. |

## Grammar string and feature grammar errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ValueError: Expected an arrow` | Malformed production syntax. | Use `LHS -> RHS`; quote terminals; put comments on separate or trailing lines. |
| `ValueError: Unterminated string` | Terminal quote mismatch. | Use balanced single or double quotes around terminals. |
| `ValueError: No productions found` | Empty grammar after comments/blank lines or malformed input. | Print the exact grammar string and check indentation/line continuation. |
| Feature parse unexpectedly fails | Feature values do not unify or variables are bound inconsistently. | Print the feature grammar and parse a shorter sentence; inspect feature variables such as `?n` and boolean features like `-pl`. |
| Feature left-corner methods fail | `FeatureGrammar.leftcorners()` and `leftcorner_parents()` are not implemented. | Use `FeatureChartParser`/feature chart classes and avoid code paths requiring those methods. |
| Semantic feature cannot be read | Root tree label lacks the expected key (`SEM` by default). | Check `tree.label()` and use the correct semantic key, e.g. lowercase `sem` for legacy grammars. |

## Chunker and tag-pattern failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ValueError: chunk structures must contain tagged tokens or trees` | `RegexpParser` received raw words or invalid token objects. | Pass POS-tagged tuples `(word, tag)` or a valid chunk `Tree`. |
| No chunks are found | Tag pattern does not match POS tags. | Print the input tags and convert simple patterns with `tag_pattern2re_pattern` for debugging. |
| `ValueError: Bad tag pattern` | Illegal braces/angle brackets or malformed tag pattern. | Use valid forms such as `<DT>?<JJ>*<NN.*>+`; keep chunk braces outside tag patterns unless using quantifiers like `<N.*>{4,}`. |
| `ValueError: Illegal chunk pattern` from `RegexpParser` | Rule line combines unsupported forms or has bad context syntax. | Use one rule per line: `{...}`, `}...{`, `...}{...`, `...{}...`, or `left{chunk}right`. |
| `tree2conlltags` raises "too deeply nested" | CoNLL IOB conversion supports shallow chunk trees only. | Flatten or choose a single chunk layer before converting. |
| A user-supplied chunk rule is suspiciously large or adversarial | Chunk tag-pattern parsing is public input surface. Current code has ReDoS guards, but user patterns can still be expensive semantically. | Bound user pattern length, loop count, and input sentence length in applications; run crafted patterns in a time-limited test if accepting untrusted rules. |
| `ne_chunk` raises `LookupError` | Named-entity chunker model/words data is missing. | Route targeted resource downloads/checks to data/downloader. |

Security evidence: focused tests cover chunk tag-pattern ReDoS (`test_chunk_redos_security.py`) while preserving valid quantifiers (`test_chunk.py`).

## Tree parsing, editing, and rendering failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Tree.fromstring` raises `TypeError: brackets must be a length-2 string` | Invalid bracket delimiter. | Pass a two-character string such as `'()'`, `'[]'`, or `'<>'`. Whitespace brackets are not allowed. |
| `Tree.fromstring` raises a `ValueError` with a caret | Malformed bracketed tree string. | Use the caret index in the error message; ensure exactly one complete top-level tree. |
| `Tree.productions()` raises `TypeError` | Tree labels are not strings. | Convert labels to strings or avoid production extraction for non-string labels. |
| Parent pointers are wrong or `ParentedTree` insertion raises `TypeError` | Mixed `Tree`, `ParentedTree`, or `MultiParentedTree` instances. | Convert the entire tree with `ParentedTree.convert(tree)` before parent-pointer workflows. |
| Tree drawing/SVG fails | GUI, Tkinter, Graphviz, or `svgling` dependency is unavailable. | Use `pformat`, `pretty_print(stream=...)`, or LaTeX string output unless rendering dependencies are verified. |

## Dependency graph and dependency parser issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ValueError: Number of tab-delimited fields ... not supported` | Dependency input has a nonstandard column count. | Provide a `cell_extractor`, normalize to 3/4/7/10 columns, or set the intended `cell_separator`. |
| Graph root is missing or warning says no node depends on root | No token has head `0` with the top relation label. | Verify head indices and `top_relation_label` (`ROOT`, `TOP`, `null`, etc.). |
| `DependencyEvaluator` raises sentence length or word mismatch errors | Parsed and gold graphs do not have identical token sequences. | Compare `nodes` by address and words before evaluating LAS/UAS. |
| LAS/UAS looks lower than expected | Punctuation is ignored; relation labels affect LAS but not UAS. | Inspect triples and heads directly. |
| `DependencyGraph.load(path)` raises `PermissionError` | NLTK path security rejected an out-of-root file. | Move the file under an allowed data root or adjust the caller's pathsec policy intentionally; do not bypass with arbitrary `open`. |
| `_repr_svg_()` or `to_dot` rendering fails | Graphviz `dot` or notebook rendering dependencies are missing. | Use `tree()`, `triples()`, or `to_conll()` for base diagnostics; install/configure Graphviz only if rendering is required. |
| Projective dependency parsing rejects a long token list | `ProjectiveDependencyParser.MAX_TOKENS` guards an O(n²)/O(n³) algorithm. | Reduce input length or raise the cap only with explicit resource budget. |

Security evidence: `DependencyGraph.load` is covered by pathsec sandbox tests, and dependency graph cycle detection/projective parsing include resource-bound fixes.

## Logic, model evaluation, and DRT issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| `LogicalExpressionException` on variable/predicate names | NLTK logic distinguishes individual variables from constants/predicates. | Check illegal abstractions/quantification such as `\walk...` or `all walk...`; use legal variable names (`x`, `y`, etc.) and constants in argument position. |
| Deep expression raises a clean parse error | `LogicParser.MAX_PARSE_DEPTH` guard fired. | Reduce nesting or adjust the cap only for trusted formulas with budget. |
| `Model.evaluate(...)` returns `'Undefined'` | A constant/predicate/variable has no valuation or assignment. | Inspect `val.symbols`, `val.domain`, and assignment bindings. Treat `'Undefined'` as neither `False` nor `True`. |
| `Model(...)` raises valuation-domain error | Model domain does not contain all individuals used by the valuation. | Use `dom = val.domain` or a superset. |
| `model.satisfy(...)` raises a resource-bound `Error` | Nested quantifier/lambda evaluation would exceed `Model.MAX_SATISFY_OPERATIONS`. | Shrink the domain or formula; avoid evaluating adversarial formulas directly. |
| Typed logic gives unexpected `?` or type errors | Signature missing or inconsistent. | Use `Expression.fromstring(expr, type_check=True, signature={...})` and inspect `.type`. |
| `DrtExpression.fol()` fails on an empty DRS | A DRS with no conditions cannot be converted to FOL. | Ensure the DRS has conditions or handle empty DRS as a special case. |

Security evidence: logic parser depth, valuation parsing ReDoS, and model satisfaction cost are guarded by focused security tests.

## Inference/prover issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| In-process resolution/tableau search takes too long | First-order proof search can be non-terminating or explosive. | Keep formulas small; rely on `ResolutionProver.TIMEOUT`, `TableauProver.TIMEOUT`, and `TableauProver.MAX_TABLEAU_DEPTH`; do not set timeout to `0` for untrusted formulas. |
| `Prover9`/`Mace` cannot find a binary | External prover/model-builder binaries are not installed or not discoverable. | Configure binary locations/environment variables or avoid external wrappers. |
| `expr.equiv(other)` unexpectedly tries external Prover9 | Default equivalence uses `Prover9()` if no prover is supplied. | Pass an explicit in-process prover or avoid equivalence proof unless Prover9 is configured. |
| Mace/Prover9 exits with limit/fatal error | Binary timed out, hit memory/model-size limits, or rejected syntax. | Inspect generated formulas, reduce assumptions, and set timeout/end-size consciously. |

Security evidence: in-process `ResolutionProver`/`TableauProver` have default wall-clock/depth bounds; Prover9 has a timeout parameter.

## Optional external parser wrappers

| Wrapper symptom | Likely cause | Fix |
| --- | --- | --- |
| CoreNLP server fails to start or connect | Missing JAR/model JAR, Java options, port conflict, or server readiness timeout. | Verify JAR paths/env vars, Java, port, and use context manager lifecycle to stop failed servers. |
| Stanford parser classpath errors | Parser/model JARs not found. | Set `STANFORD_PARSER`, `STANFORD_MODELS`, or explicit path arguments. |
| MaltParser resolves an unexpected directory or fails assertions | Missing `maltparser-*.jar` or dependencies. | Use an absolute parser directory or configured `MALT_PARSER`; verify required JAR basenames. |
| BLLIP import or parse fails | `bllipparser` or model files missing; non-ASCII tokens; not thread-safe. | Install/configure `bllipparser`, keep ASCII/token constraints explicit, and avoid multiple parser objects in one process. |
| TransitionParser model loading fails with pickle errors | Model is incompatible, corrupt, or blocked by the allowlisted unpickler. | Re-train with the active environment or use a trusted model; never switch to unrestricted pickle loading for untrusted files. |

## Smoke script failures

Run:

```bash
python /path/to/grammar_parse_smoke.py --help
python /path/to/grammar_parse_smoke.py --json
```

Interpretation:

- `--help` should work even if NLTK is not importable, because it only uses `argparse`.
- A runtime import failure means the active environment does not have NLTK on `sys.path`.
- Any assertion failure is an environment/package regression because the script uses only in-memory grammars, strings, and tiny objects; it performs no downloads and invokes no external binaries.
