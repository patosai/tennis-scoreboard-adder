import unittest

from . import core


class ScoreFileParserTest(unittest.TestCase):
    def test_validate_score_json(self):
        good_case_two_sets = [{'timestamp': 10.3, 'my_score': [6, 4, 15], 'their_score': [3, 2, 30], 'serving': 'them'}]
        self.assertEqual(good_case_two_sets, core.validate_score_json(good_case_two_sets))

        good_case_no_sets = [{'timestamp': 10.89, 'my_score': [15], 'their_score': [30], 'serving': 'me'}]
        self.assertEqual(good_case_no_sets, core.validate_score_json(good_case_no_sets))

        bad_game_score = [{'timestamp': 10.3, 'my_score': [6, 4, 15], 'their_score': [3, 2, 31], 'serving': 'me'}]
        with self.assertRaises(AssertionError):
            core.validate_score_json(bad_game_score)

        no_timestamp = [{'my_score': [2, 15], 'their_score': [5, 40]}]
        with self.assertRaises(AssertionError):
            core.validate_score_json(no_timestamp)

    def test_parse_timestamp_string(self):
        self.assertEqual(74.567, core.parse_timestamp_string("1:14.567"))
        self.assertEqual(30.1, core.parse_timestamp_string("30.100"))
        self.assertEqual(30.9, core.parse_timestamp_string("30.9"))
        self.assertEqual(9059.9, core.parse_timestamp_string("2:30:59.9"))


if __name__ == '__main__':
    unittest.main()