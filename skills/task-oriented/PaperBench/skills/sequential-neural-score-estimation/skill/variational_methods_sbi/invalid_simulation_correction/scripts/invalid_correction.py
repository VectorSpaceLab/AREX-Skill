def estimate_validity(theta_flags, bins=4):
    if not theta_flags: return []
    xs=[t for t,_ in theta_flags]; lo=min(xs); hi=max(xs); width=(hi-lo)/bins if hi>lo else 1.0
    stats=[[0,0] for _ in range(bins)]
    for theta,valid in theta_flags:
        idx=min(bins-1, int((theta-lo)/width)) if hi>lo else 0
        stats[idx][0]+=1; stats[idx][1]+=1 if valid else 0
    return [{"bin":i,"count":c,"valid_count":v,"p_valid":(v+1)/(c+2)} for i,(c,v) in enumerate(stats)]

def correct_scores(likelihood_scores, validity_probs):
    return [a*b for a,b in zip(likelihood_scores, validity_probs)]

if __name__ == "__main__":
    import json; print(json.dumps(estimate_validity([(0,True),(1,False),(2,True)])))
