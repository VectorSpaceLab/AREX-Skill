---
name: skills-and-installation
description: "Operate safe Claude/Codex skill installation and research-support routes for papers, conferences, reports, and Obsidian."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Skills and installation

Use this sub-skill for the repository's eight user-facing research and
integration skills, and for the installer ownership boundary. It is a router:
it does not reimplement the experiment loop, provider clients, execution
backends, tool registry, GPU logic, memory format, or report rendering APIs.
Hand those questions to the sibling sub-skill that owns the relevant core API.

## Operating contract

1. Inspect first. Installation and uninstallation are opt-in side effects; do
   not run them merely because a user mentions the repository.
2. Keep the source and destination roles separate:
   - Claude receives one command Markdown file per source skill.
   - Codex receives one directory per source skill, a transformed `SKILL.md`,
     copied supporting files, and an ownership marker.
3. Before an explicit install, identify the repository's immediate source-skill
   root and the two destination roots. Refuse to flatten or merge nested
   generated skill roots.
4. Never overwrite an existing Codex destination unless its ownership marker is
   present. An unmarked destination is foreign or ambiguous, even when its
   name matches a source skill.
5. Do not treat Codex UI/export metadata as generated source content. In
   particular, `agents/openai.yaml` is packaging metadata, not a source skill
   reference or a replacement for `SKILL.md`.
6. For paper and conference routes, state the network requirement and preserve
   graceful failure. Do not request, invent, or persist credentials for public
   literature endpoints. LLM calls still require the separately configured
   provider or subscription.
7. Before a report or Obsidian refresh, confirm the intended project and output
   route. A vault write, local note write, or dated report is a user-visible
   mutation.
8. Do not import this graph, its sub-skills, or source skills into live managed
   skill directories from this task. The explicit boundary is “inspect, draft,
   or plan”; installation into `~/.claude` or `~/.codex` requires a separate,
   user-approved operation.

## Route by trigger

| User intent or trigger | Route | First action |
|---|---|---|
| launch/resume 24/7 loop, `PROJECT_BRIEF.md`, cycles, GPU flag | `auto-experiment` | Confirm project, brief, and execution target |
| current loop, cycle count, PID, latest log, directive | `experiment-status` | Inspect project state without changing it |
| free/busy GPU, utilization, temperature, remote server | `gpu-monitor` | Use local or explicitly named remote target |
| newest arXiv work, topics, daily recommendations, dedup | `daily-papers` | Ask for topics if absent; require network |
| one paper, arXiv id/URL, figures, method/results analysis | `paper-analyze` | Validate identifier; require network for fetches |
| venue, conference, query, CVPR/NeurIPS/ICML search | `conf-search` | Require venue and query; use Semantic Scholar route |
| milestones, experiments, metrics, blockers, next steps | `progress-report` | Read project history; confirm report destination |
| dashboard, daily note, Obsidian, local progress export | `obsidian-sync` | Check `obsidian.enabled` and choose vault/fallback |

The exact source frontmatter, command forms, network limits, and output shapes
are in [source-integrations.md](references/source-integrations.md). Core
installation mechanics are in [installation.md](references/installation.md).

## Install decision

Use `python install.py` only after the user explicitly asks to install the
integrations and confirms that the current repository is the intended source.
The command targets the user's Claude and Codex directories by default. First
perform a read-only conflict check or a temporary-fixture rehearsal; never use
home directories for a rehearsal.

The install transaction checks all Codex conflicts before writing Claude command
files. It then copies all immediate source skills to Claude, transforms only the
Codex `SKILL.md` frontmatter, copies runtime Python modules/configuration to
per-agent bundles, and prints the eight `/name` and `$name` entry points. A
successful install does not mean the research task has run.

Use `python install.py --uninstall` only after an explicit request and a review
of ownership. It removes matching Claude command files without a Claude marker,
removes only Codex skill directories bearing the installer marker, and removes
the per-agent runtime bundle. It does not remove an unmarked Codex skill.
See [troubleshooting.md](references/troubleshooting.md) for refusal, partial
state, network, and route-selection handling.

## Safe verification and active roots

The bundled checker is read-only:

```bash
python scripts/check_skill_layout.py --root <repository-or-skills-root>
```

It validates the eight immediate source skills and reports nested active roots
without descending into or merging them. A directory that itself has `SKILL.md`
and `sub-skills/` is an active generated root; treat it as one graph. In
particular, a nested `skills/disco/<repo-skill>` output is not another source
skill and must not be merged with the top-level source-skill set.

For installer tests, use a disposable fixture with explicit temporary
`claude_dir`, `codex_dir`, and `repo_dir` arguments. Assert the marker refusal,
Claude copy, Codex transformation, runtime-bundle copy, and marker-gated
uninstall. Do not call the default installer or uninstall command during a
verification pass. The checker and all instructions here avoid network,
credentials, daemon startup, training, and home-directory mutation by default.
