import math

from skill_prior import build_skill_schedule


def test_fixed_skill_within_episode_and_log_prior():
    schedule = build_skill_schedule(num_skills=4, episodes=5, horizon=3, seed=11)
    assert len(schedule["skills"]) == 5
    assert math.isclose(schedule["log_prior"], -math.log(4))
    for episode in range(5):
        episode_records = [r for r in schedule["records"] if r["episode"] == episode]
        assert len(episode_records) == 3
        assert {r["skill"] for r in episode_records} == {schedule["skills"][episode]}
        for record in episode_records:
            assert sum(record["conditioning"]) == 1
            assert record["conditioning"][record["skill"]] == 1
