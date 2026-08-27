# DiG overview

Distributional Graphormer (DiG) is a research-code subtree that sits beside the
core Graphormer fairseq user-dir package. It is not the same thing as the core
Graphormer property-prediction stack.

## Subprojects

| Subproject | Main workflow | Typical assets | Main caveat |
| --- | --- | --- | --- |
| `catalyst-adsorption/` | training, sampling, density estimation | OC20-derived LMDB data, checkpoints | external data and long GPU jobs |
| `property-guided/` | training and property-guided structure sampling | RSS carbon LMDB data, checkpoints | external data and long GPU jobs |
| `protein/` | protein conformation inference | AlphaFold-style feature pickles, FASTA, checkpoint | GPU preferred and a first-run SO(3) build delay |
| `protein-ligand/` | single-datapoint sampling and full evaluation | dataset tarball, checkpoints, Docker image | external assets and long evaluation time |

## Environment pattern

The DiG subtree is split into its own environments or dependency sets. The
validated source material uses different Python versions and packaging choices
than the core Graphormer property-prediction stack.

Rules of thumb:

- treat the DiG subtree as optional and research-only
- expect external downloads for datasets and checkpoints
- prefer command rendering and preflight notes before a real run
- do not assume the core Graphormer environment automatically covers DiG

## What the command renderer helps with

- preserving the parameter names from the source shell scripts
- making GPU counts, save directories, and data roots explicit
- showing when a workflow is only a sketch because the source code itself is
  the executable contract

## Where to look next

- [Catalyst and property-guided workflows](catalyst-and-property-guided.md)
- [Protein workflows](protein-workflows.md)
- [Protein-ligand workflows](protein-ligand-workflows.md)
- [Troubleshooting](troubleshooting.md)
