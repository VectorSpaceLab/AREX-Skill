import json, math, argparse

def sigmoid(z): return 1/(1+math.exp(-z))
def run(steps=25, lr=0.4):
    # frozen source: four logits from two target coords plus two trainable padding coords
    source_weights=[[2,0,0,1],[-2,0,0,-1],[0,2,1,0],[0,-2,-1,0]]
    source_before=json.loads(json.dumps(source_weights))
    data=[([-1,-1],0),([-1,1],0),([1,-1],1),([1,1],1)]*3
    theta=[0.0,0.0]; head=[0.0,0.0,0.0,0.0]; b=0.0
    def feats(x):
        v=[x[0],x[1],theta[0],theta[1]]
        return [sum(wi*vi for wi,vi in zip(w,v)) for w in source_weights]
    def loss_acc():
        loss=0; ok=0
        for x,y in data:
            z=sum(h*f for h,f in zip(head,feats(x)))+b; p=sigmoid(z)
            loss+=-(y*math.log(p+1e-9)+(1-y)*math.log(1-p+1e-9)); ok+=(p>=.5)==bool(y)
        return loss/len(data), ok/len(data)
    params_before={'theta':theta[:],'head':head[:],'bias':b}
    loss_before,acc_before=loss_acc()
    for _ in range(steps):
        gt=[0,0]; gh=[0,0,0,0]; gb=0
        for x,y in data:
            f=feats(x); z=sum(h*fi for h,fi in zip(head,f))+b; p=sigmoid(z); e=p-y
            for j in range(4): gh[j]+=e*f[j]/len(data)
            gt[0]+=e*(head[2]*1+head[3]*-1)/len(data); gt[1]+=e*(head[0]*1+head[1]*-1)/len(data); gb+=e/len(data)
        for j in range(4): head[j]-=lr*gh[j]
        theta[0]-=lr*gt[0]; theta[1]-=lr*gt[1]; b-=lr*gb
    loss_after,acc_after=loss_acc()
    return {'loss_before':loss_before,'loss_after':loss_after,'accuracy_before':acc_before,'accuracy_after':acc_after,'params_before':params_before,'params_after':{'theta':theta,'head':head,'bias':b},'source_before':source_before,'source_after':source_weights,'source_unchanged':source_before==source_weights}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); pathlib=None
    r=run(); open(a.output,'w').write(json.dumps(r,indent=2))
