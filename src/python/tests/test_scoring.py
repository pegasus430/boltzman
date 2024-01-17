from core.aiprediction import AIPrediction
from tests.test_utils import generate_dummy_network
from unittest.mock import patch

print (generate_dummy_network)
initial_ts = 1619197227
def time_generator():
    global initial_ts
    initial_ts +=100
    return initial_ts

data = [
        {"p_points" : [30.23, 30.5032, 10.5012, 10.503, 20.0125],
        "r_points" : [30.23, 31.5031, 12.5012, 11.5030, 30.0025],
        "score" : 0.3956314076920816},
        {"p_points" : [1025.45,3000, 1500],
        "r_points" : [1000.455,3100, 1800],
        "score" : 0.7839175114461512}

]


def test_scores():
    with patch("workers.aitradetask.config.current_time", wraps=time_generator) as mock_obj:
        for test in data:
            n = generate_dummy_network(output_size = len(test["p_points"]))
            p_points = [30.23, 30.5032, 10.5012, 10.503, 20.0125]
            r_points = [30.23, 31.5031, 12.5012, 11.5030, 30.0025]
            prediction = AIPrediction(n,0, test["p_points"])
            score = prediction.calculate_score(test["p_points"], test["r_points"])
            assert (score == test["score"])

