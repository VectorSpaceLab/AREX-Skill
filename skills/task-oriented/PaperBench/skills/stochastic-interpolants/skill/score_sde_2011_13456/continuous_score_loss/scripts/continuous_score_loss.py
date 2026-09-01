#!/usr/bin/env python3
import argparse, json, math

def ve_sigma(t, sigma_min=0.01, sigma_max=50.0):
    return sigma_min * (sigma_max / sigma_min) ** float(t)

def make_batch(samples, times, noises, sigma_min=0.01, sigma_max=50.0):
    if not (len(samples) == len(times) == len(noises)):
        raise ValueError('samples, times, and noises must have equal length')
    batch=[]
    for x0,t,z in zip(samples,times,noises):
        sigma=ve_sigma(t, sigma_min, sigma_max)
        xt=x0+sigma*z
        batch.append({'x0':x0,'t':t,'noise':z,'sigma':sigma,'xt':xt,'target_score':-z/sigma})
    return batch

def predict(params, xt, t):
    return params['a']*xt + params['b']*t + params['c']

def loss_and_grad(params, batch):
    n=len(batch); loss=0.0; grad={'a':0.0,'b':0.0,'c':0.0}
    for item in batch:
        pred=predict(params,item['xt'],item['t']); err=pred-item['target_score']; loss += err*err
        grad['a'] += 2*err*item['xt']/n; grad['b'] += 2*err*item['t']/n; grad['c'] += 2*err/n
    return loss/n, grad

def step(params, batch, lr=0.05):
    loss_before, grad = loss_and_grad(params, batch)
    updated={k: params[k]-lr*grad[k] for k in params}
    loss_after, _ = loss_and_grad(updated, batch)
    return {'loss_before': loss_before, 'loss_after': loss_after, 'params_before': dict(params), 'params_after': updated, 'grad': grad}

def self_test():
    batch=make_batch([-1,1],[0.2,0.8],[0.5,-0.25])
    perfect=[item['target_score'] for item in batch]
    assert perfect[0] < 0 and perfect[1] > 0
    params={'a':0.0,'b':0.0,'c':0.0}
    trace=step(params,batch,lr=0.01)
    assert trace['params_before'] != trace['params_after']
    assert trace['loss_after'] < trace['loss_before']
    return True

def main():
    p=argparse.ArgumentParser(); p.add_argument('--self-test', action='store_true'); args=p.parse_args()
    if args.self_test:
        self_test(); print(json.dumps({'ok': True})); return
    batch=make_batch([-2,-1,1,2],[0.15,0.35,0.65,0.85],[0.3,-0.4,0.2,-0.1])
    print(json.dumps(step({'a':0.0,'b':0.0,'c':0.0}, batch, 0.02), indent=2))
if __name__ == '__main__': main()
