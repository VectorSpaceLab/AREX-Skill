---
name: trees-phylogeny
description: "Use scikit-bio TreeNode objects, Newick trees, distance-based tree
  construction, tree comparison, consensus, and phylogenetic tree constraints
  for downstream diversity analyses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# trees-phylogeny

Use this sub-skill when an agent needs to read or write Newick, navigate or edit a `TreeNode`, build a phylogeny from a `DistanceMatrix`, compare tree topology or branch lengths, build a majority-rule consensus, or prepare a tree/taxa set for Faith PD or UniFrac.

## Quick Routing

| Need | Start here |
| --- | --- |
| Parse Newick, inspect tips, traverse nodes, root or reroot | [API reference](references/api-reference.md#treenode-core) and [workflows](references/workflows.md#read-inspect-and-write-newick) |
| Keep or remove taxa, prune empty internals, repair polytomies | [workflows](references/workflows.md#prune-shear-and-clean-tree-shape) |
| Construct a tree from pairwise distances | [workflows](references/workflows.md#construct-a-tree-from-a-distancematrix) |
| Improve a candidate tree with NNI | [API reference](references/api-reference.md#construction-and-rearrangement) |
| Compare tree topology or branch lengths | [workflows](references/workflows.md#compare-trees-safely) |
| Derive a majority-rule consensus | [workflows](references/workflows.md#build-a-majority-rule-consensus) |
| Fix errors before Faith PD or UniFrac | [troubleshooting](references/troubleshooting.md#phylogenetic-diversity-and-unifrac-constraints) |

## Boundaries

- This sub-skill covers `skbio.TreeNode` / `skbio.tree.TreeNode`, tree algorithms in `skbio.tree`, and tree/taxa constraints needed by phylogenetic diversity metrics.
- For distance matrix statistics, PERMANOVA/PERMDisp/ANOSIM, and ordination from distance matrices, use `../statistics-ordination/SKILL.md`.
- For actually running alpha/beta diversity metrics such as Faith PD or UniFrac, use `../diversity-tables/SKILL.md`; this sub-skill only prepares and diagnoses the tree and taxa inputs.
- For sequence alignment or sequence-derived distances before tree construction, use `../sequences-alignment/SKILL.md`.

## Public Smoke Check

Run the bundled script from any working directory after installing scikit-bio:

```bash
python scripts/tree_phylogeny_smoke.py
python scripts/tree_phylogeny_smoke.py --algorithm upgma
python scripts/tree_phylogeny_smoke.py --help
```

The script parses a small Newick tree, validates rooted/tip/branch-length expectations, builds a `DistanceMatrix`, runs `nj` or `upgma`, and prints compact JSON. It imports public scikit-bio APIs only.
