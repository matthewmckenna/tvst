import json
import os
import unittest

# import requests

import tracker
# import utils


@unittest.skip
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

    def test_got_film_with_same_name(self):
        """Test that we recognise when we get a film instead of a show"""
        show = tracker.Show(title='Fargo')
        with self.assertRaises(tracker.FoundFilmError):
            show.populate_seasons()


# @unittest.skip
class ShowDBTestCase(unittest.TestCase):
    """Test case for ShowDatabase class"""
    def setUp(self):
        self.testdir = os.path.join(os.path.expanduser('~'), 'showtest1')

    @unittest.skip
    def test_create_database(self):
        """Test database is correctly created as a Database instance"""
        show_db = tracker.ShowDatabase(self.testdir, watchlist_path='test_watchlist.txt')
        # show_db.write_database()
        self.assertIsInstance(show_db, tracker.Database)

    # @unittest.skip
    def test_write_database(self):
        """Test database is correctly written to disk"""
        show_db = tracker.ShowDatabase(self.testdir, watchlist_path='test_watchlist.txt')
        show_db.write_database()

        self.assertTrue(os.path.exists(show_db.path_to_database))

    @unittest.skip
    def test_load_database(self):
        """Test that we correctly build objects when loading from file"""
        show_db = tracker.load_database(os.path.join(self.testdir, '.showdb.json'))

        self.assertEqual(
            show_db._shows['game_of_thrones']._seasons[5]._episodes[9].title,
            'The Winds of Winter'
        )

    # def tearDown(self):
    #     os.remove(os.path.join(self.testdir, '.showdb.json'))
    #     # os.rmdir(os.path.join(self.testdir))


if __name__ == '__main__':
    unittest.main()
