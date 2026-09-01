
import math

def sigmoid(z): return 1/(1+math.exp(-z))

def binary_loss(weight, prompt, xs, ys):
    total=0.0
    for x,y in zip(xs,ys):
        p=sigmoid(weight*(x+prompt))
        total += -(y*math.log(p+1e-12)+(1-y)*math.log(1-p+1e-12))
    return total/len(xs)

def train_scalar_prompt(xs, ys, weight=3.0, prompt=0.0, lr=0.2, steps=20):
    weight_before=weight; prompt_before=prompt; loss_before=binary_loss(weight,prompt,xs,ys)
    for _ in range(steps):
        grad=0.0
        for x,y in zip(xs,ys):
            grad += (sigmoid(weight*(x+prompt))-y)*weight
        grad /= len(xs)
        prompt -= lr*grad
    loss_after=binary_loss(weight,prompt,xs,ys)
    return {'params_before': {'prompt': prompt_before}, 'params_after': {'prompt': prompt}, 'loss_before': loss_before, 'loss_after': loss_after, 'frozen_weights_unchanged': weight == weight_before, 'weight_before': weight_before, 'weight_after': weight}
