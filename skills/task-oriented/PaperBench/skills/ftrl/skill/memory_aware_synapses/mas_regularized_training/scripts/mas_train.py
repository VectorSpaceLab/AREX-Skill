def train_linear_regression(weights, targets, features, *, theta_star=None, omega=None, lam=0.0, lr=0.05, steps=20):
    weights=list(weights); before=list(weights)
    theta_star=list(theta_star) if theta_star is not None else list(weights)
    omega=list(omega) if omega is not None else [0.0 for _ in weights]
    trace=[]
    for _ in range(steps):
        grads=[0.0 for _ in weights]; loss=0.0
        for sample,target in zip(features, targets):
            pred=sum(w*x for w,x in zip(weights,sample)); err=pred-target; loss+=err*err/len(targets)
            for i,x in enumerate(sample): grads[i]+=2*err*x/len(targets)
        penalty=0.0
        for i in range(len(weights)):
            drift=weights[i]-theta_star[i]; penalty+=lam*omega[i]*drift*drift; grads[i]+=2*lam*omega[i]*drift
        for i in range(len(weights)): weights[i]-=lr*grads[i]
        trace.append({'task_loss':loss,'mas_penalty':penalty,'total_loss':loss+penalty})
    return {'params_before':before,'params_after':weights,'trace':trace,'optimizer_step_executed':before!=weights,'high_importance_drift':abs(weights[0]-before[0]),'low_importance_drift':abs(weights[-1]-before[-1])}
