import argparse,json,re

def norm(t):
    t = t.lower()
    return re.sub(r'^(ġ|Ġ|▁|\s)+','',t)
def group(top_tokens, lexicon):
    inv={norm(tok):label for label,toks in lexicon.items() for tok in toks}
    groups={}; unresolved=[]
    for item in top_tokens:
        tok=item['token'] if isinstance(item,dict) else item; key=norm(tok); lab=inv.get(key)
        if lab: groups.setdefault(lab,[]).append(tok)
        else: unresolved.append(tok)
    total=max(1,len(top_tokens)); best=max(groups.items(), key=lambda kv: len(kv[1]))[0] if groups else 'unknown'
    return {'best_concept':best,'groups':groups,'unresolved':unresolved,'purity': len(groups.get(best,[]))/total}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input'); ap.add_argument('--output'); ap.add_argument('--fixture',action='store_true'); ns=ap.parse_args()
    data={'top_tokens':[{'token':'cat'},{'token':'dog'},{'token':'red'}], 'lexicon':{'animal':['cat','dog'],'color':['red']}} if ns.fixture else json.load(open(ns.input))
    out=group(data['top_tokens'], data['lexicon']); text=json.dumps(out,indent=2); open(ns.output,'w').write(text) if ns.output else print(text)
if __name__=='__main__': main()
