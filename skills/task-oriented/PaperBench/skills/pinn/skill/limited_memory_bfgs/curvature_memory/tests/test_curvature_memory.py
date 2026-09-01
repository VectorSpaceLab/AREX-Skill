from curvature_memory import update_memory, dot

def test_accepts_positive_curvature_and_truncates_fifo():
    mem = []
    mem = update_memory(mem, [0, 0], [1, 0], [0, 0], [2, 0], 2)
    mem = update_memory(mem, [1, 0], [1, 1], [2, 0], [2, 3], 2)
    mem = update_memory(mem, [1, 1], [2, 1], [2, 3], [7, 3], 2)
    assert len(mem) == 2
    assert dot(mem[0][0], mem[0][1]) == 3
    assert dot(mem[1][0], mem[1][1]) == 5

def test_rejects_nonpositive_curvature():
    mem = update_memory([], [0], [1], [1], [0], 3)
    assert mem == []
