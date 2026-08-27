# Neural Networks Troubleshooting

## Purpose

Read this when neural-network explanations, snippets, or documentation edits need caveats. It covers conceptual errors, optional dependency issues, and source-code limitations from ML Glossary.

## Conceptual mistakes to catch

| Symptom | Likely issue | Correction |
| --- | --- | --- |
| User says a neuron is just a linear regression model | Missing activation and layered composition. | A neuron's weighted input is linear, but activation and stacking layers create nonlinear models. |
| User confuses activation and loss | Both are functions but occur at different points. | Activation transforms layer outputs; loss compares prediction to target. |
| User expects ReLU to be always better | Overgeneralization. | ReLU is cheap and effective but can have dead neurons; sigmoid/tanh/softmax still have output-layer roles. |
| User asks why backpropagation is not just one derivative | Network is nested across layers. | Backprop applies chain rule repeatedly and reuses layer errors. |
| User applies dropout at inference like training | Training/inference behavior differs. | Dropout randomly drops units during training; inference uses all units with appropriate scaling behavior. |
| User treats gradient accumulation as changing the model objective | Misunderstanding memory workaround. | It approximates a larger batch by accumulating mini-batch gradients before updating. |
| User wants to run architecture snippets as production training | Source code was illustrative. | Provide caveats, ask for a framework/data target, or write a small modern example. |

## Optional dependency and backend caveats

The runtime skill does not require PyTorch, TensorFlow, GPU, datasets, or notebook execution. The original architecture examples often assumed PyTorch-like APIs and datasets. If the user wants executable architecture training:

1. Ask or infer the desired framework and dataset.
2. Separate repo-grounded concept explanation from modern external implementation.
3. Avoid downloads, GPU jobs, or long training unless the user explicitly approves.
4. Provide a tiny CPU-only smoke example when possible.

## Legacy source-code caveats

- Neural code under the original `code/` tree mixed NumPy and PyTorch examples.
- Some snippets were written for Sphinx `literalinclude` and may not be standalone scripts.
- Architecture training functions were not selected as required verification because they can require external datasets and long runs.
- Optimizer source snippets included syntax/incompleteness issues; use conceptual optimizer descriptions unless writing fresh code.

Use `../scripts/activation_loss_demo.py` for a safe runtime-owned calculation demo.

## Documentation-maintenance guidance

- Keep architecture entries beginner-first: definition, components, use case, caveats, citation.
- If adding code to RST, include all imports and avoid hidden dataset downloads.
- If adding math, define `X`, `W`, `b`, `Z`, activation, prediction, and loss before writing formulas.
- For backpropagation, use the chain-rule story rather than dumping a long derivative chain unless the user requested derivation.
- Cross-link calculus/linear algebra prerequisites to basics/math.

## Common Sphinx/code warning causes for neural pages

- `literalinclude` references a Python object that no longer exists or cannot be parsed.
- PyTorch examples import modules unavailable in the docs-build environment.
- Long code blocks have inconsistent indentation or tabs.
- External image references or local images are missing from the active docs tree.
- Inline math uses unsupported or malformed LaTeX.

## Recovery steps

- Replace fragile `literalinclude` blocks with short, explicit Python 3 snippets when maintaining documentation.
- If a code example is too large, move it to a maintained example file in the user's active checkout and include a small excerpt in docs.
- If a build warning predates the user's edit, report it separately instead of silently fixing broad legacy issues.
- If a user asks for GPU evidence, state that the generated skill selected CPU-only documentation verification; GPU architecture training was optional and not verified.
