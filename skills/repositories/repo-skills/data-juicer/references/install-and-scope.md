# Install and scope

## Verified package baseline
- Repository package: `py-data-juicer`
- Verified package version: `1.5.5`
- Primary import name: `data_juicer`
- Console scripts: `dj-process`, `dj-analyze`, `dj-install`, `dj-mcp`

## What this skill covers
- Local recipe workflows and analysis
- Ray execution, partitioning, checkpointing, and recovery
- API service and MCP tool routing
- Operator discovery, dataset loading, export, and utility helpers

## Recommended install matrix
| Workflow | Suggested extra(s) | Why |
| --- | --- | --- |
| Local recipes and local analysis | none, then `tools` if CLI/MCP helpers are needed | Core processing works from the base package; `tools` adds service-side helper packages. |
| Ray execution and recovery | `distributed` | Adds Ray and the distributed dependencies used by Ray-backed workflows. |
| Service / MCP workflows | `tools` | Adds `fastapi`, `mcp[cli]`, `rank-bm25`, and plotting utilities used by the service surface. |
| Image / video processing | `vision` | Enables multimodal operator families. |
| Text-heavy NLP workflows | `nlp` | Enables NLP-oriented operators and helpers. |
| Audio workflows | `audio` | Enables audio-oriented operators and helpers. |
| Broad model-backed operators | `generic` | Enables the model and runtime stack for more advanced operators. |
| External AI service integrations | `ai_services` | Enables DashScope, OpenAI, and labeling integrations. |
| Skill maintenance and docs work | `dev` | Adds project tooling for development-only tasks. |

## Practical rule
Do not install every optional group by default. Add only the extra that matches the workflow being routed.

## Smoke-check order
1. Import `data_juicer` in the inspection environment.
2. Run `dj-process --help`.
3. Run `dj-analyze --help`.
4. Run `dj-install --help`.
5. Run `dj-mcp --help` when service or MCP routes are relevant.

## Scope note
This repository has three major user-facing routes: local recipes, Ray recovery, and service/MCP routing. Keep those boundaries explicit in the root skill and route deeper questions into the matching sub-skill.
