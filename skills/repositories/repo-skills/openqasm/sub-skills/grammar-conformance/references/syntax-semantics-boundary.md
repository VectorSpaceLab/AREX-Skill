# Syntax–semantics boundary

Use this boundary before reporting why an OpenQASM input succeeds or fails. The
ANTLR grammar, the public Python AST parser, a semantic compiler, an include
resolver, and a provider backend answer different questions.

## Classification table

| Layer | Question answered | Typical evidence | Concrete example | What success means | Owner / next step |
|---|---|---|---|---|---|
| **Lexical** | Can the character stream be divided into reference-grammar tokens in the active lexer mode? | lexer token stream or a token-recognition diagnostic | `barrier $a;` fails because hardware qubits require `$` plus decimal digits; `include "";` fails because arbitrary strings are non-empty | Only that tokenization succeeded | This sub-skill; inspect mode, token spelling, and first bad character |
| **Grammar** | Can those tokens be consumed by `program` and its parser rules through EOF? | exact ANTLR parse tree, rule path, or strict parse rejection | `while true {}` lacks required parentheses; `f(,);` has an empty expression-list item; `OPENQASM 3 3;` does not match `version` | Only that a reference-grammar derivation exists | This sub-skill; minimize source and name the accepting/failing rule |
| **AST-parser contextual** | After grammar recognition, does the Python AST visitor accept selected scope and shape constraints while constructing `Program`? | `QASM3ParsingError` raised from a source context, usually with line/column | `break;` outside a loop, nested `pragma`, `return;` outside a subroutine, a second `default`, `gphase()` with wrong arity, or `uint[0] x;` | A reference AST could be constructed under the visitor's implemented checks | This sub-skill classifies the failure; AST internals route to [python-ast-tooling](../../python-ast-tooling/SKILL.md) |
| **Semantic / type / compiler** | Are names declared, scopes legal under the full language rules, types compatible, constants valid, operations well formed, and target-independent semantics satisfied? | specification-aware semantic analysis, symbol tables, type checker, compiler diagnostics | `OPENQASM 3.1; x q;` parses even though a compiler still must resolve `x` and `q`; duplicate names and operand/type compatibility are not proved by parse success | The program passed the particular compiler analyses that were actually run | Meaning and source-design questions route to [language-authoring](../../language-authoring/SKILL.md); full semantic compiler implementation is out of scope |
| **Include resolution** | Can an include name be located, loaded under policy, version-checked, and integrated without cycles/conflicts? | resolver trace, include search policy, loaded-unit diagnostics | `include "stdgates.inc";` parses without opening any file; a missing include is not a grammar error | Referenced units were resolved under one tool's policy | Outside this sub-skill; report parser acceptance separately from resolver outcome |
| **Provider execution** | Can a simulator/QPU/provider compile, map, schedule, and run the program with supported capabilities? | provider/compiler job result, backend diagnostics, execution result | A syntactically valid calibration body, gate set, dynamic-control construct, or timing feature may be unsupported by a provider | Only that the named provider accepted or ran this program under its configuration | Out of scope; never infer from parser acceptance |

## Decision procedure

1. **Was there a token-recognition error?** Classify lexical. Record line,
   zero-based column, active mode if known, and the smallest unrecognized text.
2. **Did ANTLR fail to derive `program` through EOF?** Classify grammar. Name the
   nearest rule and expected token/delimiter. A generic public-parser
   `parse failed` still belongs here if the failure occurred before AST visits.
3. **Did the message describe scope, built-in arity, array/type shape, or another
   explicit visitor condition?** Classify AST-parser contextual, even if the
   underlying language concept is semantic. This label describes where the
   reference implementation rejected it.
4. **Did strict `parse` return `Program`?** Syntax and implemented context checks
   passed. Stop before claiming symbol/type/compiler validity.
5. **Is the dispute about a name, type, value, or normative meaning?** Route to
   language semantics or a compiler validation stage.
6. **Does it require opening an include or contacting/running a provider?**
   Record a separate resolver or provider result; those operations are not
   performed by this skill's helper.

## What the grammar deliberately permits

The parser grammar explicitly states that it defines parsing and leaves
semantic analysis and rejection of invalid scopes to compiler implementations.
Its general `program` and `scope` rules are consequently broader than a full
semantic validator. Examples of syntax accepted for later interpretation
include:

