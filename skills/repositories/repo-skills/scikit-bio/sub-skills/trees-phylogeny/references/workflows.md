# Tree and Phylogeny Workflows

These recipes are self-contained and use only public scikit-bio APIs. They are intentionally small enough to adapt into agent-generated scripts without depending on source repository files.

## Read, Inspect, and Write Newick

```python
from io import StringIO
from skbio import TreeNode

newick = "((OTU1:0.5,OTU2:0.5):0.5,(OTU3:0.7,OTU4:0.9):0.4)root;"
tree = TreeNode.read([newick])

summary = {
    "root": tree.name,
    "is_root": tree.is_root(),
    "root_child_count": len(tree.children),
    "tips": [tip.name for tip in tree.tips()],
    "tip_count": tree.count(tips=True),
    "has_all_tip_lengths": all(tip.length is not None for tip in tree.tips()),
}

print(tree.ascii_art())
print(str(tree))
```

Checklist:

1. Parse from `TreeNode.read([newick_text])`, a file path, or a text handle.
2. Inspect tips with `tree.tips()` and internal nodes with `tree.non_tips()`.
3. Treat `tree` as the root node; any node can represent a subtree.
4. Write with `tree.write(path_or_handle)` or `str(tree)`.

## Navigate a Clade

```python
tree = TreeNode.read(["((A:1,B:2)primates:3,(C:4,D:5)other:6)root;"])
primates = tree.find("primates")
ancestor = tree.lca(["A", "B"])

assert primates is ancestor
assert primates.subset() == frozenset({"A", "B"})
assert tree.find("A").parent.name == "primates"
```

Useful navigation methods:

- Use `find(name)` for one named node and `find_all(name)` if duplicate internal names are possible.
- Use `lca(names_or_nodes)` when clade-defining taxa are known but the internal node name is not.
- Use `subset()` for rooted clades and `bipart()` / `biparts()` for unrooted branch splits.

## Prune, Shear, and Clean Tree Shape

Use `shear` to keep only a target taxon set and `prune` to clean unnecessary internals.

```python
tree = TreeNode.read(["((A:1,B:2)C:3,(D:4,E:5)F:6,G:7)root;"])
wanted = {"A", "E", "G", "missing"}

kept = tree.shear(wanted, strict=False, prune=True)
kept_tips = kept.subset()
missing = wanted - kept_tips

if missing:
    print("Taxa absent from tree:", sorted(missing))

assert kept_tips == {"A", "E", "G"}
```

Guidelines:

- Prefer `strict=True` when absence indicates a data error; use `strict=False` when intentionally intersecting a tree with a table.
- Call `copy()` first when preserving the original tree matters.
- After manual `remove`, `append`, or `extend` operations, call `prune()` if single-child internal nodes should be collapsed.
- Use `bifurcate()` before algorithms that require a strict binary topology, then re-check with `is_bifurcating(strict=True, include_self=False)`.

## Root or Unroot Deliberately

Distance-based construction such as `nj`, `gme`, and `bme` usually returns unrooted trees. Root before methods that require rooted trees, and unroot only when the downstream comparison should ignore direction.

```python
tree = TreeNode.read(["((out:0.5,A:1.0):0.4,(B:1.1,C:1.2):0.6)root;"])
rooted_by_outgroup = tree.root_by_outgroup(["out"])
midpoint_rooted = tree.root_at_midpoint()
unrooted = rooted_by_outgroup.copy().unroot()
```

Rules of thumb:

- Use `root_by_outgroup` when biology or metadata identifies an outgroup.
- Use `root_at_midpoint` when branch lengths exist and no outgroup is available.
- For unrooted RF comparison, pass `rooted=False` rather than changing the original tree unless you need an unrooted output tree.

## Construct a Tree from a DistanceMatrix

For creating or analyzing distance matrices themselves, use `../statistics-ordination/SKILL.md`. Once you have a `DistanceMatrix`, tree construction is direct:

```python
from skbio import DistanceMatrix
from skbio.tree import nj, upgma, gme, bme, nni

data = [
    [0, 5, 9, 9, 8],
    [5, 0, 10, 10, 9],
    [9, 10, 0, 8, 7],
    [9, 10, 8, 0, 3],
    [8, 9, 7, 3, 0],
]
ids = list("abcde")
dm = DistanceMatrix(data, ids)

nj_tree = nj(dm)                       # unrooted; negative lengths zeroed by default
upgma_tree = upgma(dm)                 # rooted ultrametric
wpgma_tree = upgma(dm, weighted=True)  # weighted UPGMA variant
gme_tree = gme(dm)                     # scalable unrooted minimum evolution
bme_tree = bme(dm)                     # balanced minimum evolution

candidate = TreeNode.read(["((a,b),(c,d),e);"])
if not candidate.is_bifurcating(strict=True, include_self=False):
    candidate = candidate.copy()
    candidate.bifurcate(include_self=True)
    candidate.prune()
improved = nni(candidate, dm, balanced=True)
```

