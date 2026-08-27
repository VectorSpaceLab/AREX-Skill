# Source integrations and research routes

The source package exposes eight skills. Their frontmatter is intentionally
small and Codex-compatible before installation: each has only `name` and
`description` in the current source snapshot. The `agents/openai.yaml` files
are UI/export metadata and are not operating-source content.

## Actual source frontmatter

| `name` | Exact `description` |
|---|---|
| `auto-experiment` | `Launch an autonomous THINK→EXECUTE→REFLECT experiment loop on a GPU project` |
| `conf-search` | `Search papers from top AI/ML conferences` |
| `daily-papers` | `Daily arXiv paper recommendations with automatic deduplication` |
| `experiment-status` | `Check status of running autonomous experiment loops` |
| `gpu-monitor` | `Check GPU status, running experiments, and available resources` |
| `obsidian-sync` | `Refresh Obsidian dashboard and daily notes from current experiment state` |
| `paper-analyze` | `Deep analysis of a single paper with figure extraction from arXiv source` |
| `progress-report` | `Generate structured research progress reports` |

The Claude command name and Codex skill name are the directory name, not a
frontmatter transformation invented by the router. Claude examples use
`/name`; Codex examples use `$name`.

## Core experiment routes

### `auto-experiment`

**Triggers:** launch, start, resume, or run an autonomous experiment; 24/7
loop; THINK/EXECUTE/REFLECT; project brief; `--project`; `--gpu`;
`--max-cycles`.

**Documented forms:**

```text
/auto-experiment
/auto-experiment --project <project> --gpu 0
/auto-experiment --project . --max-cycles 5
$auto-experiment
```

The project must contain `PROJECT_BRIEF.md`. An optional project `config.yaml`
can select the provider, model, cycle bounds, polling, dry-run policy, or SSH
execution. The route owns integration selection only; delegate loop phases,
provider behavior, execution backends, and tool APIs to their owning sibling
sub-skills. Do not start training or a daemon during a read-only verification.

### `experiment-status`

**Triggers:** status, progress, cycle count, current best, PID, latest training
log, pending `HUMAN_DIRECTIVE.md`, or “is the experiment running?”.

**Documented forms:**

```text
/experiment-status
/experiment-status --project <project>
$experiment-status
```

Read the project brief, memory log, cycle counter, backend process status,
latest log tail, GPU status, and pending directive. In SSH mode, controller
state is local to the project while PID/log/GPU checks use the configured
remote backend. This route is inspection-first and should not alter project
state.

### `gpu-monitor`

**Triggers:** GPU status, free/busy devices, utilization, memory, temperature,
training processes, remote GPU server.

**Documented forms:**

```text
/gpu-monitor
/gpu-monitor --server user@remote-host
$gpu-monitor
```

The result is a GPU table plus free devices and training assignments. A
`--server` request changes the inspection target; do not infer a remote host
from a project path. Delegate actual GPU/backend implementation to the core
execution sub-skill. A safe check may inspect availability, but must not launch
or reserve a process.

## Literature routes

### `daily-papers`

**Triggers:** daily papers, latest papers, arXiv recommendations, recent
preprints, topics, relevance ranking, deduplicate recommendations.

**Documented behavior:** ask for topics when none are supplied (or use config
defaults), search papers from the previous one to three days, compare IDs with
previous recommendations, rank by relevance, give detailed analyses for the
top five, brief summaries for the next five, and save a dated Markdown result.

**Documented form:**

```text
/daily-papers --topics "vision transformer, image classification"
$daily-papers
```

This is a network route. The low-level arXiv tool uses a public Atom endpoint,
sorts by submitted date, accepts a query plus optional category and limit, and
has a 20-second request timeout. It sends a user-agent but no API key. Network
failure is returned as an error rather than a local paper list. Do not claim
freshness or deduplication if the network request, prior-ID store, or dated
output cannot be read. Do not download data during a safe verification.

### `paper-analyze`

**Triggers:** analyze one paper, arXiv ID or URL, abstract/method/results,
figures, equations, source package, PDF fallback, limitations.

**Documented forms:**

```text
/paper-analyze <arxiv_id-or-url>
$paper-analyze
```

