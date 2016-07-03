import json
import unittest

# import requests

import tracker
# import utils


class IOShowTestCase(unittest.TestCase):
    """Test real IO in the Show class"""
    def test_request_show_info(self):
        """Test that a real IO request contains correct data"""
        show = tracker.Show(title='Game of Thrones')
        with open('got_s01_response.json', 'r') as f:
            expected_response = json.load(f)
        self.assertDictEqual(
            show.request_show_info(season=1),
            expected_response,
        )

    def test_show_does_not_exist(self):
        """Test that we raise a show not found error"""
        show = tracker.Show(title='The Adventures of Moonboy and Patchface')
        with self.assertRaises(tracker.ShowNotFoundError):
            show.populate_seasons()


# class IOSho


if __name__ == '__main__':
    unittest.main()
