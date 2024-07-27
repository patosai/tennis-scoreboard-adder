This adds a scoreboard to a video of a tennis match (or any sport). This tool takes in the video and a JSON file, and generates a scoreboard at the bottom left of the video.

To use: `./core.py [video filename] [score filename]`

Score file JSON format
-----------
The JSON file must be an array of objects, with the following properties:
- timestamp: a float, or str in `HH:MM:SS.SSS` format, that represents when the point starts
- my_score: an array representing game count in each set, with the last element being my score of the current game
- their_score: same as `my_score`, but for the opponent
- serving: a string denoting who is serving the current point. Must be one of `me` or `them`


Requirements
-----------
- requires ffmpeg and imagemagick
- pip requirements