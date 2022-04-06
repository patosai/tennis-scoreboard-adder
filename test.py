import unittest

from . import core


class ScoreFileParserTest(unittest.TestCase):
    def test_validate_score_json(self):
        good_case = [{'timestamp': 10.3, 'player1_score': [6, 4, 15], 'player2_score': [3, 2, 30]}]
        self.assertEqual(good_case, core.validate_score_json(good_case))

        bad_game_score = [{'timestamp': 10.3, 'player1_score': [6, 4, 15], 'player2_score': [3, 2, 31]}]
        with self.assertRaises(AssertionError):
            core.validate_score_json(bad_game_score)


if __name__ == '__main__':
    unittest.main()