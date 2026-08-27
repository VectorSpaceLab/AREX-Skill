# Troubleshooting

## Header Not Found

Symptom: compilation reports `fatal error: testlib.h: No such file or directory`.

Copy the bundled `scripts/testlib.h` from this skill into the working directory
and compile with `-I.`, or pass `-I` the directory that actually contains the
header. Testlib is header-only; no library link flag is needed.

## Checker Rejects Its Command Line

Symptom: the checker says it must be run with input, output, and answer files.

Use exactly:

```
./checker case.in case.out case.ans
```

The second path is contestant output and the third is the standard answer. If
the checker ignores `ans`, still provide an existing placeholder file.

## Checker Gives Surprising Results

- Confirm that `ouf` is read as contestant output and `ans` as jury output.
- A default exit code of `1` is wrong answer, `2` is presentation/format error,
  and `3` is a checker or judge-data failure.
- `quitf(_ok, ...)` checks for extra non-whitespace contestant output. Consume
  all permitted output before accepting.
- Preserve stderr: it contains the checker verdict and diagnostic.
- Run `echo $?` immediately after the checker, before any other command changes
  the shell status.

## Validator Rejects Apparently Valid Input

Validators are strict. `readSpace()` expects the required separator,
`readEoln()` expects the line ending at that point, and `readEof()` expects no
remaining bytes. Compare the file's exact whitespace with the validator's
grammar. Do not replace strict reads with loose parsing merely to accept a
malformed generated test.

## Solution Timeout or Crash Is Confused with Checker Status

GNU `timeout` commonly returns `124` when the time limit expires. That status
belongs to the solution command, while the later status belongs to the
checker. In a more defensive shell loop, capture each status immediately and
report whether the failure came from solution execution or output checking.

## Generator Is Not Reproducible

- Use `registerGen(argc, argv, 1)`.
- Use `rnd` and testlib's `shuffle`, not standard `rand`, `srand`, or
  `random_shuffle`.
- Keep the full command line and bundled header version unchanged.
- Remember that changing any generator argument changes the seed.

## Interactor Hangs

- Flush every query with `std::endl` or `std::flush`.
- Confirm that a bidirectional runner connects solution stdout to interactor
  stdin and interactor stdout to solution stdin.
- Do not run an interactive solution with the ordinary redirected offline
  command.
- Treat unexpected EOF as a protocol or process failure and include the last
  completed protocol step in the diagnostic.

## Partial Scoring Looks Like Failure

`quitp(points, ...)` uses the points result and normally exits with code `7`,
not `0`. A simple zero/nonzero shell policy is appropriate only for accepted
versus non-accepted checking. A scored task needs an orchestrator that parses
and aggregates the points verdict.
