# Helper Resolution and Project Files

## Helper Resolution Chain

ARIS skills should not hardcode `python3 tools/<helper>.py` because project-local installs usually create `.aris/tools` rather than a top-level `tools/` directory. Resolve helpers in this order:

1. Skill-owned helper under the current skill directory, when a helper is bundled for that one skill.
2. Project-local `.aris/tools/<helper>` symlink or copy.
3. Project-local `tools/<helper>` manual copy.
4. ARIS repository from `ARIS_REPO` environment variable.
5. ARIS repository from `.aris/installed-skills.txt` `repo_root` field.
6. ARIS repository from the global pointer file under the user's home directory.

Use `scripts/aris_helper_resolver.py` to diagnose which path the chain selects:

```bash
python scripts/aris_helper_resolver.py --project /path/to/project --helper research_wiki.py
```

The resolver only reports paths; it does not execute the helper.

## Project Files Used by ARIS

| File or directory | Purpose |
| --- | --- |
| `CLAUDE.md` or `AGENTS.md` | Host-agent project guidance, ARIS managed block, backend hints, remote server notes. |
| `.aris/installed-skills*.txt` | Manifest of project-local ARIS skill symlinks and the source repo pointer. |
| `.aris/tools` | Symlink/copy to ARIS helper scripts for installed skills. |
| `.aris/skills-declined*.txt` | Remembered declined skills during selective install/reconcile. |
| `.aris/traces/<skill>/<date>_run<NN>/` | Reviewer trace directories for replay and audit. |
| `research-wiki/` | Persistent papers, ideas, experiments, claims, graph edges, log, and query pack. |
| `PIPELINE_STATUS.md` or equivalent status files | Human and agent recovery checkpoint for long workflows. |
| `EXPERIMENT_PLAN.md`, `EXPERIMENT_LOG.md`, `NARRATIVE_REPORT.md` | Core W1/W1.5/W2/W3 handoff files. |
| `REVIEW_STATE.json` | Auto-review-loop resume state. |
| Audit verdict files | `EXPERIMENT_AUDIT`, `PAPER_CLAIM_AUDIT`, `CITATION_AUDIT`, `KILL_ARGUMENT`, and related JSON/Markdown reports. |

## Artifact Discipline

- Markdown and JSON state files are canonical; rendered HTML is a view.
- Write timestamped artifacts first when a workflow has versioned outputs, then update the fixed latest filename.
- Reviewer calls should receive file paths and raw artifacts, not executor summaries, to preserve independence.
- If a helper cannot be found, fail explicitly and fix the install or pointer; do not silently invent a replacement.
