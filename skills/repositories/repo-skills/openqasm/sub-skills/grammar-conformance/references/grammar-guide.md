# OpenQASM 3 grammar guide

This guide distills the ANTLR reference grammar at the verified OpenQASM
baseline. Use it to navigate a syntax question; do not treat it as a complete
replacement for the normative language specification. The grammar defines
syntactic acceptance and deliberately leaves much semantic analysis to later
compiler stages.

## 1. Lexer shape and token priority

The lexer has a default mode plus six purpose-built modes: version identifiers,
arbitrary strings, end-of-line pragmas/annotations, calibration preludes for
`cal` and `defcal`, and opaque calibration blocks. Whitespace (`space` and tab),
line breaks, and comments are handled before parsing:

- `Whitespace` and `Newline` are skipped.
- `LineComment` starts with `//`, consumes through but not including a line
  ending, and is sent to the hidden channel.
- `BlockComment` starts with `/*`, uses a non-greedy `.*?` body, ends at `*/`,
  and is sent to the hidden channel. It may span lines.
- The public Python API can recover hidden comments with `get_comments(source)`;
  comments do not appear as parser statements or ordinary AST nodes.

Keywords and fixed symbols have uppercase rule names (`INCLUDE`, `QUBIT`,
`DOUBLE_ASTERISK`). Tokens that carry source text use PascalCase names such as
`Identifier`, `FloatLiteral`, and `StringLiteral`. A useful debugging habit is
to ask whether the first unexpected character is lexable before asking which
parser rule should consume it.

Important default-mode token families include:

- identifiers: an underscore, ASCII letter, or valid Unicode letter-like
  character first, followed by zero or more such characters or digits;
- hardware qubits: `$` followed by one or more decimal digits, such as `$0`;
- integers: binary (`0b`/`0B`), octal (`0o`), decimal, and hexadecimal
  (`0x`/`0X`), with underscores only between digits;
- floats: decimal exponent forms, leading-dot forms such as `.5`, and decimal
  dot forms such as `1.`, optionally with an exponent;
- imaginary literals: an integer or float followed by optional horizontal
  space and `im`;
- timing literals: an integer or float followed by optional horizontal space
  and one of `dt`, `ns`, `us`, `µs`, `ms`, or `s`;
- bitstring literals: a non-empty double-quoted sequence of `0` and `1` with
  optional internal underscores.

A leading minus is the `MINUS` operator, not part of a numeric literal. This
matters when reducing a negative-expression failure: first inspect the unary
expression rule, then the numeric token.

The lexer has distinct tokens for one- and two-character operators. The
multi-character rules include `->`, `++`, `**`, `||`, `&&`, equality operators,
compound assignments, comparisons, and bitshifts. Do not infer that every
punctuation character is legal in an identifier or ordinary expression merely
because a pragma or calibration body can carry it as opaque text.

## 2. Mode transitions

### Version mode

`OPENQASM` pushes `VERSION_IDENTIFIER`. That mode skips whitespace and accepts
one `VersionSpecifier` consisting of decimal digits with an optional
`.` followed by decimal digits, then returns to the default mode. Consequently,
`OPENQASM 3;` and `OPENQASM 3.0;` are tokenizable, while `OPENQASM 3.1.2;`
may be detected by `parse_version` but is rejected by the Python parser's
version policy before ordinary parsing completes.

The first header is parsed by:

```text
program: version? statementOrScope* EOF;
version: OPENQASM VersionSpecifier SEMICOLON;
```

`parse_version` is an inexpensive preliminary scanner, not a full grammar
check. It ignores leading comments/blank material, only recognizes an
`OPENQASM` candidate as the first non-comment construct, and can return a
version for input that is later rejected.

### Arbitrary-string mode

`include` and `defcalgrammar` push `ARBITRARY_STRING`. The mode accepts a
single non-empty quoted string using either double or single quotes, excluding
its quote, carriage return, tab, and newline from the body, then returns to the
default mode. The parser rules require the string and a semicolon:

