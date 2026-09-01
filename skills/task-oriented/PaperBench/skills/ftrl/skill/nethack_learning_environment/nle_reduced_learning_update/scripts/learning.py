def predict(params, features):
    return params["bias"] + sum(params["weights"].get(k,0.0)*float(v) for k,v in features.items())

def one_step_update(features, reward, lr=0.01, params=None):
    if params is None:
        params={"bias":0.0,"weights":{k:0.0 for k in features}}
    before={"bias":params["bias"],"weights":dict(params["weights"])}
    pred=predict(before, features); err=pred-float(reward); loss_before=err*err
    after={"bias":before["bias"]-lr*2*err,"weights":dict(before["weights"])}
    for k,v in features.items():
        after["weights"][k]=after["weights"].get(k,0.0)-lr*2*err*float(v)
    pred_after=predict(after, features); loss_after=(pred_after-float(reward))**2
    return {"loss_before":loss_before,"loss_after":loss_after,"params_before":before,"params_after":after,"optimizer_state_changed":before!=after}
