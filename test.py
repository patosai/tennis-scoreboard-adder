import unittest

from . import core


class ScoreFileParserTest(unittest.TestCase):
    def test_validate_score_json(self):
        good_case_two_sets = [{'timestamp': 10.3, 'player1_score': [6, 4, 15], 'player2_score': [3, 2, 30]}]
        self.assertEqual(good_case_two_sets, core.validate_score_json(good_case_two_sets))

        good_case_no_sets = [{'timestamp': 10.89, 'player1_score': [15], 'player2_score': [30]}]
        self.assertEqual(good_case_no_sets, core.validate_score_json(good_case_no_sets))

        bad_game_score = [{'timestamp': 10.3, 'player1_score': [6, 4, 15], 'player2_score': [3, 2, 31]}]
        with self.assertRaises(AssertionError):
            core.validate_score_json(bad_game_score)

        no_timestamp = [{'player1_score': [2, 15], 'player2_score': [5, 40]}]
        with self.assertRaises(AssertionError):
            core.validate_score_json(no_timestamp)


if __name__ == '__main__':
    unittest.main()