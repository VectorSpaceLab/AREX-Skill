import argparse,json

def attribution_margin(activation, promoted_scores, control_scores):
    p=sum(promoted_scores)/max(1,len(promoted_scores)); c=sum(control_scores)/max(1,len(control_scores))
    margin=activation*(p-c)
    return {'activation':activation,'promoted_mean':p,'control_mean':c,'margin':margin,'passes': activation>0 and margin>0}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input'); ap.add_argument('--output'); ap.add_argument('--fixture',action='store_true'); ns=ap.parse_args()
    data={'activation':2,'promoted_scores':[1,.8],'control_scores':[0,.1]} if ns.fixture else json.load(open(ns.input))
    out=attribution_margin(data['activation'], data['promoted_scores'], data['control_scores']); text=json.dumps(out,indent=2); open(ns.output,'w').write(text) if ns.output else print(text)
if __name__=='__main__': main()
