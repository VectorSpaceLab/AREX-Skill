# DSL Compilation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unknown token` | The `.gui` file contains a token not defined for the selected platform. | Check platform vocabulary in `dsl-reference.md`; choose another platform or correct token names. |
| `Closing brace without matching opening token` | DSL has an extra `}`. | Remove the extra brace or restore the missing opening token before compiling. |
| `Unclosed tokens` | One or more `{` blocks never closed. | Add closing braces until the nesting returns to the implicit body root. |
| Output text/IDs change across runs | Original compilers generate random placeholder text and IDs. | Use `--seed` with the bundled helper for deterministic review output. |
| Output compiles but looks unrealistic | pix2code templates are research scaffolds, not complete app code. | Treat the output as a proof of DSL expansion, then hand-edit for production UI work. |
