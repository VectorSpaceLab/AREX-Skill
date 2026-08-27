# API and CLI patterns

Use these patterns when adding or reviewing console-first utilities in this subtree.

## Preferred shapes

| Shape | Use it for | Examples | Notes |
| --- | --- | --- | --- |
| `argparse` + `Path` | File utilities and one-argument CLIs | `Cat_command`, `Diff_Utility`, `csv_to_json` | Parse paths as `pathlib.Path`, print a clear `--help`, and keep path display separate from execution. |
| Pure function module | Reusable transforms and math helpers | `Password_Generator_2`, `string_manipulator`, `Caesar_Cipher`, `Converting_Roman_to_Integer` | Make the core behavior importable and free of prompts. |
| Importable class | Trees, stacks, linked lists, tries, and other structures | `Binary_tree`, `Binary_Search_Tree`, `Prefix_Trie`, `linked_lists`, `Stack_structure` | Put the demo in a small harness; keep the structure API callable directly. |
| Interactive prompt loop | Simple converters and puzzles | `Converter`, `Email Slicer`, `Tower-of_Hanoi`, `lorem_in_python` | Keep the loop inside `main()` so imports stay quiet. |
| Fixed command runner | Shell helpers | `Execute Shell Command` | Use an explicit command or a verified test-only command; do not accept arbitrary user shell text. |
| GUI wrapper | Tk-based utilities | `Password Generator`, `Smart_Calculator` | The GUI shell is an edge case here; do not smoke-test it in a headless environment. |

## Small CLI template

```python
from argparse import ArgumentParser
from pathlib import Path


def main(argv=None) -> int:
    parser = ArgumentParser(description="Describe the utility")
    parser.add_argument("source", type=Path, help="Input file")
    args = parser.parse_args(argv)

    # keep the real work in a helper function
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Runtime and API rules

| Rule | Why it matters | Better approach |
| --- | --- | --- |
| Keep side effects behind `main()` | Prevents import-time prompts, file writes, and GUI launches. | Move demo code under a guard and call it from `main()`. |
| Use `subprocess.run([...], shell=False)` for new helpers | Avoids shell injection and quoting bugs. | Reserve `shell=True` only for the repository's fixed smoke test helper. |
| Quote paths only for display | Display quoting is helpful, but execution should use real argument lists. | Use `shlex.quote` in logs and `Path`/lists when calling subprocess. |
| Validate `sys.argv` or use `argparse` | Makes errors readable and safe. | Prefer `argparse` with `--help` and explicit required arguments. |
| Keep math and parsing separate from I/O | Easier to test and reuse. | Put arithmetic, lookup tables, and parsing in helpers that return values. |
| Avoid `eval` in conversion helpers | The current `Converter` pattern is fragile and unsafe to copy. | Use explicit arithmetic or a lookup table. |
| Avoid fixed output names unless they are documented | Hidden overwrites are easy to miss. | Add an output argument or clearly document the default output file. |

## Pattern notes by project style

| Style | Example path names | Good test shape |
| --- | --- | --- |
| File printer | `Cat_command/cat.py` | Run the script on a tiny fixture and compare stdout exactly. |
| File transformer | `csv_to_json/csv_to_json.py`, `lorem_in_python/lorem.py` | Feed a small input and assert the output file exists and contains the expected format. |
| Algorithm module | `Password_Generator_2/password_generator`, `string_manipulator/string_manipulator.py` | Import the function or class and call it with synthetic values. |
| Data-structure module | `Binary_Search_Tree/bst.py`, `Prefix_Trie/trie.py`, `linked_lists/*` | Build a structure in memory and verify operations directly. |
| Prompt-driven demo | `Tower-of_Hanoi/hanoi.py`, `Converter/converter.py`, `Email Slicer/EmailSlicer.py` | Keep prompt interactions outside the core logic and smoke-test only the reusable helpers. |
| Command executor | `Execute Shell Command/execute_shell_command.py` | Keep the allowed command fixed and review the output contract carefully. |

## Special caution

`Smart_Calculator/calculator.py` imports Tk and creates a window immediately. That makes it unsuitable for headless smoke runs and a good example of why GUI shells should stay separate from reusable logic.
