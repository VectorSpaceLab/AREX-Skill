# LinearRNA API Reference

LinearRNA is PaddleHelix's pybind11-backed RNA secondary-structure extension. It exposes LinearFold for structure prediction and LinearPartition for partition-function/base-pair probability estimation.

## Import

Prefer the installed package import when the wheel/editable build placed the compiled extension under the package namespace:

```python
import pahelix.toolkit.linear_rna as linear_rna
```

Developer builds can also expose `c.pahelix.toolkit.linear_rna.linear_rna` from a build directory, or a direct `linear_rna` pybind module. Treat those forms as build/debug signals, not as stable public APIs. The bundled checker tries all three routes and reports which one imports.

## Function Families

| Function | Model | Purpose | Return |
| --- | --- | --- | --- |
| `linear_fold_c(sequence, beam_size=100, use_constraints=False, constraint="", no_sharp_turn=True)` | CONTRAfold-style machine-learning parameters | Predict one dot-bracket secondary structure. | `(structure: str, score: float)` |
| `linear_fold_v(sequence, beam_size=100, use_constraints=False, constraint="", no_sharp_turn=True)` | ViennaRNA-style thermodynamic parameters | Predict one dot-bracket secondary structure. | `(structure: str, free_energy: float)` |
| `linear_partition_c(sequence, beam_size=100, bp_cutoff=0.0, no_sharp_turn=True)` | CONTRAfold-style machine-learning parameters | Estimate partition score and base-pair probabilities. | `(score: float, pairs: list[(i, j, probability)])` |
| `linear_partition_v(sequence, beam_size=100, bp_cutoff=0.0, no_sharp_turn=True)` | ViennaRNA-style thermodynamic parameters | Estimate partition score and base-pair probabilities. | `(score: float, pairs: list[(i, j, probability)])` |

The public README signatures for LinearPartition contain the typo `no_sharpe_turn`, and its return section says `tuple(string, list)` even though the examples and pybind source return a numeric score plus a pair list. Use the actual pybind keyword `no_sharp_turn` and interpret LinearPartition returns as `(score, pairs)`. The `c` variants use learned CONTRAfold-style parameters; the `v` variants use ViennaRNA-style thermodynamic parameters.

## Parameters

- `sequence`: RNA sequence. The extension uppercases input and converts `T` to `U`, but its native validator only rejects non-alphabetic characters; validate user input first and prefer `A`, `C`, `G`, `U` only.
- `beam_size`: integer beam size, default `100`. Larger values keep more states and may be slower. `0` disables beam pruning.
- `use_constraints`: LinearFold-only boolean. Set to `True` only when passing a non-empty `constraint` string.
- `constraint`: LinearFold-only dot/parenthesis constraint string. It is ignored unless `use_constraints=True`.
- `bp_cutoff`: LinearPartition-only float threshold. The extension returns base pairs whose probabilities pass the cutoff; keep it in `[0.0, 1.0]` and use a positive value for compact output.
- `no_sharp_turn`: boolean, default `True`. When true, sharp hairpin turns are disallowed; the partition implementation skips base pairs closer than the configured turn length.

## Constraint Rules

A LinearFold constraint string must satisfy all of these before the API call:

- The string length matches the normalized sequence length.
- Characters are only `?`, `.`, `(`, and `)`.
- `?` means unconstrained, `.` means forced unpaired, and parentheses force a specific pair.
- Parentheses are balanced and properly nested, so crossing pseudoknot-like constraints are not expressible.
- Forced pairs must be canonical or wobble RNA pairs: `AU`, `UA`, `CG`, `GC`, `GU`, or `UG` after `T` is normalized to `U`.

The bundled checker catches length mismatches, illegal characters, unmatched parentheses, missing left parentheses before `)`, and non-canonical forced pairs before calling the extension. The C++ source prints errors and returns an empty structure with score `0` for many invalid constraints, and may not guard every malformed parenthesis pattern before stack access, so pre-validation is safer and easier for future agents to explain.

## Minimal Examples

Fold with the machine-learning parameterization:

```python
import pahelix.toolkit.linear_rna as linear_rna

structure, score = linear_rna.linear_fold_c("GGGCUCGUAGAUCAGCGGUAGAUCGCUUCCUUCGCAAGGAAGCCCUGGGUUCAAAUCCCAGCGAGUCCACCA")
```

Fold with constraints:

```python
sequence = "AACUCCGCCAGGCCUGGAAGGGAGCAACGGUAGUGACACUCUCUGUGUGCGUAGGUUGCCUAGCUACCAUUU"
constraint = "??(???(??????)?(????????)???(??????(???????)?)???????????)??.???????????"
structure, score = linear_rna.linear_fold_v(sequence, use_constraints=True, constraint=constraint)
```

Partition with a cutoff:

```python
score, pairs = linear_rna.linear_partition_c("UGAGUUCUCGAUCUCUAAAAUCG", bp_cutoff=0.2)
# pairs look like [(4, 13, 0.20071), ...] using 1-based positions.
```

## Output Interpretation

- LinearFold structures use dot-bracket notation with the same length as the normalized sequence when a valid structure is found.
- LinearFold scores differ by model family: the `c` variant is learned-parameter scoring; the `v` variant reports thermodynamic energy-like values.
- LinearPartition pair indices are 1-based positions from the original sequence order.
- Empty structure `""` with score `0` usually means invalid sequence/constraints or no valid constrained fold; validate first, then retry with simpler constraints or `no_sharp_turn=False` only if biologically justified.
- For invalid input, partition calls may return score `0.0` and an empty pair list instead of throwing; validate sequence and cutoff before interpreting an empty result as biology.

## Suggested Tiny Checks

Use toy sequences before long RNAs:

```bash
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GGGAAACCC --model c
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GGGAAACCC --model v
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence UGAGUUCUCGAUCUCUAAAAUCG --partition --bp-cutoff 0.2 --model c
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence UGAGUUCUCGAUCUCUAAAAUCG --partition --bp-cutoff 0.2 --model v
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GAAAC --constraint '(...)'
```

If the first two commands fail at import time, switch to `build-and-troubleshooting.md` instead of debugging user RNA input.
