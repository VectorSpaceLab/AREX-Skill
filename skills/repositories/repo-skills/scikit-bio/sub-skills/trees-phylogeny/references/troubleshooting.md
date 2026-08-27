# Tree and Phylogeny Troubleshooting

Use these checks before changing a tree. Many scikit-bio tree APIs are permissive because `TreeNode` can represent general hierarchies, while phylogenetic diversity, UniFrac, and some comparison workflows require stricter phylogenetic assumptions.

## Newick Parse Errors

Symptoms:

- `TreeNode.read(...)` raises while reading a string, file, or handle.
- Parsed tree has unexpected nameless tips or internal labels.
- Branch support values appear as names rather than support attributes.

Checks and fixes:

1. Ensure the Newick text ends with `;` and parentheses/commas are balanced.
2. Use `TreeNode.read([newick_text])` for an inline string; use a path or text handle for files.
3. Quote labels containing Newick punctuation such as `:`, `,`, `(`, `)`, or spaces.
4. Inspect `tree.ascii_art()` and `[tip.name for tip in tree.tips()]` immediately after parsing.
5. If internal labels encode support, call `tree.assign_supports()` before filtering by `node.support`.

## Duplicate or Missing Node Names

Symptoms:

- `DuplicateNodeError` during Faith PD, UniFrac, or cache creation.
- `MissingNodeError` or `ValueError` from `find`, `lca`, `shear`, or diversity validation.
- `find(name)` returns an unexpected node when duplicate internal or tip names exist.

Diagnostic snippet:

```python
def name_report(tree, taxa=()):
    tip_names = [tip.name for tip in tree.tips()]
    tree_duplicates = sorted({name for name in tip_names if name and tip_names.count(name) > 1})
    taxa = list(taxa)
    taxa_duplicates = sorted({name for name in taxa if taxa.count(name) > 1})
    missing_taxa = sorted(set(taxa) - set(tip_names))
    return {
        "tip_count": len(tip_names),
        "tree_duplicate_tips": tree_duplicates,
        "taxa_duplicate_ids": taxa_duplicates,
        "taxa_missing_from_tree": missing_taxa,
    }
```

Fix direction:

- If duplicates are technical artifacts, rename tips before analysis.
- If duplicates represent merged observations, aggregate the table first and keep one tree tip per taxon ID.
- If taxa are missing because the tree is larger/smaller than the table, decide whether to fail strictly or use `tree.shear(set(taxa), strict=False)` and report the missing IDs.
- Extra unobserved tips in a tree are acceptable for Faith PD and UniFrac, but supplied taxa absent from the tree are not.

## Phylogenetic Diversity and UniFrac Constraints

Faith PD and UniFrac execution belongs in `../diversity-tables/SKILL.md`, but tree preparation belongs here.

Common validation failures and fixes:

| Problem | Why it fails | Actionable fix |
| --- | --- | --- |
| Unrooted tree | Tests expect Faith PD and UniFrac to reject a root with more than two children. | Use biologically justified `root_by_outgroup(...)`, branch-length-based `root_at_midpoint()`, or supply a rooted tree. |
| Missing branch lengths | Phylogenetic diversity and weighted UniFrac need branch lengths to accumulate diversity along observed paths. | Reconstruct with `nj`, `upgma`, `gme`, or `bme`, or annotate all non-root branches with defensible lengths. Do not silently set all lengths to one unless the analysis explicitly allows it. |
| Duplicate tree tips | Diversity validation needs unique tree tip IDs. | Rename, aggregate, or remove duplicate taxa; verify with `[tip.name for tip in tree.tips()]`. |
| Duplicate taxa IDs | Count vectors map by taxa ID. | Deduplicate/aggregate the count table so each column/feature ID appears once. |
| Supplied taxon absent from tree | The metric cannot attach counts to a branch path. | Add the missing tip with a valid branch length, relabel synonyms, or drop/recompute the table feature and report the omission. |
| Vector length mismatch | Count vector and taxa list must align positionally. | Reindex counts to the taxa list before calling diversity APIs. |

Safe preparation pattern for a missing taxon in a UniFrac table:

```python
taxa = ["OTU1", "OTU2", "OTU_missing"]
tree_tips = {tip.name for tip in tree.tips()}
missing = sorted(set(taxa) - tree_tips)
if missing:
    # Preferred: correct IDs or obtain a tree containing these taxa.
    # Fallback: drop missing taxa from both count vectors and taxa only when that is acceptable for the study.
    keep = [idx for idx, taxon in enumerate(taxa) if taxon in tree_tips]
```

## DistanceMatrix ID Mismatch

Symptoms:

- `nni(tree, dm)` raises because tree taxa and distance matrix IDs differ.
- Tree construction produces unexpected tip labels.
- Comparisons or downstream table joins fail after construction.

Checks:

```python
tree_taxa = set(tree.subset())
dm_taxa = set(dm.ids)
only_tree = sorted(tree_taxa - dm_taxa)
only_dm = sorted(dm_taxa - tree_taxa)
```

Fix direction:

- Make `DistanceMatrix(..., ids=...)` match intended taxon labels exactly.
- Reorder is fine; `DistanceMatrix` stores IDs, and UniFrac tests show taxa order can differ when IDs are supplied correctly.
- For `nni`, prune or relabel the tree and rebuild the distance matrix to the same ID set before calling.
- For `nj`, `gme`, `bme`, and `upgma`, confirm IDs are unique before construction because they become tip names.

## Tree Comparison Preconditions

Symptoms:

- RF distances are zero because no taxa are shared.
- Weighted/topological comparisons disagree due to rooted versus unrooted interpretation.
- Branch-length distances are unexpectedly small because missing lengths were treated as zero.

Checklist:

1. Compute `tip_sets = [set(tree.subset()) for tree in trees]`.
2. Decide whether to compare all trees on `set.intersection(*tip_sets)` or pairwise intersections with `shared_by_all=False`.
3. Require at least two shared named tips for a meaningful path comparison and enough shared taxa for the topology question being asked.
4. Choose rooted semantics: `rooted=True` compares rooted clades/subsets, `rooted=False` compares unrooted bipartitions.
5. For `wrf_dists` or `path_dists(use_length=True)`, list nodes with `length is None` before trusting the result.
6. Use unique comparison IDs; duplicate `ids` raise `ValueError`.

Recovery pattern for mismatched tip sets:

```python
shared = tree_a.subset() & tree_b.subset()
if len(shared) < 2:
    raise ValueError("Relabel or add taxa before comparing; fewer than two shared tips.")
pruned_a = tree_a.shear(shared, strict=True)
pruned_b = tree_b.shear(shared, strict=True)
rf = pruned_a.compare_rfd(pruned_b, rooted=False)
```

If a mismatch is a synonym issue, relabel first and then re-run duplicate checks; pruning before relabeling can discard useful taxa.

## NNI and Bifurcation Failures

Symptoms:

- `nni(tree, dm)` raises about tree shape or taxa mismatch.
- A tree with a root tip or multifurcation cannot be rearranged.

Fix direction:

1. Check `tree.subset() == set(dm.ids)`.
2. Check `tree.is_bifurcating(strict=True, include_self=False)`.
3. If needed, work on `candidate = tree.copy()`, then call `candidate.bifurcate(include_self=True)` and `candidate.prune()`.
4. Avoid a tree representation where a tip is the root node with one child; reroot on an internal branch or use a different construction as the candidate.
5. Call `nni(candidate, dm, balanced=True)` for BME-style optimization or `balanced=False` for OLS/FastNNI style optimization.
