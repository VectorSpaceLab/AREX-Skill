---
name: domain-routing
description: "Choose a ClawBio skill or short skill chain from catalog metadata,
  file shape, headers, and biological intent."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ClawBio domain routing

Use this sub-skill when a request names no exact ClawBio capability, supplies a data file, asks which skill to use, or may require a multi-step analysis. This is a routing contract, not a substitute for a specialist skill's scientific method.

## Load the right detail

- Read [catalog-and-routing.md](references/catalog-and-routing.md) for catalog semantics, routing order, aliases, and data-shape decisions.
- Read [domain-families.md](references/domain-families.md) for the family map and common chains.
- Read [troubleshooting.md](references/troubleshooting.md) before reporting a missing, ambiguous, stale, or unsafe route.
- For execution and flag policy, hand off to [core-runner](../core-runner/SKILL.md).
- For Nextflow and other multi-stage wrappers, hand off to [pipelines-integrations](../pipelines-integrations/SKILL.md).
- For a quick metadata lookup, run the bundled read-only [catalog query script](scripts/catalog_query.py) with an explicit catalog path.

## Operating procedure

1. **Normalize the request.** Record the biological goal, input paths, expected output, reference/build if stated, and whether the user requests one analysis or a chain. Do not infer a clinical diagnosis or silently add a downstream step.
2. **Inspect before routing.** Confirm that each path exists and inspect a small header or metadata sample locally. Extension alone is not enough: distinguish raw counts from finished DE tables, a VCF from a DTC genotype text file, raw scRNA counts from a processed `.h5ad`, and a bulk FASTQ from a single-cell FASTQ bundle. Do not upload genomic payloads.
3. **Search the catalog.** Match `trigger_keywords`, `tags`, description, input shape, and `chaining_partners`; use `maturity_evidence.cli_registered` to determine whether a `cli_alias` is actually runnable through `clawbio.py run`. The catalog is discovery metadata, not proof that every entry is executable.
4. **Prefer the narrowest route.** A strong explicit biological intent beats a generic extension route. If the user asks for a named registered alias, preserve it unless the input contract contradicts it. If two routes remain plausible, ask one focused clarification and show the competing interpretations.
5. **Choose an invocation form.** For a registered skill, use its CLI alias, not necessarily its directory name. For an agent-readable-only entry, use its `SKILL.md` as operating guidance or explain that it is not exposed through `clawbio run`; never invent an alias. Apply the runner's allow-listed flags; do not bypass `allowed_extra_flags`.
6. **Plan, then execute.** For chains, state each handoff and the expected artifact (for example, counts TSV or `integrated.h5ad`) before running. The runner and pipeline integration skills own command construction, dependency checks, overwrite checks, and reproducibility details.
7. **Report uncertainty.** If the catalog is missing or stale, distinguish a routing suggestion from a verified executable route. If headers are malformed, the path is missing, or a required backend is unavailable, stop at the appropriate preflight and give a concrete fix.

## Fast routing rules

- VCF/VCF.GZ + annotation/ClinVar/VEP/gnomAD: prefer the agent-readable variant annotation guidance; VCF/VCF.GZ + population diversity: registered `equity`; an rsID association/PheWAS/eQTL question: registered `gwas`; VCF + PRS: registered `just-prs` or `prs` according to the requested model/input contract.
- 23andMe/AncestryDNA raw text + drug, CYP, CPIC, or pharmacogenomics: registered `pharmgx`; a unified personal report may continue to registered `profile`.
- FASTQ/BAM/CRAM + QC or alignment: `seq-wrangler` is agent-readable-only in the inspected catalog; use a registered `rnaseq-pipeline`, `scrnaseq-pipeline`, or `sarek-pipeline` only when the request matches that upstream pipeline and samplesheet contract.
- FASTA + generic sequence/protein metrics: registered `analyze-fasta`; FASTA plus promoter, splice, enhancer, chromatin, expression, or gene-annotation intent: the corresponding `gi-*` agent-readable skill. PDB/CIF or structure comparison: `struct-predictor` guidance.
- `.h5ad` or 10x Matrix Market: registered `scrna` for QC, clustering, markers, annotation, and contrasts; `scrna-embedding` first for scVI/scANVI/latent/integration/batch correction, then hand its latent artifact to `scrna` when downstream markers or clustering are requested.
- CSV/TSV: inspect headers. Count matrix plus sample metadata and a DE request routes to registered `rnaseq`; finished DE/marker columns route to registered `diffviz`; ancestry/population columns plus diversity intent route to `equity`. Never treat every tabular file as counts.
- Image/PDF figure + digitization or extraction: registered `data-extract`; proteomics platform tables route by platform (`affprot` for Olink/SomaScan; proteomics-specific agent-readable guidance for MaxQuant/DIA-NN or clocks).

## Safety checkpoint

Before selecting a route, inspect VCF header/version and sample columns, FASTA headers, FASTQ read structure, BAM/CRAM metadata, Matrix Market companion files, `.h5ad` `obs`/`var`/`layers`/`obsm` keys, and CSV/TSV column names. Preserve genome build and whether data are raw, processed, or synthetic. Treat a malformed or contradictory header as `needs_input`, not as permission to guess.

## Output of this sub-skill

Return a compact routing record: normalized intent, inspected shape/header signals, candidate names and aliases, registered/agent-readable status, selected route or clarification question, planned chain and artifact handoffs, maturity caveats, and any safety or stale-catalog warning. Then hand off execution to the relevant operating skill; do not run specialist analyses from this router.
