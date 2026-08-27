# ARIS Workflow Map

## Main Research Chain

| Workflow | Typical skill | Input | Output / handoff | Use when |
| --- | --- | --- | --- | --- |
| W1 | `/idea-discovery` | Research direction | Idea report, experiment plan, refined proposal | Starting from a broad direction or topic. |
| W1.5 | `/experiment-bridge` | Experiment plan | Code, sanity checks, initial results, experiment log | A concrete experiment plan exists and needs implementation/deployment. |
| W2 | `/auto-review-loop` | Paper, results, or scope | Revised work, review state, narrative report | Need iterative external critique and fixes. |
| W3 | `/paper-writing` | Narrative report or structured evidence | Manuscript source/PDF plus audit reports | Ready to write or polish a submission. |
| W4 | `/rebuttal` | Paper plus reviews | Paste-ready and rich rebuttal drafts | Reviews have arrived. |
| W5 | `/resubmit-pipeline` | Existing paper directory | New-venue resubmission package | Rejected/redirected paper needs text-only venue porting. |
| W6 | `/paper-talk` | Accepted paper | Slides, talk script, Q&A prep | Prepare presentation materials. |

## Audit Chain at Submission Assurance

ARIS uses separate audit skills for experiment honesty, claim support, paper number correctness, citation correctness, and adversarial rejection analysis. At strict assurance levels, one non-green gate can block final reporting. Treat these gates as workflow safety features, not optional polish.

## Choosing Orchestrator vs Leaf Skill

Choose an orchestrator when the user asks for a lifecycle stage with multiple outputs. Choose a leaf skill when the request is narrow: search arXiv, render one Markdown file, compile LaTeX, monitor an experiment, draft claims, or produce a specific figure/table.

## Common Parameter Semantics

- `effort: lite | balanced | max | beast`: depth, fan-out, number of rounds, and budget.
- `assurance: draft | polished | conference-ready | submission`: how strict audit gates are.
- `reviewer`: reviewer route; `auto`, Codex, oracle-pro, manual, or model/provider-specific variants depending on host.
- `gpu`: local, remote, Vast, Modal, or other configured backend.
- `human checkpoint`: whether to pause for approval.
- `AUTO_PROCEED`: whether the workflow continues automatically through gates that allow it.

## Artifact Handoff Discipline

- Use fixed filenames for current canonical state and timestamped copies for version history when a skill specifies both.
- Reviewer calls should use file paths and raw artifacts; avoid executor summaries that bias review.
- If a required artifact is missing, either generate it with the upstream workflow or explicitly narrow the task.