```text
includeStatement: INCLUDE StringLiteral SEMICOLON;
calibrationGrammarStatement: DEFCALGRAMMAR StringLiteral SEMICOLON;
```

The grammar does not resolve an include or interpret a calibration grammar
name.

### Line mode for pragmas and annotations

`PRAGMA` accepts either `pragma` or `#pragma` and pushes `EAT_TO_LINE_END`.
`AnnotationKeyword` accepts `@name` or a dotted name such as
`@vendor.feature`, then also pushes that mode. The mode skips initial spaces,
consumes a non-empty remainder as `RemainingLineContent`, and pops on a line
ending. The remainder is intentionally not tokenized as OpenQASM.

The parser rules are:

```text
annotation: AnnotationKeyword RemainingLineContent?;
pragma: PRAGMA RemainingLineContent;
```

A statement may have zero or more annotations before it. The remainder after an
annotation belongs to that annotation, so a second `@` on the same line is
ordinary annotation command text rather than a second annotation. Put separate
annotations on separate lines. A pragma is a statement in the grammar, but the
Python AST visitor additionally requires pragmas to be in global scope.

### Calibration prelude and block modes

`cal` changes to `CAL_PRELUDE`; `defcal` changes to `DEFCAL_PRELUDE`. These
modes skip whitespace/comments and look for the first opening brace. The
`defcal` prelude duplicates enough type, punctuation, literal, operation, and
name tokens to parse its argument and operand prelude without making the lexer
know the host pulse language. The opening brace is retyped as `LBRACE` and
enters `CAL_BLOCK`.

`CAL_BLOCK` treats everything except braces as opaque payload and recognizes
nested braces recursively:

```text
fragment NestedCalibrationBlock: LBRACE (NestedCalibrationBlock | ~[{}])* RBRACE;
CalibrationBlock: (NestedCalibrationBlock | ~[{}])+;
CAL_BLOCK_RBRACE: RBRACE -> type(RBRACE), mode(DEFAULT_MODE);
```

The parser then accepts `cal { CalibrationBlock? }` and the corresponding
`defcal` form. The payload is not OpenQASM expression syntax and is not
validated as OpenPulse or another calibration language. Because the lexer has
no knowledge of that inner language, a brace-looking character in an inner
comment or string can still affect balancing; test such inputs explicitly.

## 3. Program, statements, and scopes

At the top level, `program` accepts at most one optional version statement,
then any number of `statementOrScope` items, and EOF. A `statementOrScope` is
either a `statement` or a brace-delimited `scope`:

```text
scope: LBRACE statementOrScope* RBRACE;
```

The grammar's `statement` alternatives cover:

- directives: pragma, annotation-prefixed statements, include, and
  `defcalgrammar`;
- control flow: `break`, `continue`, `if`/`else`, `for`, `while`, `switch`,
  `case`, `default`, `return`, and `end`;
- quantum directives: barrier, box, delay, nop, gate calls, measurement
  arrows, and reset;
- declarations: classical, constant, input/output, old-style `creg`/`qreg`,
  and `qubit`;
- definitions: `def`, `extern`, `gate`, `cal`, and `defcal`;
- expressions and assignments.

A bare brace block is syntactically valid where `statementOrScope` is allowed;
whether a construct is allowed in a particular enclosing scope is a separate
parser-context or semantic concern. In particular, the grammar file comments
that it does not enforce all invalid scopes.

The most useful parser-rule entry points when explaining an error are
`program`, `statement`, `scope`, the named `*Statement` rule, `expression`,
`indexOperator`, and the relevant type/list rule. For a reduced fixture, name
the smallest rule that should accept it rather than saying only “the parser
likes it.”

## 4. Expressions and precedence

`expression` uses ANTLR direct left recursion. The alternatives are ordered from
most tightly binding to least tightly binding, and the order determines the
precedence. The effective table is:

