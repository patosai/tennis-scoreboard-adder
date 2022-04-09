#!/usr/bin/env python3

from moviepy.editor import *
import functools
import json
import sys


def parse_timestamp_string(timestamp):
    """ex. 1:14.567 -> 74.567"""
    parts = timestamp.split(':')
    [seconds, millis] = parts[-1].split('.')
    nonmilli_parts = parts[:-1] + [seconds]
    seconds = functools.reduce(lambda accumulator, item: 60*accumulator + int(item), nonmilli_parts, 0)
    millis = millis.ljust(3, '0')[:3]
    return seconds + (int(millis) * 0.001)


def validate_score_json(scores):
    assert isinstance(scores, list)
    for score in scores:
        assert 'timestamp' in score, "Needs a timestamp"
        if isinstance(score['timestamp'], str):
            score['timestamp'] = parse_timestamp_string(score['timestamp'])
        assert 'serving' in score, "Needs who's serving"
        assert score['serving'] in ["me", "them"], "'serving' should be 'me' or 'them', got: %s" % score['serving']
        assert isinstance(score['my_score'], list), "my_score needs to be a list"
        assert isinstance(score['their_score'], list), "their_score needs to be a list"
        assert len(score['my_score']) == len(score['their_score']), "player scores need to be the same length"
        if len(score['my_score']) > 0:
            assert score['my_score'][-1] in [0, 15, 30, 40, "AD"], "invalid me score: %s" % score['my_score'][-1]
            assert score['their_score'][-1] in [0, 15, 30, 40, "AD"], "invalid them score: %s" % score['their_score'][-1]
    return scores


def parse_score_file(filename):
    with open(filename) as file:
        scores = json.load(file)
    scores = validate_score_json(scores)
    return scores


def add_scores_to_video(scores, video_filename, save_instead_of_preview=False):
    scores.sort(key=lambda x: x['timestamp'])
    original_video = VideoFileClip(video_filename)

    COL_1_START = 0.03
    COL_SCORE_START = 0.14
    COL_SCORE_DELTA = 0.02

    ROW_1_START = 0.9
    ROW_2_START = 0.94

    clip_total_duration = original_video.duration
    composite_clip_components = [original_video]
    for score_idx, score in enumerate(scores):
        start = score['timestamp']
        end = scores[score_idx+1]['timestamp'] if score_idx != (len(scores)-1) else clip_total_duration
        duration = end - start

        my_name = "Patrick"
        opp_name = "White shirt"
        if score['serving'] == "me":
            my_name += "*"
        elif score['serving'] == "them":
            opp_name += "*"
        my_name_text = TextClip(my_name, fontsize=24, color='white', font="Helvetica Neue").set_position((COL_1_START, ROW_1_START), relative=True).set_start(start).set_duration(duration)
        opponent_text = TextClip(opp_name, fontsize=24, color='white', font="Helvetica Neue").set_position((COL_1_START, ROW_2_START), relative=True).set_start(start).set_duration(duration)
        composite_clip_components.append(my_name_text)
        composite_clip_components.append(opponent_text)

        for idx, my_score in enumerate(score['my_score']):
            new_text = TextClip(str(my_score), fontsize=24, color='white', font="Helvetica Neue").set_position((COL_SCORE_START + (idx*COL_SCORE_DELTA), ROW_1_START), relative=True).set_start(start).set_duration(duration)
            composite_clip_components.append(new_text)
        for idx, their_score in enumerate(score['their_score']):
            new_text = TextClip(str(their_score), fontsize=24, color='white', font="Helvetica Neue").set_position((COL_SCORE_START + (idx*COL_SCORE_DELTA), ROW_2_START), relative=True).set_start(start).set_duration(duration)
            composite_clip_components.append(new_text)

    video = CompositeVideoClip(composite_clip_components)

    # do some dirty hack to prevent "AttributeError: 'CompositeAudioClip' object has no attribute 'fps'"
    aud = video.audio.set_fps(44100)
    video = video.without_audio().set_audio(aud)

    if save_instead_of_preview:
        chopped_video_filename = video_filename.split('.')
        chopped_video_filename.insert(-1, "edited")
        new_filename = '.'.join(chopped_video_filename)
        print("saving to: " + new_filename)
        video.write_videofile(new_filename, codec="libx264")
    else:
        # run the preview
        video.preview()


if __name__ == "__main__":
    video_filename = sys.argv[1]
    score_filename = sys.argv[2]
    print("Video file: %s, score file: %s" % (video_filename, score_filename))
    scores = parse_score_file(score_filename)
    add_scores_to_video(scores, video_filename, save_instead_of_preview=True)