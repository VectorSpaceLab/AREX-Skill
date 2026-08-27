---
name: clawbio
description: "Use ClawBio for local-first bioinformatics agent workflows:
  install and run its skill library, route genomic or omics inputs, create
  reproducible reports, connect optional MCP or Nextflow integrations, and
  author or validate skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ClawBio

ClawBio is a Python package and skill library for reproducible, local-first
bioinformatics workflows. Use this repo skill to operate the platform and
choose its specialist skills; do not improvise scientific thresholds or treat
an output as a clinical diagnosis.

## Start here

- For install, `clawbio list/run/upload`, Python APIs, profiles, outputs, or
  replay metadata, read [core-runner](sub-skills/core-runner/SKILL.md).
- For a natural-language biological request, an input file, or a multi-step
  chain, read [domain-routing](sub-skills/domain-routing/SKILL.md) before
  choosing an alias.
- For MCP, messaging/web adapters, provider credentials, or nf-core/Nextflow,
  read [pipelines-integrations](sub-skills/pipelines-integrations/SKILL.md).
- For creating or changing a skill, catalog registration, tests, demos, or
  `INTENTS.json`, read [skill-authoring](sub-skills/skill-authoring/SKILL.md).
- For replay/checksum review, benchmark status, action contracts, privacy, or
  security filtering, read [validation-safety](sub-skills/validation-safety/SKILL.md).
- Read [troubleshooting](references/troubleshooting.md) when the failure spans
  more than one route. Use [provenance](references/repo-provenance.md) before
  deciding whether this graph is stale for a repository checkout. For a
  read-only package/API/CLI probe, run [check_environment.py](scripts/check_environment.py)
  after reading its help.

## Public setup

For ordinary users, install the public distribution with Python 3.11 or newer:

```bash
python -m pip install clawbio
python -c "import clawbio; print(clawbio.__version__)"
clawbio list
```

The optional MCP extra is `clawbio[mcp]`. It is deliberately separate from the
base install. A source checkout may use the repository's documented `uv sync`
workflow, but a published skill must not assume that checkout exists.

## Platform operating rules

1. Identify the goal, input format/build, desired artifact, and whether the
   request is demo, local-file, or profile based. Inspect small headers locally;
   do not upload raw genomic data just to determine its type.
2. Route to the narrowest catalog entry. Catalog metadata distinguishes the
   registered CLI aliases from agent-readable-only `SKILL.md` contracts; do not
   invent a runnable alias for a spec-only skill.
3. Execute registered skills through `clawbio run` or the stable Python runner,
   not by bypassing the runner's per-skill flag allowlist. Use a fresh writable
   output directory and inspect structured results as well as exit codes.
4. Preserve the local-first boundary. External APIs, cloud datasets, MCP local
   file access, bots, credentials, containers, Nextflow, and large references
   are explicit opt-ins with separate failure and provenance handling.
5. Keep `PASS`, `SKIP`, `FAIL`, stale/expired action, and unavailable-backend
   states distinct. A successful import or demo does not prove a scientific
   method, external service, GPU, or clinical interpretation.
6. Reports must retain the package's research/education disclaimer. Do not give
   medical diagnoses or treatment advice from a ClawBio result.

## Common entry points

```bash
clawbio list
clawbio run <registered-alias> --demo
clawbio run <registered-alias> --input sample.ext --output results
clawbio upload --input genotype.txt --patient-id PT001
clawbio run profile --profile profiles/PT001.json --output profile-results
clawbio mcp
```

The exact flags and virtual `full-profile` behavior belong to
[core-runner](sub-skills/core-runner/SKILL.md). Use [domain-routing](sub-skills/domain-routing/SKILL.md)
for aliases and chains, not this short list as a substitute for input
inspection.

## Freshness and scope

This graph is versioned against the source snapshot in
[repo-provenance.md](references/repo-provenance.md). If the package version,
public entry points, catalog, or major evidence paths changed, refresh the repo
skill before relying on detailed claims. Review-only test cases and reports are
kept outside this runtime directory; they are not inputs to ordinary ClawBio
runs.