| Binding strength | Form | Associativity |
|---|---|---|
| primary/parenthesized and indexing | `(expression)`, `expression[index]` | indexing chains leftward |
| power | `expression ** expression` | right |
| unary | `~`, `!`, `-` followed by expression | prefix |
| multiplicative | `*`, `/`, `%` | left |
| additive | `+`, `-` | left |
| bitshift | `<<`, `>>` | left |
| comparison | `<`, `>`, `<=`, `>=` | left by grammar shape |
| equality | `==`, `!=` | left by grammar shape |
| bitwise and | `&` | left |
| bitwise xor | `^` | left |
| bitwise or | `\|` | left |
| logical and | `&&` | left |
| logical or | `\|\|` | left |

The primary alternatives also include casts (`scalarType` or `arrayType`
followed by a parenthesized expression), `durationof(scope)`, function calls,
and literal/identifier forms. Special forms such as measurement and quantum
calls are deliberately separate from general expressions and cannot simply be
inserted into arbitrary arithmetic.

Power is explicitly marked right-associative: `2 ** 3 ** 2` groups as
`2 ** (3 ** 2)`. Power binds more tightly than unary in the generated parser,
so inspect the tree rather than applying a host-language intuition to
`-2 ** 2`. Parentheses are the conformance-safe way to make the intended group
visible.

Indexing has its own `indexOperator` and can contain a set, an expression, a
range, or a comma-separated mixture of expressions/ranges with a trailing
comma. A range has optional endpoints and one or two colons, for example
`[:]`, `[start:end]`, or `[start:step:end]`. Set expressions require at least
one expression, unlike array literals which may be empty.

## 5. Declarations and type shapes

The grammar distinguishes `scalarType`, `arrayType`, `arrayReferenceType`, and
`qubitType`. Scalar forms include `bit`, `int`, `uint`, `float`, `angle`,
`bool`, `duration`, `stretch`, and `complex` with an optional nested float
component. A `designator` is exactly one bracketed expression:

```text
designator: LBRACKET expression RBRACKET;
```

Therefore `int[8] x;` is one width designator, while `int[8, 16] x;` is not a
valid scalar declaration grammar. `array` takes a scalar type and an
expression list of dimensions, for example `array[int[8], 4, 3] a;`.

Argument rules distinguish classical, quantum, old-style register, and array
reference arguments. `gate` definitions use identifier lists for parameters
and qubits. `extern` arguments may use scalar, array-reference, or old-style
classical register forms. `defcal` has its own argument and operand rules so
that a definition such as `defcal rz(angle[20] theta) q { ... }` can be
recognized while leaving its body opaque.

## 6. Lists, optional items, and trailing commas

The grammar consistently uses the following pattern for non-empty lists:

```text
item (COMMA item)* COMMA?
```

It appears in argument definitions, defcal arguments and operands, expression
lists, identifiers, gate operands, extern arguments, and similar constructs.
Thus these forms have an optional final comma:

```text
extern f(int, int,);
gate g a, b { x a; }
nop q0, q1,;
foo(1, 2,);
```

An optional list at a caller can be empty, such as the argument list in
`foo()`. The trailing-comma suffix does **not** permit an empty first or middle
item: `foo(,);` is rejected. A set expression is non-empty but permits a final
comma: `{1, 2,}`. An array literal may be empty and may also have a trailing
comma: `{}` and `{1, 2,}`. Use paired positive/negative fixtures whenever a
consumer's pretty-printer or formatter changes commas.

## 7. How to read an acceptance dispute

1. Tokenize the smallest failing fragment, paying special attention to mode
   transitions and multi-character operators.
2. Locate the parser rule named by the nearest construct (`includeStatement`,
   `expressionList`, `gateOperandList`, and so on).
3. Check whether the ambiguity is resolved by alternative order, direct
   left-recursion precedence, or a special-case rule such as `gphase`.
4. Check whether the public Python visitor adds a contextual rejection after
   ANTLR has recognized the rule.
5. Only then route meaning, types, lowering, or execution questions to the
   appropriate sibling skill.
