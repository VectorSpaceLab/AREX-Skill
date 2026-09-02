import argparse,json

def dot(a,b): return sum(float(x)*float(y) for x,y in zip(a,b))
def project(value_vectors, unembedding, vocab, top_k=5):
    if len(unembedding)!=len(vocab): raise ValueError('unembedding rows must match vocab')
    out=[]
    for rec in value_vectors:
        vec=rec.get('vector', rec) if isinstance(rec,dict) else rec
        scores=[{'token':tok,'score':dot(vec,row)} for tok,row in zip(vocab,unembedding)]
        scores.sort(key=lambda x:(-x['score'], x['token']))
        out.append({'neuron': rec.get('neuron', len(out)) if isinstance(rec,dict) else len(out), 'top_tokens': scores[:top_k]})
    return out
def fixture():
    vocab=['cat','dog','red','blue']; unemb=[[1,0],[.9,0],[0,1],[0,.8]]; vals=[{'neuron':0,'vector':[1,0]}]
    return project(vals,unemb,vocab,2)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input'); ap.add_argument('--output'); ap.add_argument('--fixture',action='store_true'); ns=ap.parse_args()
    if ns.fixture: out=fixture()
    else:
        data=json.load(open(ns.input)); out=project(data['value_vectors'], data['unembedding'], data['vocab'], data.get('top_k',5))
    text=json.dumps(out,indent=2); open(ns.output,'w').write(text) if ns.output else print(text)
if __name__=='__main__': main()
