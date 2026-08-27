---
name: cli-algorithms-and-utilities
description: "Route pure-Python CLI, algorithm, data-structure, calculator,
  text/file utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI Algorithms and Utilities

Use this sub-skill for stdlib-heavy command-line utilities, algorithms, data structures, text transforms, file transforms, and related non-display-first calculators or puzzles in this repository.

## In scope
- Cat_command
- Execute Shell Command
- Binary_Search_Tree
- Binary_tree
- Caesar_Cipher
- Converter
- Converting_Roman_to_Integer
- Diff_Utility
- Email Slicer
- Encode_Morse.py
- ExtractPhoneNumberEmail
- Password Generator
- Password_Generator_2
- Prefix_Trie
- Stack_structure
- Tower-of_Hanoi
- csv_to_json
- linked_lists
- string_manipulator
- lorem_in_python
- related console-first calculators and puzzles

Keep the password and calculator logic here when the task is about the algorithm or CLI surface. If the task is mainly a Tk or other GUI shell, route that GUI work to games-gui-and-desktop.

## Route elsewhere
- GUI-first, Tk, pygame, turtle, or desktop app work -> games-gui-and-desktop
- Network, API, service, bot, or credential automation -> web-network-and-automation
- Data, media, CV, ML, or heavy notebook workflows -> data-media-ml-and-vision

## Working rules
- Prefer pure functions or small classes plus thin CLI wrappers.
- Keep file paths as `Path` objects; assume project folders may contain spaces.
- Do not use `shell=True` for new helpers; only preserve the repository's fixed shell smoke test.
- Keep all side effects behind `main()` and `if __name__ == "__main__":`.
- Treat Tk imports or immediate `mainloop()` calls as GUI edge cases, not standard smoke targets.

## Safe validation
- Use `scripts/run_stdlib_smoke_checks.py` for the only curated native checks in this subtree.
- Default mode lists the checks for a target checkout.
- Pass `--run` to execute only the curated checks:
  - `Cat_command/cat.py` with `Cat_command/test_cat.txt`
  - `Execute Shell Command/execute_shell_command_test.py`

## References
- `references/project-recipes.md`
- `references/api-and-cli-patterns.md`
- `references/troubleshooting.md`
