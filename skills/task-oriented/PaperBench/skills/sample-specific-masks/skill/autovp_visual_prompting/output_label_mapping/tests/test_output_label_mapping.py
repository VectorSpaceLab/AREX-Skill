from output_label_mapping import freq_map, map_prediction, fully_map

def test_freq_map_and_fully_map():
    mp=freq_map([2,2,1,3,3,3],[0,0,0,1,1,1],1)
    assert mp=={0:[2],1:[3]}
    assert map_prediction(3,mp)==1
    assert fully_map([1,2], [[1,0],[0,2]], [0,1]) == [1,5]


def test_freq_map_tie_breaks_by_source_id():
    mp=freq_map([5,4],[0,0],1)
    assert mp[0]==[4]
