# Programming Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| “source files too many” or task stalls | tree exceeds practical file limit or includes generated/vendor files | use `plan_code_analysis.py`, split by module, exclude low-signal paths |
| generated architecture is shallow | model too weak or files lack comments/context | switch to stronger model; analyze core modules separately |
| uploaded archive cannot be parsed | wrong archive layout, unsupported compression, non-UTF8 paths | repackage as zip with source root at top level; remove binary files |
| docstring insertion changes code unexpectedly | LLM write workflow not reviewed or scope too broad | require backup/clean git state; run on small copy; review diffs manually |
| notebook analysis misses logic | outputs too large or hidden cells | clear outputs, export key cells, or analyze notebook plus supporting scripts |
| Markdown translation breaks code/API names | model translated code fences or identifiers | instruct not to translate code blocks, paths, symbols, formulas, or API names |
| API/model timeout during project analysis | too much parallel work or provider rate limits | lower worker count, split files, increase timeout, or use a faster model |
