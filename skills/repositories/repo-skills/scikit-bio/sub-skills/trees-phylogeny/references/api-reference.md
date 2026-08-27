# Trees and Phylogeny API Reference

This reference distills the public tree APIs exercised by scikit-bio tree docs and tests. Examples assume:

```python
from io import StringIO
from skbio import DistanceMatrix, TreeNode
from skbio.tree import bme, gme, majority_rule, nj, nni, path_dists, rf_dists, upgma, wrf_dists
```

## TreeNode Core

`TreeNode(name=None, length=None, support=None, parent=None, children=None)` creates a tree node. A complete tree is represented by its root node.

| Task | API | Notes |
| --- | --- | --- |
| Read Newick | `TreeNode.read(source)` | `source` can be a file path/handle or a list/iterable containing Newick text, e.g. `TreeNode.read(["((A:1,B:2)C:3,D:4)root;"])`. |
| Write Newick | `tree.write(destination)` or `str(tree)` | `str(tree)` includes a trailing newline; branch lengths and support labels are serialized when present. |
| Display | `tree.ascii_art(show_internal=True, compact=False)` | Good for debugging shape without relying on child order in Newick. |
| Copy | `tree.copy(deep=False)` | Use before destructive edits such as `shear(..., inplace=True)`, `prune()`, `unroot()`, or rerooting. |
| Root identity | `tree.is_root()`, `node.parent`, `node.children` | Every `TreeNode` knows its parent except the root. |
| Tip/internal identity | `node.is_tip()` | Tips usually represent taxa/feature IDs. |
| Count | `tree.count(tips=False)` | Use `tips=True` for number of taxa/tips. |
| Traverse | `tree.traverse()`, `tree.preorder()`, `tree.postorder()` | `include_self=True` by default for traversal. |
| Iterate by type | `tree.tips()`, `tree.non_tips()` | `tips()` defaults to excluding `self` unless `self` is a tip. |
| Lookup | `tree.find(name)`, `tree.find_all(name)` | `find` caches lookups; duplicate names can make lookup ambiguous for downstream tools. |
| Cache control | `tree.create_caches()`, `tree.has_caches()` | Mutation APIs usually clear caches unless `uncache=False` is explicitly used. |

Minimal parsing pattern:

```python
tree = TreeNode.read(["((A:1,B:2)C:3,D:4)root;"])
tips = [node.name for node in tree.tips()]
lengths = {node.name: node.length for node in tree.traverse() if node.name}
```

## Navigation, Editing, and Shape

| Task | API | Notes |
| --- | --- | --- |
| Lowest common ancestor | `tree.lca(["A", "B"])` | Names or nodes may be supplied. |
| Tip set below node | `node.subset(include_self=False)` | Returns a frozen set of tip names below an internal node; for a tip, pass `include_self=True` if you need its own name. |
| Rooted clade sets | `tree.subsets(...)` | Used by rooted topology comparisons. Options include `within`, `include_full`, `include_tips`, and `map_to_length`. |
| Unrooted split | `node.bipart()` | Returns the smaller side of the branch split; root has an empty bipartition. |
| Unrooted split set | `tree.biparts(...)` | Used by unrooted topology comparisons. |
| Attach node(s) | `parent.append(node)`, `parent.extend(nodes)` | Reparents existing nodes automatically. |
| Detach node | `parent.remove(node)` | Returns `True` when removed. |
| Prune empties | `tree.prune()` | Removes unnecessary single-child internals after edits. |
| Keep selected tips | `tree.shear(names, strict=True, prune=True, inplace=False)` | `strict=False` keeps the intersection when some requested names are absent. |
| Contract branches | `tree.unpack_by_func(func)` | Useful for low-support or short branches; child lengths absorb contracted parent lengths. |
| Force binary shape | `tree.bifurcate(strict=False, include_self=True)` | Use before algorithms that require strict bifurcation; `insert_length=0` can assign lengths to inserted nodes. |

Common safe cleanup after selecting observed taxa:

```python
wanted = {"OTU1", "OTU2", "OTU4"}
subtree = tree.shear(wanted, strict=False, prune=True)
missing = wanted - subtree.subset()
```

## Rooting and Branch Lengths

| Task | API | Notes |
| --- | --- | --- |
| Root at tip/node/branch | `tree.root_at(name_or_node, ...)` | Use a copy unless you intend to mutate the original. |
| Root by outgroup | `tree.root_by_outgroup(["outgroup_id"])` | Requires outgroup taxa to be present and meaningful. |
| Midpoint root | `tree.root_at_midpoint()` | Uses branch lengths to place root halfway between distant tips. |
| Unroot | `tree.unroot()` | Collapses rooted direction into an unrooted representation. |
| Is bifurcating | `tree.is_bifurcating(strict=False, include_self=True)` | `strict=True, include_self=False` is useful before `nni`. |
| Patristic distance | `node_a.distance(node_b)` | Sum of branch lengths on the path; missing lengths are treated as zero by some tree distance APIs. |
| Max tip distance | `tree.maxdist()` | Useful as a quick length sanity check. |
| Total length | `tree.total_length()` | Sum of branch lengths under the tree. |
| Tip distance matrix | `tree.cophenet(endpoints=None, use_length=True)` | Returns a `DistanceMatrix` of tip-to-tip path lengths. |

