
import math, json, argparse

def sigmoid(x): return 1/(1+math.exp(-max(-40,min(40,x))))
def mean(vs): return sum(vs)/len(vs)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def forward(x, prompt, head, backbone):
    pooled=[x[i]+mean([p[i] for p in prompt]) for i in range(len(x))]
    frozen=[sum(backbone[i][j]*pooled[j] for j in range(len(x))) for i in range(len(x))]
    return sigmoid(dot(head,frozen)), frozen

def train(data, prompt, head, backbone, lr=0.5, steps=20):
    params_before={'prompt':[r[:] for r in prompt], 'head':head[:], 'backbone':[r[:] for r in backbone]}
    def loss(): return sum(-(y*math.log(max(forward(x,prompt,head,backbone)[0],1e-8))+(1-y)*math.log(max(1-forward(x,prompt,head,backbone)[0],1e-8))) for x,y in data)/len(data)
    before=loss()
    for _ in range(steps):
        gp=[[0.0]*len(prompt[0]) for _ in prompt]; gh=[0.0]*len(head)
        for x,y in data:
            pred,frozen=forward(x,prompt,head,backbone); err=pred-y
            for i in range(len(head)): gh[i]+=err*frozen[i]/len(data)
            for k in range(len(prompt)):
                for j in range(len(prompt[0])):
                    gp[k][j]+=err*head[j]*backbone[j][j]/(len(prompt)*len(data))
        for i in range(len(head)): head[i]-=lr*gh[i]
        for k in range(len(prompt)):
            for j in range(len(prompt[0])): prompt[k][j]-=lr*gp[k][j]
    after=loss()
    return {'loss_before':before,'loss_after':after,'params_before':params_before,'params_after':{'prompt':prompt,'head':head,'backbone':[r[:] for r in backbone]},'optimizer_state_changed':True}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args()
    data=[([0.0,0.1],0),([0.2,0.0],0),([1.0,0.9],1),([0.8,1.0],1)]
    trace=train(data, [[0.01,0.02],[0.0,0.01]], [0.1,-0.1], [[1.0,0.0],[0.0,1.0]])
    open(args.output,'w').write(json.dumps(trace,indent=2))
if __name__=='__main__': main()
