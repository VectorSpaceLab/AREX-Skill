# ROSA experiment workflows

## What ROSA is in this repository

ROSA means Rapid Online Suffix Automaton. The RWKV-8 notes frame ROSA as an
experimental path for improving RNNs with richer online state. The toy scripts
show how suffix-like memory can help copy/count/reverse digit sequences or
augment simple recurrent models.

## Script families

| Family | What it demonstrates | Runtime expectation |
| --- | --- | --- |
| `251014_rosa_1bit_train.py` | Embedding plus 1-bit ROSA layer trained on number sequences | CUDA and long toy training; extremely slow backward in comments |
| `251016_rosa_1bit_run.py` | Runs a saved two-layer 1-bit ROSA toy checkpoint | CUDA and a local `.pth` file |
| `251024_rosaQKV_run.py` | ROSA-QKV arithmetic-style digit task with RWKV-7-like block pieces | CUDA, local checkpoint, custom extension |
| `251105_reverse_run.py` | Reverse-digit toy task with small parameter count | CUDA, local checkpoint, custom extension |
| `260212_rosa1bitLM_L12.py` | ROSA-1bit language-model demo | CUDA and model checkpoint |
| `260222_rosa4bitLM_L12.py` | ROSA-4bit language-model demo | CUDA and model checkpoint |

## CPU-safe first step

Run `scripts/rosa_suffix_automaton_demo.py` to inspect the online suffix output
on a string or token list. This validates the algorithmic idea without claiming
that any GPU training script or checkpoint has been verified.

## When to run the full scripts

Only run the original full scripts when the user has:

- a compatible CUDA-enabled torch environment
- required checkpoints in the expected format
- enough time for toy training or extension compilation
- a clear goal, such as reproducing the reverse-digit output or studying a
  specific ROSA-QKV implementation detail

If any of those are missing, keep the answer at the reference/algorithm level.

## Interpreting outputs

Many scripts print input, gold sequence, ROSA-only prediction, model prediction,
diff markers, and accuracy. Treat these as toy-task diagnostics, not as general
LLM benchmark results.
