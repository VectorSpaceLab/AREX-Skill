from output_map import aggregate

def test_empty_group_rejected():
    try:
        aggregate([0.2,0.8], [[0], []])
    except ValueError:
        return
    assert False
