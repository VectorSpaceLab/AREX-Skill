# C++ API reference

This is the focused public reference for the hnswlib 0.9.0 header API. The
implementation is included by the public umbrella header; there is no library
archive to link.

## Include and compile

Use the public include form from a client source file:

```cpp
#include <hnswlib/hnswlib.h>
```

A direct GNU/Clang-style compile uses an explicit include-root variable:

```sh
c++ -std=c++11 -O2 -pthread -I"${HNSWLIB_INCLUDE}" app.cpp -o app
```

The include root is the directory whose child is `hnswlib/`. `-pthread` is
needed by normal C++ programs that use the library's mutex/thread machinery; it
is not a separate hnswlib link library. CMake exposes an interface target named
`hnswlib::hnswlib` after installation or project integration:

```cmake
cmake_minimum_required(VERSION 3.0)
project(client LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(hnswlib CONFIG REQUIRED)
add_executable(client app.cpp)
target_link_libraries(client PRIVATE hnswlib::hnswlib)
```

The repository CMake definition is an `INTERFACE` target that supplies include
directories. Its optional example/test branch sets C++11 and compiler options,
but a consuming project owns its own warning, optimization, OpenMP, and native
CPU choices. The Makefile is for Python packaging/tests, not a C++ link step.

## Metric spaces and ownership

`L2Space(size_t dim)` implements squared L2 distance over `float[dim]` and
reports `dim * sizeof(float)` bytes. `InnerProductSpace(size_t dim)` implements
the distance `1.0f - inner_product` over `float[dim]` and reports the same byte
size. Both expose the distance function and a parameter pointing into the space
object. Construct the space first and keep it alive until the index is gone:

```cpp
hnswlib::L2Space space(dim);
hnswlib::HierarchicalNSW<float> index(
    &space, max_elements, M, ef_construction, random_seed,
    allow_replace_deleted);
```

The normal construction form is:

```cpp
HierarchicalNSW(
    SpaceInterface<dist_t>* space,
    size_t max_elements,
    size_t M = 16,
    size_t ef_construction = 200,
    size_t random_seed = 100,
    bool allow_replace_deleted = false);
```

The space pointer is not an ownership transfer. The index retains its distance
function and parameter, so destroying or moving the space first is invalid.
The default query `ef_` is 10. Call `index.setEf(ef)` explicitly; for ordinary
k-nearest-neighbor work choose `ef >= k`, then tune higher for recall at the
cost of query time.

`M` controls graph connectivity, memory, and construction/search behavior. The
implementation caps `M` at 10000 and sets `ef_construction_` to at least `M`.
The public algorithm guidance describes roughly 12--48 as a common starting
range, with higher values sometimes useful for high intrinsic dimension. These
are tuning starting points, not correctness requirements. `max_elements` is
the initial capacity.

The base interfaces are also available for custom spaces:

```cpp
template<typename MTYPE>
class SpaceInterface {
    virtual size_t get_data_size() = 0;
    virtual DISTFUNC<MTYPE> get_dist_func() = 0;
    virtual void* get_dist_func_param() = 0;
    virtual ~SpaceInterface() {}
};
```

A custom space must make its data size, distance function, and distance-function
parameter agree with every point and query buffer. `L2SpaceI` exists for byte
vectors and `int` distances, but the normal examples and smoke path use float
L2/IP spaces.

## Population and ordinary search

The algorithm interface uses external labels (`labeltype` is `size_t`):

```cpp
void addPoint(const void* datapoint, labeltype label,
              bool replace_deleted = false);
std::priority_queue<std::pair<dist_t, labeltype>>
searchKnn(const void* query_data, size_t k,
          BaseFilterFunctor* isIdAllowed = nullptr) const;
std::vector<std::pair<dist_t, labeltype>>
searchKnnCloserFirst(const void* query_data, size_t k,
                    BaseFilterFunctor* isIdAllowed = nullptr) const;
```

`addPoint` copies the point into index-owned storage. A repeated label updates
the existing item rather than adding a second external label. The caller must
keep the input buffer valid for the duration of the call and must provide the
space's exact data size.

`searchKnn` intentionally returns a `std::priority_queue` whose `top()` is the
worst/farthest item retained in the result set. Repeatedly reading `top()` and
popping therefore consumes results from farther to closer. The helper
`searchKnnCloserFirst` drains the queue and returns a vector in closer-first
order. Distances are the metric's distance values, not similarities; lower is
closer for both built-in spaces.

The result can contain fewer than `k` elements when the index has fewer eligible
items or a filter excludes candidates. `BruteforceSearch` uses the same
`AlgorithmInterface` result conventions but asserts that `k` is no greater than
its total stored count, so a caller should validate the requested `k` and
eligible population when comparing implementations.

## Filters

Derive from `BaseFilterFunctor` and return `true` for an allowed external label:

```cpp
class AllowSome : public hnswlib::BaseFilterFunctor {
 public:
    bool operator()(hnswlib::labeltype label) override {
        return label % 2 == 0;
    }
};

AllowSome filter;
auto result = index.searchKnnCloserFirst(query, k, &filter);
```

The functor is called with external labels, not internal graph positions. Keep
the functor and any state it references alive and synchronized for the complete
search call. A filter can reduce the output below `k`; it is not a post-search
assertion that all requests must be filled.

## Persistence and capacity

The index persistence methods are:

