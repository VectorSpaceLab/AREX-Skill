# testlib.h Usage Guide

## Purpose

Use this reference to author small, self-contained C++ programs around the
bundled `testlib.h`. The primary workflow is an offline checker with an
optional validator. Generator and interactor coverage is included because they
use the same header, but they do not change the minimal checker command line in
the root skill.

The API facts and examples here were distilled from testlib 0.9.45, its bundled
header, and the repository's C++ examples.

## Header Setup

Testlib is a single header. Copy the bundled header from this skill's
`scripts/` directory into the working directory and include it first:

```cpp
#include "testlib.h"

#include <vector>
```

No library link flag is required. Compile each checker, validator, generator,
or interactor as its own executable. The `-I.` flag works when `testlib.h` is
in the current directory; otherwise point `-I` at the directory that contains
the bundled header.

Including testlib first also lets it replace compiler-specific random helpers.
For generator code, use `rnd` and testlib's `shuffle` instead of `rand`,
`srand`, or `random_shuffle`.

## Checker

### Minimal checker template

This checker compares one signed 64-bit integer from the standard answer with
one integer from the contestant output:

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    setName("compare one signed 64-bit integer");
    registerTestlibCmd(argc, argv);

    long long expected = ans.readLong();
    long long actual = ouf.readLong();

    if (actual != expected) {
        quitf(_wa, "expected %lld, found %lld", expected, actual);
    }

    quitf(_ok, "answer is %lld", actual);
}
```

Compile it with the command in the root skill and run it with three file paths
in this exact semantic order: input, contestant output, standard answer.

### Streams

| Stream | Source | Typical use |
| --- | --- | --- |
| `inf` | First checker file argument | Read problem input, constraints, dimensions, or instance data |
| `ouf` | Second checker file argument | Parse and validate contestant output |
| `ans` | Third checker file argument | Read the jury answer, reference objective, or expected tokens |

For non-unique or constructive answers, validate `ouf` against the instance in
`inf`. Use `ans` only for data that is genuinely needed, such as an optimal
objective value. Do not reject a valid construction merely because its text is
different from the jury construction.

### Common readers

| Need | Typical call |
| --- | --- |
| 32-bit integer | `readInt()` or `readInt(lo, hi, "name")` |
| 64-bit integer | `readLong()` or `readLong(lo, hi, "name")` |
| Floating-point value | `readDouble()` or `readDouble(lo, hi, "name")` |
| Whitespace-delimited token | `readToken()` |
| Token matching a pattern | `readToken("[a-z]+", "word")` |
| Whole line | `readLine()` or `readString()` |
| Several bounded values | `readInts`, `readLongs`, or `readDoubles` |
| End probe ignoring trailing blanks | `seekEof()` |

Bound contestant values while reading when the range is part of the output
contract. Testlib turns malformed or out-of-range judged output into an
appropriate non-accepted result. A successful `quitf(_ok, ...)` also checks
for extra non-whitespace data remaining in `ouf`.

`seekEof()` is a Boolean probe. Calling it without checking the returned value
does not reject trailing output. Test the result explicitly when probing early,
or rely on the successful `_ok` termination check after consuming all permitted
output.

### Verdicts

| Result | Meaning | Default local exit code |
| --- | --- | --- |
| `_ok` | Contestant output is accepted | `0` |
| `_wa` | Output is well-formed but semantically wrong | `1` |
| `_pe` | Contestant output format is invalid | `2` |
| `_fail` | Checker, input, or jury-answer failure | `3` |
| `quitp(points, ...)` | Points or partial score | `7` |

These codes are defaults. Judge-specific compile-time macros can remap them,
so portable orchestration should distinguish accepted from non-accepted and
preserve the diagnostic rather than assuming every platform uses the same
number.

Use `_fail`, not `_wa`, when the official answer is malformed or an internal
checker invariant is false. This prevents a judge-data problem from being
reported as a contestant mistake.

### Checker design sequence

1. Call `setName` and `registerTestlibCmd` near the start of `main`.
2. Read the instance data required from `inf`.
3. Read and sanity-check jury data from `ans` if the checker needs it.
4. Parse the contestant result from `ouf` with explicit types and bounds.
5. Validate syntax, feasibility, and objective value in that order.
6. Call `quitf` with a short diagnostic that includes the first useful
   mismatch or violated condition.
7. Call `_ok` only when the entire required output has been consumed and all
   semantic checks pass.

For multi-case output, call `setTestCase(i)` while checking each case so error
messages identify the failing case.

## Validator

### Strict validator template

This template accepts an integer `n`, then exactly `n` space-separated values
on the next line, and applies an example semantic rule that their sum must be
non-negative:

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int n = inf.readInt(1, 200000, "n");
    inf.readEoln();

    long long sum = 0;
    for (int i = 0; i < n; ++i) {
        if (i > 0) {
            inf.readSpace();
        }
        sum += inf.readLong(-1000000000LL, 1000000000LL, "a_i");
    }
    inf.readEoln();
    inf.readEof();

    ensuref(sum >= 0, "sum must be non-negative");
}
```

