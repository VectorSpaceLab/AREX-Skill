# Skill Groups

ARIS's selective installer groups skills by role. The exact catalog can evolve, but these group families are the routing baseline.

| Group family | What it covers | Examples of requests |
| --- | --- | --- |
| Literature/search | arXiv, OpenAlex, Semantic Scholar, Exa, Gemini, debugging search, literature review | "Find recent papers", "verify closest prior work", "debug this error via issues" |
| Ideation | idea generation, novelty check, proposal refinement, Research Wiki, full research pipeline | "start a project from this direction", "make an experiment plan" |
| Review loop | research review, auto-review, kill-argument, LLM/MiniMax review variants | "run overnight review and fixes", "stress-test my method" |
| Theory | derivation, proof writing, proof checking, proof orchestration | "formalize this lemma", "audit proof gaps" |
| Experiments/infrastructure | experiment plan/bridge, GPU run, monitoring, queueing, result analysis, audits, cloud/remote backends | "deploy this experiment to remote GPU", "monitor training" |
| Paper core | plan/write/compile papers, figures, citation and claim audits, Overleaf, integrity forensics | "turn this narrative into a paper", "audit citations" |
| Visuals | diagrams, posters, slides, talk prep, AI-generated illustrations | "make slides", "render a workflow diagram" |
| Submission | rebuttal, resubmission, grant proposals | "write NeurIPS rebuttal", "port paper to ICML" |
| Patent | invention structuring, claims, embodiments, prior art, jurisdiction formats | "turn this idea into patent claims" |
| Meta/utilities | meta-optimization, notifications, interview cheatsheets, miscellaneous integrations | "optimize the ARIS skills", "send Feishu notification" |

## Dependency Edges

The catalog records dependencies only when a default run actually exercises another skill or requires its artifact. Do not infer dependencies from see-also links. If a selected skill requires another and the user excludes it, warn about expected feature loss rather than silently adding it.

## Mirrors and Overlays

- Mainline skills live in the default skill corpus and target hosts that understand `SKILL.md` directly.
- Codex mirrors adapt execution/review mechanics for Codex CLI.
- Claude-review and Gemini-review overlays override selected Codex mirror skills so Codex can use an independent reviewer.

## Maintenance Signal

If a new mainline skill is added, it should appear exactly once in the catalog. Catalog completeness and stale-entry tests are important repository-maintenance checks.
