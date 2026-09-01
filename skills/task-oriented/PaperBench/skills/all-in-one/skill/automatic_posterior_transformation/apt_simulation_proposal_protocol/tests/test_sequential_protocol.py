from sequential_protocol import run_two_round_protocol


def test_protocol_records_round_provenance():
    result = run_two_round_protocol(seed=7, simulations_per_round=3, observation=0.5)
    records = result["records"]
    assert len(records) == 6
    assert {item["round_index"] for item in records} == {1, 2}
    assert all(item["within_prior_support"] for item in records)
    round1 = [item for item in records if item["round_index"] == 1]
    round2 = [item for item in records if item["round_index"] == 2]
    assert all(item["proposal_name"] == "prior" for item in round1)
    assert all(item["proposal_name"] == "posterior_analytic" for item in round2)


def test_proposal_update_is_posterior_derived():
    result = run_two_round_protocol(seed=9, simulations_per_round=2, observation=1.0)
    update = result["proposal_updates"][0]
    assert update["previous_proposal"]["name"] == "prior"
    assert update["next_proposal"]["name"] == "posterior_analytic"
    assert update["next_proposal"]["variance"] < update["previous_proposal"]["variance"]
