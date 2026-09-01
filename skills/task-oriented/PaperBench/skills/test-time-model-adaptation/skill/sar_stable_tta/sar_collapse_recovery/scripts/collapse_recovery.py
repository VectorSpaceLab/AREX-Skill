
def update_ema(previous, value, momentum=0.9):
    if previous is None:
        return value
    return momentum * previous + (1.0 - momentum) * value

def recovery_decision(previous_ema, current_entropy, threshold=0.2, momentum=0.9):
    ema = update_ema(previous_ema, current_entropy, momentum)
    return {'ema': ema, 'reset': ema < threshold, 'threshold': threshold}
