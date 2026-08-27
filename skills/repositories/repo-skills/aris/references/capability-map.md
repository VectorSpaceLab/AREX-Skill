# ARIS Capability Map

## What ARIS Provides

ARIS is a methodology and skill corpus for agentic research. It uses Markdown skills, shared references, helper scripts, optional MCP servers, and project-local state files to run a research loop with independent review and persistent evidence.

| Capability family | Main user intent | Route |
| --- | --- | --- |
| Project-local install and update | Install ARIS into a research project; select skill groups; reconcile new upstream skills; uninstall safely | `sub-skills/install-and-distribution/SKILL.md` |
| Workflow selection | Decide whether to run idea discovery, experiment bridge, auto-review, paper writing, rebuttal, resubmission, talk, or a leaf utility | `sub-skills/workflow-routing-and-skill-catalog/SKILL.md` |
| Reviewer/backend setup | Configure Codex MCP, Claude/Gemini reviewer overlays, manual review, generic LLM, MiniMax, ModelScope, Feishu/Lark, or image bridge | `sub-skills/review-and-provider-backends/SKILL.md` |
| Research state and experiment ops | Use `research-wiki/`, pipeline status, hooks, watchdog, experiment queue, remote GPU details, or session recovery | `sub-skills/state-recovery-and-experiment-ops/SKILL.md` |
| ARIS repo development | Modify skills, docs, helper scripts, installer scripts, MCP servers, mirrors, or tests in the ARIS checkout | `sub-skills/repository-maintenance/SKILL.md` |

## Important ARIS Terms

- **Executor**: the model/agent family that writes code, drafts papers, or applies changes.
- **Reviewer**: an independent model, human, or deterministic verifier that critiques or accepts outputs.
- **Cross-model review**: acceptance by a different model family from the executor. Same-family Codex self-review is only provisional unless another independent gate accepts it.
- **Workflow IDs**: W1 idea discovery, W1.5 experiment bridge, W2 auto-review loop, W3 paper writing, W4 rebuttal, W5 resubmission, W6 talk.
- **Research Wiki**: persistent local knowledge base for papers, ideas, experiments, claims, graph edges, and query packs.
- **Helper-resolution chain**: the ordered lookup used by ARIS skills to find helper scripts without hardcoding `python3 tools/foo.py`.
- **Assurance**: a user-facing strictness axis (`draft`, `polished`, `conference-ready`, `submission`) that controls whether audit gates block final reports.

## Operating Boundaries

- This repo skill is a distilled guide. It does not make external reviewer credentials, GPUs, LaTeX, Feishu, Overleaf, or Codex/Claude/Gemini CLIs available.
- If a user asks to run ARIS workflows, first verify the target project has installed ARIS skills and the needed optional backends.
- If a user asks to edit ARIS itself, treat it as repository maintenance and run the smallest safe native checks that cover the changed surface.
