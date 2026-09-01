import json, argparse
EXPLICIT={"loss","constraint","rule","handcrafted","gradient","saliency","decomposition","encoder","decoder"}
IMPLICIT={"attention","transformer","gan","generative","global","self-attention","adaptive","diffusion"}
def classify_method(text):
    words=text.lower().replace('_','-')
    exp=sorted([w for w in EXPLICIT if w in words])
    imp=sorted([w for w in IMPLICIT if w in words])
    if imp and exp:
        cat = 'hybrid' if min(len(imp), len(exp)) >= 2 else ('implicit' if len(imp) > len(exp) else 'explicit')
    elif imp:
        cat = 'implicit'
    elif exp:
        cat = 'explicit'
    else:
        cat = 'uncertain'
    return {'category':cat,'explicit_evidence':exp,'implicit_evidence':imp,'rationale':f'{cat} based on mechanism keywords'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('text'); ap.add_argument('--output')
    ns=ap.parse_args(); res=classify_method(ns.text)
    out=json.dumps(res,indent=2)
    if ns.output: open(ns.output,'w').write(out+'\n')
    else: print(out)
if __name__=='__main__': main()
