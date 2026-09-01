from input_programming import build_programmed_input

def test_center_preserved_border_programmed():
    r=build_programmed_input([9], [0,0,0,0,1,0,0,0,0], [1,2,3,4,5,6,7,8])
    assert r['programmed_input']==[1,2,3,4,9,5,6,7,8]
    assert r['metadata']['task_preserved'] is True
