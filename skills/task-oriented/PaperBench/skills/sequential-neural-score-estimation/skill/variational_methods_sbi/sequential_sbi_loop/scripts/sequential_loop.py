def run_rounds(prior_mean=0.0, observation=1.0, rounds=3, sims_per_round=8, learning_rate=0.35):
    data=[]; proposal_mean=float(prior_mean); logs=[]
    for r in range(rounds):
        start=proposal_mean
        for i in range(sims_per_round):
            theta=proposal_mean+(i-(sims_per_round-1)/2.0)*0.05
            x=theta
            data.append({"round":r,"theta":theta,"x":x,"valid":True})
        proposal_mean=proposal_mean+learning_rate*(observation-proposal_mean)
        logs.append({"round":r,"proposal_mean_before":start,"proposal_mean_after":proposal_mean,"count":sims_per_round})
    return {"data":data,"proposal":{"mean":proposal_mean},"logs":logs}

if __name__ == "__main__":
    import json; print(json.dumps(run_rounds(), indent=2))
