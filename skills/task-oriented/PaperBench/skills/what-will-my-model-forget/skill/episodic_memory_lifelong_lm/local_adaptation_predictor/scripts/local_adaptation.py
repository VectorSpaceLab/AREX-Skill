import math

def sigmoid(x):
    return 1.0/(1.0+math.exp(-max(min(x, 30), -30)))

def adapt_and_predict(model, memory, query_text, k=2, steps=3, lr=0.3, lambda_anchor=0.01):
    neighbors=memory.knn(query_text, k)
    base_weights=list(model.weights); base_bias=model.bias
    local_weights=list(base_weights); local_bias=base_bias
    trace=[]
    for step in range(steps):
        total_loss=0.0
        for ex in neighbors:
            x=model.features(ex['text']); y=int(ex['label'])
            p=sigmoid(sum(w*v for w,v in zip(local_weights,x))+local_bias)
            grad=p-y
            total_loss += -(y*__import__('math').log(max(p,1e-9))+(1-y)*__import__('math').log(max(1-p,1e-9)))
            local_weights=[w-lr*(grad*v + lambda_anchor*(w-bw)) for w,v,bw in zip(local_weights,x,base_weights)]
            local_bias -= lr*grad
        trace.append({'step': step+1, 'loss': total_loss})
    prediction=model.predict(query_text, weights=local_weights, bias=local_bias)
    reset_ok=(model.weights==base_weights and model.bias==base_bias)
    return {'prediction': prediction, 'neighbors': neighbors, 'trace': trace, 'base_reset_confirmed': reset_ok, 'local_weights': local_weights, 'base_weights': base_weights}
