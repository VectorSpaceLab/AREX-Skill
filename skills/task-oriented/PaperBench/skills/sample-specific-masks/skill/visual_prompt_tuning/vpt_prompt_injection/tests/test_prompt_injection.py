from prompt_injection import *
def test_prompt_shapes_and_count():
    t=[[9,9],[1,1],[2,2]]; p=[[0,0],[0.5,0.5]]
    out=prepend_prompts(t,p)
    assert out[0]==[9,9] and out[1]==[0,0] and out[-1]==[2,2]
    assert parameter_count(2,3,4,True)==24

def test_mismatched_dimension_rejected():
    try:
        prepend_prompts([[1,2]], [[1]])
        assert False
    except ValueError:
        assert True
