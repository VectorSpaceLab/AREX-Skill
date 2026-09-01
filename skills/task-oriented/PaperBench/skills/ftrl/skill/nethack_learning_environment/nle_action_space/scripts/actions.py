REDUCED_ACTIONS={"N","S","E","W","NE","NW","SE","SW","SEARCH","KICK","EAT","DOWN"}
FULL_EXTRA={"UP","WAIT","PICKUP","OPEN","READ","PRAY"}

def canonicalize_action(action, profile="reduced"):
    name=str(action).upper()
    allowed=set(REDUCED_ACTIONS)
    if profile=="full_proxy": allowed |= FULL_EXTRA
    valid=name in allowed
    return {"action":name,"profile":profile,"valid":valid,"invalid_penalty":0.0 if valid else -0.001}
