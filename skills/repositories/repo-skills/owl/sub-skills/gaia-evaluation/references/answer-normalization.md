# Answer Normalization Examples

These examples describe the implementation's comparison semantics and are
useful when designing fixtures. They are not a replacement for checking the
current source when a benchmark version changes.

| Ground truth | Model answer | Comparison path | Expected |
|---|---|---|---|
| `1234` | `$1,234.0` | numeric: remove `$`, comma, parse float | equal |
| `a; 12` | `A, 12%` | list: split on comma/semicolon; string normalization plus numeric normalization | equal |
| `New York` | `new york` | string: remove whitespace/punctuation and lowercase | equal |
| `1,2` | `1` | list length mismatch | false |

A missing answer should be treated as a failed extraction and recorded as such;
do not pass `None` to a downstream string-normalization helper without checking
how the installed version handles it. For strict benchmark reporting, keep the
raw answer, extracted answer, ground truth, and scorer result together.
