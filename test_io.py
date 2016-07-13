import json
import os
import unittest

# import requests

import tracker
# import utils


@unittest.skip('Debugging..')
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


class ShowDBTestCase(unittest.TestCase):
    """Test case for ShowDatabase class"""
    # def setUp(self):
    #
    #     NamedTemporaryFile(dir=os.path.join(userdir, '.showtracker'))
    def test_create_database(self):
        # with TemporaryDirectory() as tmpdir:
            # print('tmpdir={}'.format(tmpdir))
            # self.assertFalse(True)
        testdir = os.path.join(os.path.expanduser('~'), 'showtest1')
        show_db = tracker.ShowDatabase(testdir, watchlist='./test_watchlist.txt')
        # show_db.create_database()
        # print(show_db._shows)
        show_db.write_database()


if __name__ == '__main__':
    unittest.main()
