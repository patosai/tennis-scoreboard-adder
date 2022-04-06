from moviepy.editor import *
import json


def validate_score_json(scores):
    assert isinstance(scores, list)
    for score in scores:
        assert score['timestamp'], "Needs a timestamp"
        assert isinstance(score['player1_score'], list), "player1_score needs to be a list"
        assert isinstance(score['player2_score'], list), "player2_score needs to be a list"
        assert len(score['player1_score']) == len(score['player2_score']), "player scores need to be the same length"
        if len(score['player1_score']) > 0:
            assert score['player1_score'][-1] in [0, 15, 30, 40, "AD"], "invalid player1 score: %s" % score['player1_score'][-1]
            assert score['player2_score'][-1] in [0, 15, 30, 40, "AD"], "invalid player2 score: %s" % score['player2_score'][-1]
    scores.sort(key=lambda x: x['timestamp'])
    return scores


def parse_score_file(filename):
    with open(filename) as file:
        scores = json.load(file)
    validate_score_json(scores)
    return scores