In scikit-bio tree docs, rootedness is implicit: every tree has a root node, but a phylogenetic tree is considered rooted when the root has exactly two children. Many distance-based construction algorithms return unrooted trees that may need midpoint or outgroup rooting before rooted downstream methods.

## Construction and Rearrangement

Input distance matrices are `skbio.DistanceMatrix` instances with IDs matching taxa:

```python
dm = DistanceMatrix(
    [[0, 5, 9, 9, 8],
     [5, 0, 10, 10, 9],
     [9, 10, 0, 8, 7],
     [9, 10, 8, 0, 3],
     [8, 9, 7, 3, 0]],
    ids=list("abcde"),
)
```

| API | Signature facts | Result and constraints |
| --- | --- | --- |
| `nj(dm, neg_as_zero=True, result_constructor=None, inplace=False)` | Neighbor joining. `result_constructor` is deprecated. `inplace=True` may alter the matrix internals. | Returns an unrooted `TreeNode`. Negative branch lengths are set to zero by default. Requires at least three taxa. |
| `upgma(dm, weighted=False)` | UPGMA by default; WPGMA when `weighted=True`. | Returns a rooted ultrametric `TreeNode` with estimated edge lengths. |
| `gme(dm, neg_as_zero=True)` | Greedy minimum evolution. | Scalable unrooted reconstruction; first distance-matrix taxon is placed as a root child; negative lengths zeroed by default. |
| `bme(dm, neg_as_zero=True, **kwargs)` | Balanced minimum evolution. | Unrooted reconstruction; supports parallel tuning through keyword arguments in large runs. |
| `nni(tree, dm, balanced=True, neg_as_zero=True)` | Nearest neighbor interchange on an existing tree. | Tree taxa must match distance matrix IDs; tree may be rooted or unrooted but must be strictly bifurcating, with no tip used as the root node. |

Use `nj` for a classic exact neighbor-joining baseline, `upgma` when an ultrametric/rooted clustering tree is appropriate, `gme` for large datasets, `bme` for balanced minimum evolution, and `nni` to improve an existing bifurcating topology against the same distance matrix.

## Tree Comparison

| API | What it compares | Key options |
| --- | --- | --- |
| `tree1.compare_rfd(tree2, proportion=False, rooted=None)` | Robinson-Foulds topological distance for two trees. | Use `rooted=True` for rooted clades/subsets or `rooted=False` for unrooted bipartitions. |
| `rf_dists(trees, ids=None, shared_by_all=True, proportion=False, rooted=False)` | Pairwise RF distances for many trees. | `shared_by_all=False` recalculates by each pair's shared taxa. |
| `tree1.compare_wrfd(tree2, metric="cityblock", rooted=None, include_tips=True)` | Weighted RF / branch-score style distances using branch lengths. | Metrics include SciPy distance names such as `cityblock`, `euclidean`, `correlation`, and scikit-bio's `unitcorr`. |
| `wrf_dists(trees, ids=None, shared_by_all=True, metric="cityblock", rooted=False, include_tips=True)` | Pairwise weighted RF distances. | Requires a symmetric metric that is zero from a vector to itself. |
| `tree1.compare_cophenet(tree2, metric="unitcorr", use_length=True, sample=None, shuffler=None)` | Distance between tip-to-tip path distance matrices. | Use `metric="euclidean"` for path-length distance; `use_length=False` compares branch counts. |
| `path_dists(trees, ids=None, shared_by_all=True, metric="euclidean", use_length=True, sample=None, shuffler=None)` | Pairwise path-length distances for many trees. | `sample` can bound large comparisons; seed/control with `shuffler`. |

Preconditions for reliable comparison:

- Decide rooted versus unrooted semantics before comparing.
- Check whether trees have identical, pairwise-overlapping, or globally shared tip sets.
- For branch-length comparisons, inspect missing `length` values; some APIs treat missing lengths as zero, which may hide data problems.
- Provide unique `ids` when comparing multiple trees; duplicate IDs raise `ValueError`.

## Consensus

`majority_rule(trees, weights=None, cutoff=0.5, support_attr="support", tree_node_class=TreeNode)` returns a list of consensus trees. Multiple trees may be returned if input clades are disjoint or not all tips are present in all source trees. Consensus support is written to `support_attr` on internal nodes.

```python
consensus = majority_rule(trees, cutoff=0.5)[0]
for node in consensus.non_tips():
    print(node.subset(), node.support)
```

## Exceptions to Recognize

| Exception | Typical cause | Fix direction |
| --- | --- | --- |
| `DuplicateNodeError` | Duplicate tip IDs in a tree when a unique mapping is required. | Rename tips or collapse/aggregate duplicate features before analysis. |
| `MissingNodeError` | Requested name/taxon is absent, or an endpoint has no name. | Reconcile taxa IDs or shear/prune to the intersection. |
| `NoLengthError` | Operation requires branch lengths but a branch has `length is None`. | Supply branch lengths, rerun construction, or set defensible placeholder lengths only if scientifically valid. |
| `NoParentError` | Operation expects parent links but a node is detached/root-like. | Operate from the tree root or attach the node before the operation. |
| `TreeError` | Invalid tree edit such as unpacking the root/tip. | Check `is_root()` and `is_tip()` before editing. |
