# Project recipes

This subtree stays on console-first utilities, algorithm demos, and small file transformers. Use the tables below to decide whether a project stays here or should route to another subtree.

## Family map

| Family | Examples | Core shape | Safe default |
| --- | --- | --- | --- |
| File and text utilities | `Cat_command`, `csv_to_json`, `Email Slicer`, `Encode_Morse.py`, `ExtractPhoneNumberEmail`, `lorem_in_python`, `string_manipulator` | Read a local string or file, transform it, print or write the result. | Use explicit `Path` values, preserve encoding, and avoid silent overwrites. |
| Data structures | `Binary_Search_Tree`, `Binary_tree`, `Prefix_Trie`, `linked_lists`, `Stack_structure` | Importable classes or modules with simple operations such as add, search, push, pop, and print. | Exercise methods directly with synthetic values instead of running demo bodies. |
| Numeric transforms and ciphers | `Caesar_Cipher`, `Converting_Roman_to_Integer`, `Converter`, `infix_postfix_calculator`, `Triangle Calculator`, `Weights_on_different_planets` | Pure math, lookup-table, or conversion logic with a thin prompt wrapper. | Keep the transform pure and isolate prompts or menus in `main()`. |
| Console puzzles | `Tower-of_Hanoi`, `Number Guessing`, `Number Guessing Upper Boundary`, `Word_Jumble`, `minionGame` | Prompt-driven game or solver loops. | Treat as interactive CLI and avoid auto-running during smoke checks. |
| Password tools | `Password_Generator_2`, `Password Generator` | Random password generation, sometimes wrapped in Tk. | Keep the generator logic importable; treat any Tk shell as GUI-only. |
| Shell helper | `Execute Shell Command` | Small wrapper around a fixed shell command or command execution helper. | Never broaden it into arbitrary user-controlled shell execution. |

## Representative handling notes

| Project | Typical behavior | Notes for future agents |
| --- | --- | --- |
| `Cat_command/cat.py` | Prints a file to stdout from one positional path argument. | Good smoke target. It should be run from the project directory or with an absolute file path. |
| `Execute Shell Command/execute_shell_command.py` | Runs a command with `subprocess.Popen(shell=True)`. | Keep this project bounded to the repo's fixed `echo` test. Do not expose user input to the shell. |
| `Execute Shell Command/execute_shell_command_test.py` | Verifies the helper with `echo Khanna`. | This is one of the two curated safe native checks for this subtree. |
| `csv_to_json/csv_to_json.py` | Reads CSV rows and writes `data.json`. | The current script writes a fixed output file in the working directory. If extended, make the output path explicit. |
| `Diff_Utility/diff.py` | Compares two files and prints colored line differences. | Requires `rich`. It assumes aligned line counts and should be treated as a lightweight utility, not a full diff engine. |
| `Password_Generator_2/password_generator` | Pure password generator function. | Best import target for tests. Raises `ValueError` when no character classes are selected. |
| `Password Generator/password_generator.py` | Tk-based password generator window. | Keep the generator logic in mind, but do not run the GUI shell in headless smoke checks. |
| `Smart_Calculator/calculator.py` | Opens a Tk calculator window at import time. | Static-only by default. The `Tk()` call and `mainloop()` make it unsafe for headless smoke runs. |
| `string_manipulator/string_manipulator.py` | Wraps built-in string operations in a class. | Easy to verify with direct method calls and no environment setup. |
| `Tower-of_Hanoi/hanoi.py` | Interactive puzzle loop with global state. | Keep any future refactor split into move logic plus prompt handling so the logic can be tested independently. |
| `Encode_Morse.py/main.py` | Encodes strings with a Morse mapping and prints a demo at the bottom. | If reused, guard the demo print under `main()` so imports stay quiet. |
| `lorem_in_python/lorem.py` | Prompts for row count and writes lorem text to `lorem_in_python/text.txt`. | This is a file-writing demo; use explicit output paths and keep generation gated by `main()`. |
| `Converter/converter.py` | Menu-driven unit converter. | The current implementation uses `eval` in the conversion formula. For new work, replace that with explicit numeric operations or table lookup. |

## Edge-case reminders

- `Binary_tree/main.py`, `Prefix_Trie/main.py`, and similar demos are often just tiny harnesses around importable classes.
- `Caesar_Cipher`, `Converting_Roman_to_Integer`, and `Email Slicer` are best treated as console utilities with a single transform step.
- `lorem_in_python` and `csv_to_json` are file writers, so they should always make the output destination obvious.
- If a task primarily needs a GUI shell, a network client, or a heavy ML/data pipeline, route it away from this subtree even if the core math or parsing logic looks simple.
