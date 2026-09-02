def dlr_loss(logits, true_class, eps=1e-12):
    if len(logits) < 3:
        raise ValueError('DLR requires at least three classes')
    order=sorted(range(len(logits)), key=lambda i: logits[i])
    top=order[-1]; second=order[-2]; third=order[-3]
    competitor = second if top == true_class else top
    denom = logits[top] - logits[third] + eps
    return - (logits[true_class] - logits[competitor]) / denom

def diagnostics(logits, true_class):
    order=sorted(range(len(logits)), key=lambda i: logits[i], reverse=True)
    return {'ranking': order, 'true_rank': order.index(true_class), 'loss': dlr_loss(logits,true_class)}
