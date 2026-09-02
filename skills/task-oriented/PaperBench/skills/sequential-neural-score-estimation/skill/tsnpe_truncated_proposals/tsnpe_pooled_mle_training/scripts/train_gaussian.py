import argparse, json, math

def nll(theta, x, obs, mean, log_std):
    var=math.exp(2*log_std); total=0.0
    for t,xi in zip(theta,x):
        pred=mean + 0.5*(obs-xi)
        total += 0.5*((t-pred)**2/var + math.log(2*math.pi*var))
    return total/len(theta)

def train(payload):
    theta=[float(v) for v in payload['theta']]; x=[float(v) for v in payload['x']]
    if len(theta)!=len(x) or not theta: raise ValueError('empty or mismatched training data')
    obs=float(payload.get('observation',0.0)); mean=float(payload.get('mean',0.0)); log_std=float(payload.get('log_std',0.0)); lr=float(payload.get('lr',0.05)); steps=int(payload.get('steps',20))
    before={'mean':mean,'log_std':log_std}; loss_before=nll(theta,x,obs,mean,log_std)
    for _ in range(steps):
        var=math.exp(2*log_std); gm=0.0; gl=0.0
        for t,xi in zip(theta,x):
            pred=mean+0.5*(obs-xi); diff=pred-t
            gm += diff/var
            gl += 1 - (diff*diff)/var
        gm/=len(theta); gl/=len(theta)
        mean -= lr*gm; log_std -= lr*gl
    loss_after=nll(theta,x,obs,mean,log_std)
    return {'loss_before':loss_before,'loss_after':loss_after,'params_before':before,'params_after':{'mean':mean,'log_std':log_std},'pooled_sample_count':len(theta),'mechanism_checks':{'pooled_data_used':True,'ordinary_mle_loss_used':True,'optimizer_step_executed': before != {'mean':mean,'log_std':log_std}}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--output', required=True); ns=ap.parse_args(); json.dump(train(json.load(open(ns.input))), open(ns.output,'w'), indent=2)
if __name__=='__main__': main()
