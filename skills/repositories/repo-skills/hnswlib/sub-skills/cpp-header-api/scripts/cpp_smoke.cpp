#include <hnswlib/hnswlib.h>

#include <cassert>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

namespace {

class AllowMultiplesOfTwenty : public hnswlib::BaseFilterFunctor {
 public:
    bool operator()(hnswlib::labeltype label) override {
        return label % 20 == 0;
    }
};

void assert_close_first(
        const std::vector<std::pair<float, hnswlib::labeltype>>& result) {
    for (std::size_t i = 1; i < result.size(); ++i) {
        assert(result[i - 1].first <= result[i].first);
    }
}

void assert_expected_query(
        const std::vector<std::pair<float, hnswlib::labeltype>>& result) {
    assert(!result.empty());
    assert(result.front().second == 10);
    assert(std::fabs(result.front().first) < 1e-6f);
    assert_close_first(result);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: cpp_smoke <index-output>\n";
        return 2;
    }

    const std::string index_output = argv[1];
    const std::size_t dim = 2;
    const std::size_t capacity = 6;
    const float points[capacity][dim] = {
        {0.0f, 0.0f},
        {1.0f, 0.0f},
        {0.0f, 2.0f},
        {3.0f, 0.0f},
        {0.0f, 4.0f},
        {5.0f, 0.0f},
    };
    const hnswlib::labeltype labels[capacity] = {10, 20, 30, 40, 50, 60};
    const float query[dim] = {0.0f, 0.0f};

    // The space must outlive both index objects: each retains its distance
    // function parameter from this object.
    hnswlib::L2Space space(dim);
    hnswlib::HierarchicalNSW<float> index(
        &space, capacity, 4, 32, 17, false);
    index.setEf(32);

    for (std::size_t i = 0; i < capacity; ++i) {
        index.addPoint(points[i], labels[i]);
    }

    // The queue is intentionally further-first at top(); the helper is the
    // closer-first vector consumed by the assertions below.
    std::priority_queue<std::pair<float, hnswlib::labeltype>> queue =
        index.searchKnn(query, 3);
    assert(queue.size() == 3);
    // The three closest points have labels 10, 20, and 30; the queue top is
    // therefore the farthest of that retained trio, label 30.
    assert(queue.top().second == 30);

    const std::vector<std::pair<float, hnswlib::labeltype>> result =
        index.searchKnnCloserFirst(query, 3);
    assert(result.size() == 3);
    assert_expected_query(result);

    AllowMultiplesOfTwenty filter;
    const std::vector<std::pair<float, hnswlib::labeltype>> filtered =
        index.searchKnnCloserFirst(query, 3, &filter);
    assert(filtered.size() == 3);
    assert_close_first(filtered);
    for (const auto& item : filtered) {
        assert(item.second % 20 == 0);
    }

    index.saveIndex(index_output);

    hnswlib::HierarchicalNSW<float> loaded(
        &space, index_output, false, capacity, false);
    loaded.setEf(32);
    const std::vector<std::pair<float, hnswlib::labeltype>> restored =
        loaded.searchKnnCloserFirst(query, 3);
    assert(restored.size() == 3);
    assert_expected_query(restored);

    const std::vector<std::pair<float, hnswlib::labeltype>> restored_filtered =
        loaded.searchKnnCloserFirst(query, 3, &filter);
    assert(restored_filtered.size() == 3);
    for (const auto& item : restored_filtered) {
        assert(item.second % 20 == 0);
    }

    std::cout << "C++ header smoke passed: " << result.size()
              << " ordinary and " << filtered.size() << " filtered results\n";
    return 0;
}
