---
name: distributional-graphormer
description: "Routes Distributional Graphormer (DiG) catalyst, property-guided,
  protein, and protein-ligand workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Distributional Graphormer

Use this sub-skill for the `distributional_graphormer/` research-code subtree:
DiG catalyst adsorption, property-guided generation, protein conformation
sampling, and protein-ligand workflows.

This sub-skill is mostly a routed reference and command-rendering layer. The
DiG subprojects depend on external datasets, checkpoints, and in several cases
long GPU jobs or Docker, so the goal here is to make the workflows reviewable
and explicit without pretending they are lightweight package workflows.

## Start here

- [DiG overview](references/dig-overview.md)
- [Catalyst and property-guided workflows](references/catalyst-and-property-guided.md)
- [Protein workflows](references/protein-workflows.md)
- [Protein-ligand workflows](references/protein-ligand-workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Command renderer](scripts/build_dig_command.py)

## Route elsewhere

- Core Graphormer property-prediction training lives in
  [fairseq-training](../fairseq-training/SKILL.md).
- Core Graphormer custom dataset handling lives in
  [datasets-and-customization](../datasets-and-customization/SKILL.md).
- Core Graphormer pretrained evaluation and checkpoint loading lives in
  [pretrained-and-evaluation](../pretrained-and-evaluation/SKILL.md).
- Graphormer fairseq model/task/criterion extension lives in
  [model-extension](../model-extension/SKILL.md).

## What this sub-skill does

- summarizes the catalyst adsorption and property-guided DiG command families
- records the protein inference CLI contract and output files
- records the protein-ligand evaluation and Docker/data contracts
- renders reviewable command sketches so a later Researcher can decide whether
  a full run is feasible

## What this sub-skill does not do

- it does not download SAS-token data or checkpoints
- it does not launch distributed training or evaluation jobs
- it does not hide the fact that some workflows are source-only or long-running