- identifier-based gate/function/quantum-call forms whose declarations are not
  resolved by parsing;
- expressions whose operand types are not inferred by the grammar;
- include and calibration-grammar string names that are never opened;
- opaque `cal`/`defcal` body text whose only host-level condition is balanced
  braces;
- declarations and calls for which duplicate-name, width, value, or target
  constraints may require later analysis.

Do not “fix” these by adding negative grammar fixtures unless the grammar or an
explicit parser-context contract actually rejects them.

## What the Python AST parser checks contextually

The public parser is more than an ANTLR accept/reject wrapper: it walks the
parse tree and raises `QASM3ParsingError` for a bounded set of context
conditions. At this baseline those include, among others:

- `break`/`continue` only inside a loop and `return` only inside a subroutine;
- global-only placement for pragmas, includes, `defcalgrammar`, input/output,
  qubit declarations, arrays, externs, gates, and subroutine definitions;
- restrictions on classical assignment/declaration and non-unitary
  measure/reset operations inside gate definitions;
- one `default` and no `case` after `default` in a switch;
- exact accepted arity for parser-recognized `gphase` and `sizeof` built-ins;
- positive old-style register and `int`/`uint`/`angle` widths for simple literal
  cases;
- non-negative simple array dimensions, float components for `complex`, and
  accepted scalar categories for arrays.

This is not a complete semantic checker. The checks are best described as
“AST-parser contextual checks” in conformance reports because they happen after
ANTLR recognition while constructing the reference AST. A different parser may
split the same normative condition into a later semantic pass.

## Version results are three observations

Keep these values distinct:

1. **Detected version:** `parse_version(source)` returns a tuple or `None`. This
   preliminary scanner can detect unsupported or overlong versions and can
   return a value for an otherwise invalid program.
2. **Header version:** the detected tuple rendered as dotted text is evidence
   of a candidate first header, not full grammar acceptance.
3. **AST version:** `Program.version` after strict parse. It is the source header
   text represented by the AST (`"3"`, `"3.0"`, or `"3.1"`) or `None` for a
   headerless accepted input.

At this baseline, normal parsing supports `3`, `3.0`, and `3.1` under the
minimum/maximum policy and declares specification support for `3.0` and `3.1`.
`ignore_version=True` can attempt another reported version, but its success is
not evidence that the program is valid for that version.

## Parse-success statement template

Use wording like:

> Strict `openqasm3` parsing accepted the source and constructed a `Program`
> with AST version `3.1`. This establishes parser acceptance at the verified
> grammar/parser baseline only. Includes were not resolved, full semantic/type
> checks were not run, and no compiler or provider execution was performed.

For a contextual rejection:

> ANTLR-recognizable source was rejected during reference AST construction at
> line 1, column 0 because `break` occurred outside a loop. This is an
> AST-parser contextual failure, not a lexical failure and not evidence from a
> full semantic compiler.

For a lexical rejection:

> Strict parsing rejected the source at line 1, column 8 with a token
> recognition error in arbitrary-string mode. No grammar, semantic, include, or
> execution acceptance should be inferred.

## Borderline cases

### Headerless input

The Python parser accepts a missing header and sets `Program.version` to
`None`. Whether authored source should include a header is a normative
source-design question for the language-authoring sibling, and whether a
provider requires one is a provider question.

### Comments

Ordinary comments are lexed to a hidden channel and can be recovered with
`get_comments`. They are not preserved as ordinary AST statements. Inside a
calibration body, apparent inner-language comments are opaque calibration text;
the host lexer does not apply its normal comment rules there.

### Pragmas and annotations

Their line remainder is opaque to ordinary OpenQASM tokenization. An arbitrary
pragma command can therefore parse even if the same punctuation would be an
ordinary lexical error. The command's meaning and vendor support are later
layers.

### Calibration blocks

Balanced braces establish only host-grammar acceptance. An inner language may
reject the body; a provider may reject the calibration grammar or target; none
of that changes the host parser result.

### Trailing commas

Trailing commas are explicitly grammar-accepted in named list rules. A
formatter removing one can be syntax-preserving, but only AST/tree comparison
can establish whether it preserved the intended list. Empty or missing middle
items remain grammar errors.
