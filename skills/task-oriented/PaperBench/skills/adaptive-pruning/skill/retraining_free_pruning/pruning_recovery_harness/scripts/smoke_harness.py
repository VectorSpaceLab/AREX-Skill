def mechanism_pass_rate(checks):
    vals=[bool(v) for v in checks.values()]
    return sum(vals)/len(vals) if vals else 0.0
