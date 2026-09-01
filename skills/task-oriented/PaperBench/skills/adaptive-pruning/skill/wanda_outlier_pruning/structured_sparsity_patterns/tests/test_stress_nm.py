from structured import nm_mask

def test_multiple_rows_exact_counts():
    res=nm_mask([[9,1,8,2,7,3,6,4],[1,2,3,4,5,6,7,8]], 2, 4)
    for row in res['mask']:
        assert row[:4].count(True)==2
        assert row[4:8].count(True)==2
