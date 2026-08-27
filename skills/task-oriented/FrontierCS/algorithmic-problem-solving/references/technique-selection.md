# Algorithm Technique Selection

Use this catalog after the problem model is trusted and [model and route algorithms](../sub-skills/model-and-route-algorithms/SKILL.md#5-establish-the-operation-and-memory-envelope) has narrowed the admissible solution classes. It supplies algorithm-family questions and rejection conditions, not copy-paste code. Generate only the implementation the problem needs, then compile and test it; static template libraries often contain hidden convention, overflow, memory, or boundary assumptions.

## Plateau gate

If this technique-selection failure occurs after the admission criteria for [plateau escape](../sub-skills/plateau-escape/SKILL.md) are met, do not choose another method family from this catalog yet. Complete that structural review, then use this catalog to compare the returned routes. Before a plateau, use the failed complexity, proof, or brute-test evidence to narrow candidates.

## Family-level routing

Test only families admitted by the contract and feasibility record, stopping when a clean fit is established:

1. **Direct structure:** sorting, counting, prefix/suffix summaries, two pointers, monotonicity, greedy exchange, sweep, or binary search on the answer.
2. **Graph formulation:** connectivity, shortest path, DAG order, SCC, MST, matching, flow/cut, 2-SAT, or difference constraints.
3. **Dynamic programming:** minimal sufficient state, ordering, transition locality, rolling memory, bitset acceleration, and safe dominance.
4. **Algebra, geometry, or strings:** exploit the exact mathematical structure rather than discretizing or searching blindly.
5. **Decomposition:** independent components, separators, treewidth, centroid or block structure, coordinate compression, or offline ordering.
6. **Bounded exponential:** subset DP, meet-in-the-middle, branch-and-bound, iterative deepening, memoized search, or inclusion-exclusion.
7. **General solver:** SAT/SMT, CP-SAT, ILP/MIP, or convex optimization when the environment and model size support it.

Do not infer hardness from a large raw search space or select a sophisticated structure from surface vocabulary. Verify every family-specific precondition against the trusted model and feasibility envelope.

## Fundamental transforms

| Signal | Consider | Reject or modify when |
|---|---|---|
| Feasibility changes monotonically with a value | Binary search on answer plus decision oracle | Predicate is not actually monotone or witness reconstruction is missing |
| Need aggregate over prefixes/ranges | Prefix sums, difference arrays, Fenwick/segment tree, sparse table | Operation/update model does not match associativity/invertibility/idempotence assumptions |
| Ordered values and local comparisons | Sort, coordinate compression, two pointers, monotone stack/queue | Original order is semantic and not recoverable |
| Events become active/inactive in order | Sweep line plus balanced structure | Comparator changes inconsistently or events require dynamic future discovery |
| Many equivalent labels/states | Canonicalization, symmetry breaking, quotient state | Symmetry action does not preserve constraints/objective |
| Offline range queries with cheap endpoint edits | Mo's algorithm and variants | Updates/order dimension makes moves too costly or an online answer is required |
| Offline add/query events across an order | CDQ divide-and-conquer, sweep, BIT | Causality/order or duplicate boundaries are modeled incorrectly |
| Many monotone answer searches share work | Parallel binary search | Per-query predicate is not monotone or batched updates cannot be replayed correctly |

## Graphs and relations

| Need | Default candidates | Critical checks |
|---|---|---|
| Reachability/components | DFS/BFS, DSU, SCC | Directedness, offline vs online updates, recursion depth |
| Nonnegative shortest path | Dijkstra, 0-1 BFS for binary weights, Dial for small integers | Negative edges, overflow, stale queue entries |
| Negative weights | Bellman-Ford, DAG DP, potentials/Johnson | Reachable negative cycles and complexity |
| Connect all vertices cheaply | Kruskal/Prim MST | Graphic structure, disconnected inputs, precision/ties |
| Cardinality pairing | Bipartite matching, Hopcroft-Karp | Graph is bipartite and matching is unweighted |
| Weighted assignment | Hungarian, min-cost flow | Rectangular padding, min/max sign, overflow, sparse scale |
| Capacity/cut constraints | Dinic/push-relabel max flow, min cut | Node splitting, integral capacities, graph size |
| Implication choices | 2-SAT via SCC | Clauses truly have at most two literals; extract assignment correctly |
| Static tree path/subtree | Euler tour, LCA, HLD, DSU-on-tree, centroid decomposition | Choose path updates vs subtree aggregation vs distance decomposition precisely |
| Dynamic forest paths | Link-cut tree or offline rollback/decomposition | Static alternatives are simpler; splay invariants and memory are fully tested |

For a graph reduction, document what vertices and edges mean and prove both directions. Do not use an advanced tree structure merely because the input is a tree.

## Dynamic programming and exact search

| Structure | Consider | Main risk |
|---|---|---|
| Small `n` with subset interactions | Bitmask DP, meet-in-the-middle, subset convolution | `2^n` memory, transition factor, reconstruction |
| Sequence with local choices | Prefix DP, automaton DP, interval DP | Missing sufficient history, invalid transition ordering |
| Tree dependencies | Tree DP, rerooting, small-to-large | Parent/child direction, combining children, stack depth |
| Bounded integer sum | Knapsack, bitset shift/or, sparse frontier | Pseudo-polynomial bound and negative values |
| Partition point recurrence | Divide-and-conquer or Knuth optimization | Required monotonicity/quadrangle inequality must be proved |
| Linear transition envelope | Convex hull trick or Li Chao tree | Min/max convention, slope/query order, equal slopes, overflow |
| Few resources/parameters | Multidimensional DP, Pareto frontier | State explosion and unsafe dominance pruning |
| Hard combinatorial core | Branch-and-bound, memoized DFS, iterative deepening | Weak bound/order, duplicate states, exponential tail |

Always build a small brute oracle before applying a subtle DP optimization. Compare the optimized recurrence against the unoptimized one on random cases.

## Strings

| Need | Candidate | Pitfalls |
|---|---|---|
| One pattern in text | KMP or Z-function | Separator choice, prefix indexing, empty pattern |
| Many patterns | Aho-Corasick | Failure/output links, alphabet memory, counting order |
| Palindromic substrings | Manacher | Odd/even conventions and transformed indices |
| Suffix ordering/LCP queries | Suffix array plus Kasai/RMQ | Rank convention, radix vs comparison cost, arbitrary LCP needs RMQ |
| Online distinct substrings/repetitions | Suffix automaton | Clone transitions, occurrence propagation |
| Fast equality as a filter | Double/randomized hashing | Collision remains possible; adversarial inputs and normalization |

Prefer deterministic algorithms when equality must be certain. If hashing is used in an exact result, combine independent hashes or verify candidates.

## Number theory and algebra

| Need | Candidate | Pitfalls |
|---|---|---|
| Modular powers/inverses | Binary exponentiation, extended GCD, Fermat for prime modulus | Inverse existence, multiplication overflow, negative residues |
| Many primes/factors in a range | Linear/classic/segmented sieve | Memory, handling 0/1, segment offset |
| 64-bit primality/factorization | Deterministic 64-bit Miller-Rabin, Pollard rho/Brent | Use a proven uint64 witness set and `__int128`; retry/cycle handling |
| Congruence system | CRT/generalized CRT | Non-coprime consistency and product overflow |
| Polynomial convolution | NTT/FFT | Modulus/root limits, padding, signed recovery, floating error |
| Binomial modulo prime | Factorials/inverses; Lucas for prime `p` when each base-`p` digit binomial is computable within budget, often because `p` is small enough for factorial tables | Composite modulus needs a different method; `O(p)` tables may be too large |

Do not trust remembered primality witness bounds or root constants without a known source and targeted tests.

For a standalone template request, pin down the supported domain and operations, then verify delicate constants, witness sets, and asymptotic claims against an authoritative source available in the environment. Return only the requested implementation plus focused tests; do not paste an unrelated template catalog.

## Geometry

First choose numeric semantics: exact integer/rational predicates where possible, or floating point with a scale-aware tolerance and consistent boundary policy.

| Need | Candidate | Pitfalls |
|---|---|---|
| Convex hull | Andrew monotone chain | Duplicates, all collinear, keep/drop boundary points |
| Orientation/intersection | Cross products and bounding boxes | Integer overflow, collinear overlap, open/closed endpoints |
| Polygon area/containment | Shoelace, winding/ray casting, convex binary search | Self-intersection, boundary convention, vertex order |
| Nearest pair | Divide-and-conquer or sweep | Duplicate points, strip invariant, squared overflow |
| Half-plane feasibility | Half-plane intersection or 2D LP | Parallel lines, unbounded/degenerate result, epsilon ordering |

Test geometry with coincident, collinear, tangent, zero-area, extreme-coordinate, and reversed-orientation cases.

## Range and advanced structures

Choose the operation algebra before the structure:

```
query type | point/range update | online/offline | persistence | coordinate size
```

- Fenwick trees suit prefix groups such as sums/xor; arbitrary min with updates does not inherit the same inverse trick.
- Segment tree lazy tags require a defined composition order. Test sequences of overlapping updates, not only isolated operations.
- Sparse-table O(1) overlapping queries require idempotence (for example min or gcd), not general sums.
- Persistent structures need heap/static-pool sizing and must never mutate shared nodes. Avoid giant node arrays as local stack objects.
- Implicit treaps need push-before-split/merge and deterministic reproducible RNG during debugging.
- Cartesian trees can be height `O(n)`; do not call them balanced search trees.

## Selecting among several fits

Rank candidates by:

1. proof burden and model fidelity;
2. worst-case time and memory with constants;
3. implementation risk under the contest environment;
4. ease of brute/differential validation;
5. extensibility to reconstruction or scoring requirements.

Use the least complex candidate that clears all five. When two candidates are close, prototype their dominant kernel on representative sizes instead of arguing from folklore constants.
