#!/usr/bin/env python3

from moviepy.editor import *
import json


def validate_score_json(scores):
    assert isinstance(scores, list)
    for score in scores:
        assert 'timestamp' in score, "Needs a timestamp"
        assert isinstance(score['player1_score'], list), "player1_score needs to be a list"
        assert isinstance(score['player2_score'], list), "player2_score needs to be a list"
        assert len(score['player1_score']) == len(score['player2_score']), "player scores need to be the same length"
        if len(score['player1_score']) > 0:
            assert score['player1_score'][-1] in [0, 15, 30, 40, "AD"], "invalid player1 score: %s" % score['player1_score'][-1]
            assert score['player2_score'][-1] in [0, 15, 30, 40, "AD"], "invalid player2 score: %s" % score['player2_score'][-1]
    return scores


def parse_score_file(filename):
    with open(filename) as file:
        scores = json.load(file)
    validate_score_json(scores)
    return scores


def add_scores_to_video(scores, video_filename):
    scores.sort(key=lambda x: x['timestamp'])
    clip = VideoFileClip(video_filename)
    my_name_text = TextClip("Patrick", fontsize=24, color='white', font="Helvetica Neue").set_position((0.03, 0.9), relative=True).set_duration(10)
    opponent_text = TextClip("Opponent", fontsize=24, color='white', font="Helvetica Neue").set_position((0.03, 0.94), relative=True).set_duration(10)
    video = CompositeVideoClip([clip, my_name_text, opponent_text])
    video.preview()


if __name__ == "__main__":
    add_scores_to_video([], "/Users/p/Desktop/4-3-2022.mov")