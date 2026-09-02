import math

def sigmoid(x): return 1/(1+math.exp(-x))
def loss_for_param(param): return (sigmoid(param)-0.8)**2
def train_one_step(param=0.0, lr=2.0, classifier_weight=1.0):
    before=param; cb=classifier_weight; eps=1e-5
    loss_before=loss_for_param(param)
    grad=(loss_for_param(param+eps)-loss_for_param(param-eps))/(2*eps)
    param=param-lr*grad
    return {"loss_before":loss_before,"loss_after":loss_for_param(param),"params_before":{"prompt_delta":before},"params_after":{"prompt_delta":param},"classifier_before":cb,"classifier_after":classifier_weight}
