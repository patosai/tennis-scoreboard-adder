#!/usr/bin/env python3

from moviepy.editor import *
import functools
import json
import os
import re
import subprocess
import sys


def parse_timestamp_string(timestamp):
    """ex. 1:14.567 -> 74.567"""
    parts = timestamp.split(':')
    seconds = ""
    millis = ""
    last_part = parts[-1].split('.')
    seconds = last_part[0]
    if len(last_part) > 1:
        millis = last_part[1]
    nonmilli_parts = parts[:-1] + [seconds]
    seconds = functools.reduce(lambda accumulator, item: 60*accumulator + int(item), nonmilli_parts, 0)
    millis = millis.ljust(3, '0')[:3]
    return seconds + (int(millis) * 0.001)


def validate_score_json(scores):
    assert isinstance(scores, list)
    seen_timestamps = set()
    dupe_timestamps = []
    for score in scores:
        assert 'timestamp_start' in score, "score needs a start timestamp"
        assert 'timestamp_end' in score, "score needs a start timestamp"
        original_start = score['timestamp_start']
        original_end = score['timestamp_end']
        if isinstance(score['timestamp_start'], str):
            score['timestamp_start'] = parse_timestamp_string(score['timestamp_start'])
        if isinstance(score['timestamp_end'], str):
            score['timestamp_end'] = parse_timestamp_string(score['timestamp_end'])
        assert score['timestamp_start'] < score['timestamp_end'], "Start timestamp needs to be the before timestamp. Got start: %s, end: %s" % (original_start, original_end)
        assert 'serving' in score, "score needs who's serving"
        assert score['serving'] in ["me", "them"], "'serving' should be 'me' or 'them', got: %s" % score['serving']
        assert isinstance(score['my_score'], list), "my_score needs to be a list"
        assert isinstance(score['their_score'], list), "their_score needs to be a list"
        assert len(score['my_score']) == len(score['their_score']), "player scores need to be the same length"
        if len(score['my_score']) > 0:
            assert (score['my_score'][-1] in [0, 15, 30, 40, "AD"] or (len(score['my_score']) == 3 and 0 <= score['my_score'][2])), "invalid me score: %s" % score['my_score'][-1]
            assert (score['their_score'][-1] in [0, 15, 30, 40, "AD"] or (len(score['their_score']) == 3 and 0 <= score['their_score'][2])), "invalid them score: %s" % score['their_score'][-1]

        if original_start in seen_timestamps:
            dupe_timestamps.append(original_start)
        else:
            seen_timestamps.add(original_start)
    assert len(set([score['timestamp_start'] for score in scores])) == len(scores), "Duplicate score timestamp found: %s" % str(dupe_timestamps)
    scores.sort(key=lambda x: x['timestamp_start'])
    return scores


def validate_notes(notes, scores):
    assert isinstance(notes, list)
    for note in notes:
        assert 'message' in note, "note needs a message"
        assert 'timestamp' in note, "note needs a timestamp"
        if isinstance(note['timestamp'], str):
            note['timestamp'] = parse_timestamp_string(note['timestamp'])

        score_clips_containing_note_with_buffer_at_end = list(filter(lambda x: (x['timestamp_start'] <= note['timestamp'] <= (x['timestamp_end']-1)), scores))
        assert len(score_clips_containing_note_with_buffer_at_end) >= 1, "didn't find score clip containing note with 1 sec buffer at end: %s" % note
    notes.sort(key=lambda x: x['timestamp'])
    return notes


def parse_config_file(filename):
    with open(filename) as file:
        config = json.load(file)
    assert config['name']
    assert config['opponent_name']
    config['scores'] = validate_score_json(config['scores'])
    config['notes'] = validate_notes(config['notes'], config['scores'])
    return config


def at_most_one(input_list):
    assert len(input_list) <= 1, "expected at most one item"
    return input_list[0] if input_list else None


def filename_with_added_last_part(filename, last_part):
    filename_split = filename.split(".")
    filename_split.insert(-1, last_part)
    return ".".join(filename_split)


def displaymatrix_rotation(video_filename):
    output = subprocess.check_output(["ffprobe", "-of", "json", "-show_entries", "stream", video_filename])
    output_json = json.loads(output)
    streams = output_json['streams']
    video_streams = [stream for stream in streams if stream["codec_type"] == "video"]
    video_stream = at_most_one(video_streams)
    side_data = video_stream.get("side_data_list", [])
    display_matrices = [data for data in side_data if data["side_data_type"] == "Display Matrix"]
    display_matrix = at_most_one(display_matrices) or {}
    return display_matrix.get("rotation", 0)