Construction diagnostics:

- `DistanceMatrix` IDs must be unique and match intended tip names.
- `nj` requires at least three taxa.
- Use `neg_as_zero=False` only when negative branch lengths are meaningful for diagnosis and downstream code can tolerate them.
- Use `inplace=True` for `nj` only when memory matters and you no longer need the original matrix content unchanged.
- `nni` requires tree taxa to match distance matrix IDs and a strictly bifurcating tree, except for the unsupported case where a tip is itself the root.

## Compare Trees Safely

```python
from skbio import TreeNode
from skbio.tree import path_dists, rf_dists, wrf_dists

trees = [TreeNode.read([text]) for text in [
    "(((a,b),c),d,e);",
    "((a,(b,c)),d,e);",
    "((a,b),(c,d),e);",
]]

all_tip_sets = [set(t.subset()) for t in trees]
shared = set.intersection(*all_tip_sets)
if not shared:
    raise ValueError("No shared taxa across trees; compare after relabeling or pruning.")

rf = rf_dists(trees, ids=["t1", "t2", "t3"], rooted=False)
rf_rooted = rf_dists(trees, rooted=True)
```

Choose the comparison:

- Topology only: `tree1.compare_rfd(tree2)` or `rf_dists([...])`.
- Topology plus branch lengths on matching splits: `tree1.compare_wrfd(tree2)` or `wrf_dists([...])`.
- Tip-to-tip path length differences: `tree1.compare_cophenet(tree2, metric="euclidean")` or `path_dists([...])`.
- Large trees with many shared tips: use `path_dists(sample=N, shuffler=seed_or_callable)` for bounded comparisons.

Recover from mismatched tip sets:

```python
t1 = TreeNode.read(["((a,b),(c,d));"])
t2 = TreeNode.read(["((a,b),(c,x));"])
shared = t1.subset() & t2.subset()

if len(shared) < 2:
    raise ValueError("Need at least two shared named tips for a meaningful comparison.")

p1 = t1.shear(shared, strict=True)
p2 = t2.shear(shared, strict=True)
distance = p1.compare_rfd(p2, rooted=False)
```

If mismatches are due to synonyms rather than absent data, relabel tips before pruning:

```python
rename = {"x": "d"}
for tip in t2.tips():
    tip.name = rename.get(tip.name, tip.name)
```

## Build a Majority-Rule Consensus

```python
from skbio import TreeNode
from skbio.tree import majority_rule

trees = [
    TreeNode.read(["((a,b),(c,d),(e,f));"]),
    TreeNode.read(["(a,(c,d),b,(e,f));"]),
    TreeNode.read(["((c,d),(e,f),b);"]),
    TreeNode.read(["(a,(c,d),(e,f));"]),
]
consensus_trees = majority_rule(trees, cutoff=0.5)

for consensus in consensus_trees:
    for node in consensus.non_tips():
        print(sorted(node.subset()), node.support)
```

Notes:

- `weights` must match the number of input trees.
- `cutoff` is a fraction of total weight; clades with support at or below the threshold are dropped.
- More than one consensus tree can be returned when supported clades do not connect all tips.

## Prepare a Tree for Faith PD or UniFrac

For running the metrics, use `../diversity-tables/SKILL.md`. Before calling them, validate the tree and taxa:

```python
def diagnose_phylo_inputs(tree, taxa):
    taxa = list(taxa)
    tip_names = [tip.name for tip in tree.tips()]
    duplicate_tips = sorted({name for name in tip_names if tip_names.count(name) > 1})
    duplicate_taxa = sorted({name for name in taxa if taxa.count(name) > 1})
    missing_taxa = sorted(set(taxa) - set(tip_names))
    missing_lengths = sorted(
        node.name or "<internal>"
        for node in tree.traverse(include_self=False)
        if node.length is None
    )
    rooted = len(tree.children) == 2
    return {
        "duplicate_tips": duplicate_tips,
        "duplicate_taxa": duplicate_taxa,
        "missing_taxa": missing_taxa,
        "missing_branch_lengths": missing_lengths,
        "rooted": rooted,
    }
```

Required constraints distilled from scikit-bio diversity tests:

- Tree tip names must be unique for phylogenetic diversity validation.
- Taxa IDs supplied with count vectors must be unique and the same length as the count vector.
- Every supplied taxon must be present as a tree tip; extra unobserved tree tips are accepted by Faith PD and UniFrac tests.
- The tree must be rooted for Faith PD and UniFrac validation.
- Non-root branches needed by the metric must have branch lengths; missing lengths raise validation errors.
