# Bio.Phylo tree reference

This reference covers core Biopython tree I/O, traversal, querying, and modification with `Bio.Phylo`. It is offline-safe and uses only public Biopython APIs.

## Verified public signatures and formats

Installed public signatures:

```text
Phylo.parse(file, format, **kwargs)
Phylo.read(file, format, **kwargs)
Phylo.write(trees, file, format, **kwargs)
Phylo.convert(in_file, in_format, out_file, out_format, parse_args=None, **kwargs)
```

Verified installed tree I/O formats:

```text
newick, nexus, phyloxml, nexml, cdao
```

Format notes:

- `newick` is compact and common for topology, tip/internal labels, and branch lengths.
- `nexus` is useful when tree data is embedded in a larger NEXUS file.
- `phyloxml` and `nexml` preserve richer annotations than Newick.
- `cdao` support is optional-dependency sensitive in many installations; if RDF-related imports fail, choose another tree format unless CDAO is required.

## Read, parse, write, convert

Use `read` when exactly one tree is expected and `parse` when a file may contain multiple trees.

```python
from io import StringIO
from Bio import Phylo

handle = StringIO("((Alpha:0.1,Beta:0.2)Inner:0.3,Gamma:0.4)Root;")
tree = Phylo.read(handle, "newick")
assert tree.root.name == "Root"
assert tree.count_terminals() == 3
```

`Phylo.read` raises `ValueError` if the file contains zero or multiple trees. In that case, use `list(Phylo.parse(...))` and decide how to handle each tree.

Writing one tree:

```python
from io import StringIO
from Bio import Phylo

out = StringIO()
count = Phylo.write(tree, out, "newick")
assert count == 1
```

`Phylo.write` accepts a single `Tree`, a `Clade`, or an iterable of trees. `Phylo.convert` is parse-then-write and shares the same format limitations.

## Tree and Clade model

Core objects:

- `Tree`: root-level tree container with attributes such as `root`, `rooted`, `id`, and `name`.
- `Clade`: node/subtree object with `name`, `branch_length`, and `clades` children.
- `tree.root`: the root clade; most traversal/query methods are available on both `Tree` and `Clade` through a shared mixin.

Common introspection:

```python
terminals = tree.get_terminals()
nonterminals = tree.get_nonterminals()
all_clades_preorder = list(tree.find_clades(order="preorder"))
all_clades_level = list(tree.find_clades(order="level"))
leaf_names = [clade.name for clade in terminals]
```

Traversal order options are:

- `"preorder"`: depth-first, parent before children; default.
- `"postorder"`: depth-first, children before parent.
- `"level"`: breadth-first level order.

## Searching and target matching

`find_clades`, `find_elements`, `find_any`, and related methods support several target styles:

```python
# Exact-looking string target is interpreted as a regular-expression match
alpha = tree.find_any(name="Alpha")
inner = tree.common_ancestor("Alpha", "Beta")
leaves = list(tree.find_clades(terminal=True))
short_named = list(tree.find_clades(lambda c: c.name and len(c.name) <= 5))
```

Search tips:

- String attribute matches use regular-expression semantics, so escape special regex characters when matching literal names from user data.
- `terminal=True` restricts to leaves; `terminal=False` restricts to internal clades.
- Float attribute searches are intentionally limited; search by boolean or a callable, then filter manually when comparing nonzero floats.
- `find_clades` usually returns the clade you want. `find_elements` can return richer annotation elements in formats such as phyloXML.

## Distances and topology queries

Useful methods:

```python
assert tree.count_terminals() == len(tree.get_terminals())
ancestor = tree.common_ancestor("Alpha", "Beta")
path = tree.get_path("Alpha")
between = tree.trace("Alpha", "Gamma")
depths = tree.depths()                       # branch-length depths
unit_depths = tree.depths(unit_branch_lengths=True)
distance = tree.distance("Alpha", "Beta")
monophyletic = tree.is_monophyletic("Alpha", "Beta")
total = tree.total_branch_length()
```

`common_ancestor` raises if a target is absent. `distance(target)` is root-to-target distance; `distance(target1, target2)` is path distance between two targets. Branch lengths may be `None`; distance methods ignore `None` branch lengths where appropriate.

## Safe tree modification

Most modification methods mutate the tree in place. Copy first if the original topology must be retained.

```python
import copy

working = copy.deepcopy(tree)
working.ladderize()              # sort clades by terminal count
parent = working.prune("Gamma")  # remove a terminal clade
```

Common mutation methods:

- `ladderize(reverse=False)`: sort child clades by number of terminals.
- `prune(target)`: remove a terminal clade; may collapse a bifurcation and alter branch lengths.
- `collapse(target)` / `collapse_all(...)`: remove internal nodes while preserving descendants; branch lengths may be redistributed.
- `root_with_outgroup(...)`: reroot in place using one or more target clades.
- `root_at_midpoint()`: reroot using midpoint heuristics.
- `split(n=2, branch_length=1.0)`: add child clades to the current clade.

After modifying a tree, assert invariants that matter to the downstream task, such as terminal names, terminal count, monophyly, total branch length, or expected root name.

## Visualization and graph conversion

Base-safe display:

```python
from Bio import Phylo
Phylo.draw_ascii(tree)
```

`Phylo.draw`, `Phylo.to_networkx`, and `Phylo.to_igraph` require optional graphics/graph dependencies. Treat missing optional packages as non-blocking unless the user specifically asked for rendering or graph export.

## Optional phylogeny tools

Biopython includes parsers and interfaces around some external phylogeny tooling, but external programs are not part of the base package. If a task mentions PAML, command-line tree builders, external aligners, or visualization backends, first identify the required executable/package, check installation, and keep the default Biopython tree parse/traverse/edit path offline.
