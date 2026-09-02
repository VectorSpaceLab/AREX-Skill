from project_vocabulary import project

def test_projection_ranks_promoted_tokens():
    out=project([{'neuron':0,'vector':[1,0]}], [[1,0],[.8,0],[0,1]], ['cat','dog','red'], 2)
    assert [x['token'] for x in out[0]['top_tokens']]==['cat','dog']
