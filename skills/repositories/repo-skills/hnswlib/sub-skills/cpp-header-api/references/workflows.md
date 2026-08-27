# C++ workflows

These recipes are intentionally small and use only the public header API. Replace
`HNSWLIB_INCLUDE` and application-specific values in the caller's environment;
no checkout layout is assumed.

## 1. Build a basic L2 index

1. Select a `dim`, a capacity at least as large as the planned population, and
   unique `labeltype` labels.
2. Construct the metric space before the index.
3. Add contiguous `float[dim]` records and set query `ef` before searching.

```cpp
const size_t dim = 4;
hnswlib::L2Space space(dim);
hnswlib::HierarchicalNSW<float> index(
    &space, 1000, 16, 200, 100, false);
index.setEf(80);

std::vector<float> point(dim);
index.addPoint(point.data(), 42);

const auto result = index.searchKnnCloserFirst(point.data(), 1);
if (result.empty() || result.front().second != 42) {
    throw std::runtime_error("self query did not return the inserted label");
}
```

The constructor's fifth and sixth arguments are random seed and replacement
policy. `M` controls graph degree/memory; `ef_construction` controls build
quality and build time. Start with the documented defaults, then tune against a
separate recall workload. `ef` is a query-time setting and should normally be at
least `k`.

## 2. Consume result order correctly

Use `searchKnnCloserFirst` when the consumer wants a vector:

```cpp
auto close_first = index.searchKnnCloserFirst(query, k);
for (const auto& item : close_first) {
    const float distance = item.first;
    const hnswlib::labeltype label = item.second;
    // distance is nondecreasing in the intended result order.
}
```

If the queue form is required, remember that `top()` is the farthest retained
item. To produce a close-first vector without relying on an undocumented queue
ordering, drain it into a vector from the back:

```cpp
auto queue = index.searchKnn(query, k);
std::vector<std::pair<float, hnswlib::labeltype>> close_first(queue.size());
size_t position = close_first.size();
while (!queue.empty()) {
    close_first[--position] = queue.top();
    queue.pop();
}
```

A common failed integration drains `top()` directly and presents the results as
closest first. Keep an assertion or a synthetic two-distance case in a test to
prevent this regression.

## 3. Add a label filter

A filter is a stateful object supplied by pointer for one search. Its call
operator receives the external label:

```cpp
class AllowRange : public hnswlib::BaseFilterFunctor {
    hnswlib::labeltype low_;
    hnswlib::labeltype high_;
 public:
    AllowRange(hnswlib::labeltype low, hnswlib::labeltype high)
        : low_(low), high_(high) {}
    bool operator()(hnswlib::labeltype label) override {
        return low_ <= label && label <= high_;
    }
};

AllowRange only_ids(100, 199);
auto result = index.searchKnnCloserFirst(query, k, &only_ids);
for (const auto& item : result) {
    assert(item.second >= 100 && item.second <= 199);
}
```

Keep the filter and any referenced state alive for the call. It is normal for a
filter to return fewer than `k` results. If no labels pass, an empty result is a
valid outcome; do not read `.top()` or `.front()` without checking.

## 4. Delete and replace capacity slots

Choose the replacement policy at construction time, before mutation:

```cpp
hnswlib::HierarchicalNSW<float> index(
    &space, capacity, 16, 200, 100, true);
// Populate until capacity, then:
index.markDelete(old_label);
index.addPoint(new_vector, new_label, true);
```

`markDelete` omits the old label from normal searches but leaves graph links in
place. The final `true` permits `addPoint` to use a deleted slot. If the index
was made with the default `false`, the same call throws with a replacement
policy error. If no deleted slot is available, replacement mode does not create
capacity out of nothing. A regular repeated-label `addPoint` is an update, not a
replacement operation.

Do not call `unmarkDelete` on a label after its deleted slot may have been reused.
Treat deletion, replacement, and label allocation as one coordinated lifecycle.

## 5. Save, load, and extend

The metric space used for load must have the same compatible dimension and data
layout and must outlive the loaded index:

```cpp
const std::string file = output_name;
index.saveIndex(file);

hnswlib::HierarchicalNSW<float> loaded(
    &space, file, false, larger_capacity, allow_replace_deleted);
loaded.setEf(80);  // save/load does not preserve ef
auto result = loaded.searchKnnCloserFirst(query, k);
```

The fourth load-constructor argument is an optional new maximum capacity. It can
be greater than the saved capacity; a value too small for existing elements is
not accepted as a shrink. For an already-created object, use
`loaded.resizeIndex(new_max_elements)` only when no concurrent operation can
observe the reallocation and the new value is not below the current count.

Use a per-run output file, check exceptions, and remove it only after the loaded
query has passed. Persistence is binary and should be treated as a compatible
hnswlib index file rather than a portable text format.

## 6. Exact baseline with BruteforceSearch

For a small index or a correctness comparison, construct the exact scan with the
same space:

```cpp
hnswlib::BruteforceSearch<float> exact(&space, capacity);
for (const auto& record : records) {
    exact.addPoint(record.data(), record.label);
}
const auto ground_truth = exact.searchKnnCloserFirst(query, k);
```

`BruteforceSearch` supports the same filter and closer-first helper and has a
file constructor for its own saved format. Its `searchKnn` asserts that `k` is
no larger than its total count before applying a filter. Use a valid `k` and
compare labels/distances under the same metric; do not compare an HNSW result
queue as if it were already ordered close-first.

## 7. Epsilon search (optional C++ path)

The exact observed entry point is a stateful stop-condition call, not a
`searchKnn` overload:

```cpp
hnswlib::EpsilonSearchStopCondition<float> stop(
    epsilon, min_num_candidates, max_num_candidates);
auto result = index.searchStopConditionClosest(query, stop);
```

`epsilon` is in the metric's distance units. With `L2Space`, it is a squared
L2 threshold. The stop object requires `min_num_candidates <=
max_num_candidates`; final results are limited to the epsilon region and the
maximum. Keep it alive until the call returns. This facility is C++-only in the
scoped evidence and should not be advertised as a Python binding feature.

## 8. Multivector search (optional C++ path)

Use a multivector space with a document-id type and allocate each stored record
as `dim` floats followed by one `DOCIDTYPE` value:

```cpp
using docidtype = unsigned int;
hnswlib::MultiVectorL2Space<docidtype> space(dim);
const size_t bytes_per_point = space.get_data_size();
std::vector<char> record(bytes_per_point);
// Fill the first dim * sizeof(float) bytes as floats.
space.set_doc_id(record.data(), document_id);
index.addPoint(record.data(), vector_label);

hnswlib::MultiVectorSearchStopCondition<docidtype, float> stop(
    space, documents_to_return, ef_collection);
auto result = index.searchStopConditionClosest(query_vector, stop);
```

The `MultiVectorInnerProductSpace<docidtype>` constructor has the same shape.
The query is only the vector bytes, while each stored record includes its
trailing document id. The stop condition counts documents rather than raw
vectors and returns vector labels representing those selected documents. Use
the exact `BaseMultiVectorSpace` and stop-condition declarations in the API
reference when implementing another document aggregation policy.

## 9. Custom stop condition

Derive from `BaseSearchStopCondition<dist_t>` and implement all of its pure
virtual methods. The implementation receives labels, data pointers, and metric
distances as candidates enter or leave the retained set. Its `filter_results`
method must reconcile the final close-first vector with any state tracked during
search. Call only:

```cpp
auto result = index.searchStopConditionClosest(query, stop_condition, filter);
```

Do not pass a custom stop object to `searchKnn`; that method has no such
parameter. Test a custom condition against a deterministic exact baseline and
assert both the stopping bound and final result invariant.

## 10. Direct compiler and CMake checks

A direct compile can be kept self-contained:

```sh
"${CXX:-c++}" -std=c++11 -O2 -pthread \
  -I"${HNSWLIB_INCLUDE}" app.cpp -o app
```

For a CMake consumer, set the standard on the client target and link the
interface target. Add OpenMP only if the client uses OpenMP or a chosen build
configuration requires it; hnswlib's public API does not expose an OpenMP
runtime contract. Add native SIMD flags only when the resulting binary will run
on a compatible CPU.