```cpp
void saveIndex(const std::string& location);
void loadIndex(const std::string& location,
               SpaceInterface<dist_t>* space,
               size_t max_elements_i = 0);
```

The load constructor is:

```cpp
HierarchicalNSW(
    SpaceInterface<dist_t>* space,
    const std::string& location,
    bool nmslib = false,
    size_t max_elements = 0,
    bool allow_replace_deleted = false);
```

The `nmslib` parameter is part of the observed constructor signature; leave it
at its default for an hnswlib file. Load with a compatible metric space and
dimension. If `max_elements` is larger than the stored current capacity, the
load form allocates that larger capacity; a value below the stored element count
is raised to a safe capacity. `resizeIndex(new_max_elements)` is also available
and rejects a value below the current element count.

The query `ef` is not written by `saveIndex`; loading resets it to 10. Always
call `setEf` after loading when the application depends on a chosen value. The
space must outlive a loaded index for the same reason it must outlive a newly
constructed one. Treat the file as an hnswlib binary artifact for a compatible
space/schema, not as a text interchange format.

## Deletion, updates, and replacement

The mutation methods are:

```cpp
void markDelete(labeltype label);
void unmarkDelete(labeltype label);
void resizeIndex(size_t new_max_elements);
void setEf(size_t ef);
```

`markDelete` marks an existing label and causes normal search to omit it; it
does not rebuild or remove graph links. Re-marking or unmarking an absent/wrongly
marked label throws. A regular `addPoint` with an existing label updates its
vector. `unmarkDelete` is explicitly unsafe as a general operation when
replacement of deleted elements is enabled, because a deleted slot may already
have been reused.

To reuse deleted slots, construct the index with the final boolean set to
`true`, mark labels deleted, then insert a new label with the third `addPoint`
argument set to `true`:

```cpp
hnswlib::HierarchicalNSW<float> index(
    &space, capacity, 16, 200, 100, true);
index.markDelete(old_label);
index.addPoint(new_vector, new_label, true);
```

Passing `replace_deleted=true` to an index whose constructor/load policy did not
enable replacement throws. If replacement is requested but no deleted slot is
available, insertion follows the normal capacity/update path and can still fail
when full. Coordinate replacement and label lifecycle decisions across threads.

## BruteforceSearch

`BruteforceSearch<dist_t>` is an exact linear-scan implementation of the same
algorithm interface:

```cpp
BruteforceSearch(SpaceInterface<dist_t>* space, size_t maxElements);
BruteforceSearch(SpaceInterface<dist_t>* space,
                 const std::string& location);
void removePoint(labeltype label);
```

It supports `addPoint`, `searchKnn`, `searchKnnCloserFirst`, `saveIndex`, and
load construction. It is useful for small exact-result comparisons and for
checking filter/order semantics, not as a replacement for HNSW's performance
profile. Its search asserts `k <= cur_element_count` before filtering.

## Optional C++ stop conditions

These declarations are C++-only optional facilities in the observed 0.9.0
headers. Use the exact templates below rather than inventing overloads:

```cpp
template<typename dist_t>
class EpsilonSearchStopCondition;

EpsilonSearchStopCondition<dist_t>(
    float epsilon, size_t min_num_candidates, size_t max_num_candidates);

std::vector<std::pair<dist_t, labeltype>>
searchStopConditionClosest(
    const void* query_data,
    BaseSearchStopCondition<dist_t>& stop_condition,
    BaseFilterFunctor* isIdAllowed = nullptr) const;
```

The epsilon condition keeps results whose metric distance is within the
specified epsilon region, while enforcing minimum and maximum candidate bounds.
For L2 this is a squared-distance threshold because `L2Space` returns squared
L2 distance. The condition's `min_num_candidates` must not exceed its maximum.

A custom `BaseSearchStopCondition<dist_t>` must implement all six virtual
operations: add a result, remove a result, decide whether to stop, decide
whether to consider a candidate, decide whether to remove extras, and filter the
final vector. The stop condition is stateful and must live through the complete
call to `searchStopConditionClosest`.

## Optional multivector search

Multivector data stores a vector followed by a document identifier. The observed
space templates and constructors are:

```cpp
template<typename DOCIDTYPE>
MultiVectorL2Space(size_t dim);
template<typename DOCIDTYPE>
MultiVectorInnerProductSpace(size_t dim);

template<typename DOCIDTYPE, typename dist_t>
MultiVectorSearchStopCondition(
    BaseMultiVectorSpace<DOCIDTYPE>& space,
    size_t num_docs_to_search,
    size_t ef_collection = 10);
```

The multivector space reports `dim * sizeof(float) + sizeof(DOCIDTYPE)` bytes
and exposes `get_doc_id(void*)` and `set_doc_id(void*, DOCIDTYPE)`. Build each
stored point with the vector bytes followed by its document id. A query passed
to `searchStopConditionClosest` is the vector portion. The multivector stop
condition groups candidate vectors by document id and filters the final labels
to the requested number of documents. See the bundled workflow for a complete
layout recipe; this path has no Python-equivalent API in the scoped evidence.

## Platform boundary

The package exposes a CPU-native extension for Python, but this sub-skill is the
C++ header API. SIMD selection is compiled conditionally by the headers; optional
`-march=native` or equivalent flags must match the deployment CPU. No CUDA API
or GPU build target is exposed here.