The route fetches arXiv metadata, tries the arXiv source archive for actual
figures, falls back to PDF reading when source is unavailable, and produces a
structured analysis containing problem, motivation, method, experiments, and
insights. Figure files are named with the arXiv ID prefix to avoid collisions.

Treat network access as required for a fresh fetch. The documented public
arXiv flow does not ask for a paper-service credential; do not prompt for one
unless a separately configured service explicitly requires it. LLM provider
authentication is independent: model analysis still needs the selected API key,
compatible endpoint credentials, or logged-in subscription CLI. If fetching is
disallowed, return a bounded “not fetched” result rather than substituting
invented paper facts.

### `conf-search`

**Triggers:** conference search, venue, CVPR, ICCV, ECCV, NeurIPS, ICML, ICLR,
AAAI, IJCAI, ACL, EMNLP, NAACL, SIGGRAPH, venue plus query, citation count.

**Documented forms:**

```text
/conf-search --venue CVPR2025 --query "gesture generation"
/conf-search --venue NeurIPS2025 --query "diffusion models"
$conf-search
```

The source route parses venue and query, searches Semantic Scholar, ranks by
relevance and citation count, shows title/authors/abstract/citations, and can
offer deep analysis of a result. The documented venue list is not exhaustive;
accept a supported venue string supplied by the user rather than silently
normalizing it to a different event.

The inspected low-level `search_papers` contract accepts `query`, `limit`, and
optional `year`, and requests title/year/authors/abstract/citation count/URL
from Semantic Scholar. It has no separate `venue` parameter. Therefore encode
the requested venue in the query/year constraints as the available tool
allows, then verify venue in returned metadata; never promise a server-side
venue filter that the tool does not expose. Requests use a public endpoint,
user-agent, and a 15-second timeout with no API key in the observed code.
Errors are returned as `Search failed: ...`. A safe verification must mock or
skip this network path.

### Literature-tool limits

The agent's idea worker has `search_papers`, `search_arxiv`, and `get_paper`.
`get_paper` accepts a Semantic Scholar paper ID, `arXiv:<id>`, DOI, or
`CorpusId:<id>`, optionally includes references/citations, and trims each
returned list to 25 entries. An empty ID fails before network access. These
are implementation/tool facts, not extra command names; route core tool/API
questions to the sibling core sub-skills.

## Report and note routes

### `progress-report`

**Triggers:** progress report, milestone summary, recent experiments, best
result, key insights, next steps, blockers, metrics table.

**Documented form:**

```text
/progress-report
$progress-report
```

Read `MEMORY_LOG.md` for milestones and decisions plus recent experiment logs,
then render:

```text
# Progress Report — YYYY-MM-DD
## Current Status
## Recent Experiments
## Key Insights
## Next Steps
## Blockers
```

Confirm the project and report destination before writing. Do not claim a
metric that is absent from project history, and do not turn a report request
into an experiment launch.

### `obsidian-sync`

**Triggers:** Obsidian, dashboard, daily note, progress export, local text
fallback, refresh notes, `--dashboard-only`, `--daily-only`.

**Documented forms:**

```text
/obsidian-sync --project <project>
/obsidian-sync --project <project> --dashboard-only
/obsidian-sync --project <project> --daily-only
$obsidian-sync
python -m core.obsidian --project <project>
```

The route reads project configuration, brief, memory log, state, and cycle
counter. If `obsidian.enabled` is false or absent, it reports that progress
export is disabled and tells the user to enable it; it does not silently write
notes. With a non-empty `obsidian.vault_path`, refresh writes
`<vault>/<project_subdir>/Dashboard.md` and the dated `Daily/YYYY-MM-DD.md`.
With an empty vault path, it uses project-local
`workspace/progress_tracking/Dashboard.txt` and
`workspace/progress_tracking/Daily/YYYY-MM-DD.txt`.

Dashboard refresh overwrites the current dashboard. Daily entries append. The
`--dashboard-only` route writes only the dashboard; `--daily-only` appends a
manual daily entry. A full enabled refresh does both. Confirm the chosen vault
or local route before mutation, and route implementation details to the core
report/Obsidian sub-skill.

## No-import boundary

These routes describe source integrations only. They do not authorize copying
this generated graph into managed Claude/Codex locations, merging nested
`skills/disco` output with source skills, or importing any `agents/openai.yaml`
metadata into generated source content. Installation and import are separate
approval-gated operations.
