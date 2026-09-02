import json

def build_fixture():
    return {'vocab':['cat','dog','red','blue','pizza'], 'unembedding':[[1,0,0],[.9,0,0],[0,1,0],[0,.9,0],[0,0,1]], 'state':{'h.0.mlp.c_proj.weight':[[1,0,0],[0,1,0],[0,0,1]]}, 'lexicon':{'animal':['cat','dog'], 'color':['red','blue'], 'food':['pizza']}}
if __name__=='__main__': print(json.dumps(build_fixture(), indent=2))