def create_new_video_using_ffmpeg(config, video_filename, remove_intermediate_files=True):
    """Given the config, creates many clips quickly from the video using ffmpeg.
    Due to the quick clipping mechanism, clip durations likely won't match exactly the duration specified in the config,
    so clip durations are also returned"""
    scores = config['scores']

    video_filename_split = video_filename.split(".")
    extension = video_filename_split[-1]
    clip_output_folder = ".".join(video_filename_split[:-1])
    os.makedirs(clip_output_folder, exist_ok=False)
    files = []
    for idx, score in enumerate(scores):
        start_in_original_video = score['timestamp_start']
        end_in_original_video = score['timestamp_end']
        duration = end_in_original_video - start_in_original_video
        filename = "{}.{}.ts".format(str(idx).zfill(3), extension)
        complete_filename = os.path.join(clip_output_folder, filename)
        subprocess.call(["ffmpeg",
                         "-ss", str(start_in_original_video),
                         "-i", str(video_filename),
                         "-to", str(duration),
                         "-c", "copy",
                         complete_filename])
        files.append(complete_filename)

    concat_filename = filename_with_added_last_part(video_filename, "clipped")

    subprocess.call(["ffmpeg",
                     "-i", "concat:" + "|".join(files),
                     "-c", "copy",
                     concat_filename])
    if remove_intermediate_files:
        subprocess.call(["rm", "-rf", clip_output_folder])

    # because converting to .ts removes displaymatrix rotation, set displaymatrix rotation metadata again
    # so no reencode is necessary
    metadata_filename = filename_with_added_last_part(concat_filename, "metadata")
    rotation = displaymatrix_rotation(video_filename)
    subprocess.call(["ffmpeg",
                     "-i", concat_filename,
                     "-metadata:s:v:0", f"rotate={rotation}",
                     "-c", "copy",
                     metadata_filename])
    if remove_intermediate_files:
        subprocess.call(["rm", concat_filename])

    # TODO: clip length can be obtained from the initial ffmpeg call to create the clip
    clip_lengths = [float(subprocess.check_output(["ffprobe",
                                                   "-v",
                                                   "error",
                                                   "-show_entries",
                                                   "format=duration",
                                                   "-of",
                                                   "default=noprint_wrappers=1:nokey=1",
                                                   file])) for file in files]

    return metadata_filename, clip_lengths


def add_labels_to_video(config, video_filename, clip_lengths, save_instead_of_preview=False):
    original_video = VideoFileClip(video_filename)

    COL_1_START = 0.03
    COL_SCORE_START = 0.14
    COL_SCORE_DELTA = 0.02

    ROW_1_START = 0.9
    ROW_2_START = 0.94

    current_note_index = 0

    composite_clip_components = [original_video]
    running_clip_duration_seconds = 0
    for idx, score in enumerate(config['scores']):
        start_in_original_video = score['timestamp_start']
        end_in_original_video = score['timestamp_end']
        duration = clip_lengths[idx]

        start = running_clip_duration_seconds

        my_name = config['name']
        opponent_name = config['opponent_name']
        if score['serving'] == "me":
            my_name += " •"
        elif score['serving'] == "them":
            opponent_name += " •"
        my_name_text = TextClip(my_name, fontsize=24, color='white', font="Helvetica Neue").set_position((COL_1_START, ROW_1_START), relative=True).set_start(start).set_duration(duration)
        opponent_text = TextClip(opponent_name, fontsize=24, color='white', font="Helvetica Neue").set_position((COL_1_START, ROW_2_START), relative=True).set_start(start).set_duration(duration)
        composite_clip_components.append(my_name_text)
        composite_clip_components.append(opponent_text)

        for idx, my_score in enumerate(score['my_score']):
            new_text = TextClip(str(my_score), fontsize=24, color='white', font="Helvetica Neue").set_position((COL_SCORE_START + (idx*COL_SCORE_DELTA), ROW_1_START), relative=True).set_start(start).set_duration(duration)
            composite_clip_components.append(new_text)
        for idx, their_score in enumerate(score['their_score']):
            new_text = TextClip(str(their_score), fontsize=24, color='white', font="Helvetica Neue").set_position((COL_SCORE_START + (idx*COL_SCORE_DELTA), ROW_2_START), relative=True).set_start(start).set_duration(duration)
            composite_clip_components.append(new_text)

        # add note
        if current_note_index < len(config['notes']):
            note = config['notes'][current_note_index]
            if start_in_original_video <= note['timestamp'] <= end_in_original_video:
                note_start = start + (note['timestamp'] - start_in_original_video)
                note_duration = 0.5
                note_text = TextClip(note['message'], fontsize=24, color='white', font="Helvetica Neue").set_position((0.5, ROW_1_START), relative=True).set_start(note_start).set_duration(note_duration)
                composite_clip_components.append(note_text)
                current_note_index += 1

        running_clip_duration_seconds += duration

    video = CompositeVideoClip(composite_clip_components)

    if save_instead_of_preview:
        chopped_video_filename = video_filename.split('.')
        chopped_video_filename.insert(-1, "edited")
        new_filename = '.'.join(chopped_video_filename)
        print("saving to: " + new_filename)
        video.write_videofile(new_filename, codec="mpeg4", bitrate='8000k')

        # moviepy causes audio to be out of sync with video, so take old audio and mux it with new video
        final_filename = chopped_video_filename.copy()
        final_filename.insert(-1, "final")
        final_filename = '.'.join(final_filename)
        subprocess.call(["ffmpeg",
                         "-an", "-i", new_filename,
                         "-vn", "-i", video_filename,
                         "-c:a", "copy",
                         "-c:v", "copy",
                         final_filename])
    else:
        # run the preview
        video.preview()


def main():
    video_filename = sys.argv[1]
    score_filename = sys.argv[2]
    print("Video file: %s, score file: %s" % (video_filename, score_filename))
    config = parse_config_file(score_filename)
    clipped_video, clip_lengths = create_new_video_using_ffmpeg(config, video_filename, remove_intermediate_files=False)
    add_labels_to_video(config, clipped_video, clip_lengths, save_instead_of_preview=True)


if __name__ == "__main__":
    main()