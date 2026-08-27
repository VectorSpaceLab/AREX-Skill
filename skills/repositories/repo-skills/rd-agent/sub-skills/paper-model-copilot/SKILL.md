---
name: paper-model-copilot
description: "Use RD-Agent's general model copilot to turn a paper/report PDF
  into a structured model experiment and iteratively developed PyTorch
  implementation."
metadata:
  disco-role: operating
  parent-skill: rd-agent
license: MIT
disable-model-invocation: true
---

# RD-Agent paper and model copilot

Use this sub-skill for `general_model`, paper/report-driven model implementation, model-coder workflows, and tensor-shape/evaluator troubleshooting. It is appropriate for tabular, time-series, and graph model research when a paper or report is the primary source.

## Input contract

Provide a local PDF report or paper path. The general-model entry point is:

```bash
rdagent general_model --report-file-path=<path-to-pdf>
```

Probe the exact option name with `rdagent general_model --help`. The implementation extracts a first-page image, loads an experiment description from the PDF, then sends it through a general-model scenario and Qlib model coder. A readable PDF is necessary but not sufficient: the paper must expose enough architecture, dimensions, data protocol, and objective details to implement and evaluate the model.

Use [inspect_pdf.py](scripts/inspect_pdf.py) for a local, read-only page-count/text probe before starting a model-generation loop. It does not upload or summarize the document.

## Reader → coder → evaluator workflow

1. Validate the PDF and identify the target task/data type.
2. Extract a structured record: inputs, outputs, architecture, tensor shapes, hyperparameters, loss, optimizer, training schedule, baseline, and evaluation protocol.
3. Mark details that are ambiguous or absent rather than inventing them.
4. Let the model coder generate an implementation and run a tiny tensor-shape/import check.
5. Compare the implementation against the paper's protocol; then run the smallest deterministic evaluator available.
6. Preserve the PDF identifier, structured experiment record, generated source, sample shapes, evaluator command, and deviations from the paper.

## Model-research hygiene

- Separate **paper fidelity** from **task performance**. A high score with a different split or architecture is not a faithful reproduction.
- Check tensor shapes at every boundary and use a tiny batch before expensive training.
- For time-series and graph data, document ordering, padding/masking, adjacency representation, and batching semantics.
- Avoid placing papers with restricted distribution, API keys, or private datasets in shared run directories.
- The general model flow is a copilot, not a paper-verification oracle; manually review extracted claims and all generated code.

Read [copilot-contract.md](references/copilot-contract.md) and route to [quant-finance](../quant-finance/SKILL.md) when the requested evaluator is specifically Qlib finance research.