`registerValidation` maps standard input to strict `inf`. In strict mode,
format is part of validity: read spaces, line endings, and EOF explicitly.
Always finish a complete validator with `inf.readEof()`; returning without it
is treated as an incomplete validator.

Use names such as `"n"` and `"a_i"` on bounded reads. They improve error
messages and validator metadata. Use `ensuref(condition, ...)` for constraints
that span multiple values, such as uniqueness, graph simplicity,
connectivity, or a total-sum limit.

The root skill shows the compile command and the stdin invocation. Run the
validator before executing the solution; stop the case immediately when the
validator returns nonzero.

## Generator

### Minimal deterministic generator

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    int n = opt<int>(1);
    println(n);
    println(rnd.perm(n, 1));
}
```

Compile and run it as follows after placing `testlib.h` beside the source:

```bash
g++ -std=c++17 -O2 -I. generator.cpp -o generator
./generator 10 > case.in
```

`registerGen(argc, argv, 1)` seeds `rnd` from the command line. Repeating the
same executable with the same arguments reproduces the same test. Change the
arguments to change the seed.

Useful primitives include:

- `rnd.next(lo, hi)` for a uniform inclusive integer range.
- `rnd.next("[a-z]{1,20}")` for a token generated from a testlib pattern.
- `rnd.wnext(lo, hi, bias)` for a biased distribution.
- `rnd.perm(n, first)` for a permutation.
- `rnd.distinct(count, lo, hi)` for distinct values.
- `rnd.partition(count, sum, minPart)` for an integer partition.
- `opt<T>(1)` for a positional argument and `opt<T>("n")` for `-n` or
  `--n` style options.
- `println` for stable whitespace-separated lines; use standard C++ output when
  custom no-newline formatting is required.

After generation, validate every intended-valid produced file with the problem
validator. If a routed randomized, batch, or large-data campaign has no
validator yet, implement the independent validator before relying on the
generated cases.

### Parameterized campaigns and large cases

Treat a generator as executable provenance for a coverage family. For randomized, batch, or large cases, expose the family and relevant structural parameters explicitly rather than hand-editing the emitted file:

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    std::string family = opt<std::string>("family");
    int n = opt<int>("n");
    int bias = opt<int>("bias");
    long long seedTag = opt<long long>("seed");

    // The complete command line, including seedTag, determines rnd's seed.
    // Implement each problem-specific family and print exactly one valid case.
    ensuref(n > 0, "n must be positive");
    (void)family;
    (void)bias;
    (void)seedTag;
    println(n);
}
```

A case can then be reproduced from its full command:

```bash
./generator --family=random --n=200000 --bias=2 --seed=104729 > case.in
./validator < case.in || exit 1
```

Implement the actual family semantics in C++; the placeholder above only demonstrates parameter and seed provenance. Use a small coded driver to enumerate a batch parameter matrix, invoke the generator once per case, validate each emitted file, and record a manifest. Keep at least the case id, family, full command, generator hash/version, input hash, and validator result. Preserve failing commands and seeds with the corresponding input, solver output, evaluator diagnostic, and transcript. Do not use manually assembled maximum-size files or unlabeled random dumps as reproducible test sources.

## Interactor

An interactor has different process wiring from an offline checker:

```cpp
#include "testlib.h"

#include <iostream>

int main(int argc, char* argv[]) {
    registerInteraction(argc, argv);

    long long a = inf.readLong();
    long long b = inf.readLong();
    std::cout << a << ' ' << b << std::endl;

    long long reply = ouf.readLong();
    tout << reply << std::endl;

    if (reply != a + b) {
        quitf(_wa, "expected %lld, found %lld", a + b, reply);
    }
    quitf(_ok, "interaction completed");
}
```

The interactor reads test data from `inf`, reads the participant process from
`ouf` (the interactor's stdin), writes protocol messages to stdout, and writes
a transcript or checker input to `tout`. Every query must be flushed. A judge
or dedicated interactive runner must connect the two processes; the root
skill's `solution < case.in > case.out` command is not an interactive runner.

## Minimal File Layout

```
work/
  testlib.h
  solution.cpp
  checker.cpp
  validator.cpp       # optional
  generator.cpp       # optional
  case.in
  case.ans
  case.out             # produced by the solution
```

Keep the header copied with the judging sources so the compile commands are
portable and do not depend on the original testlib repository checkout.
