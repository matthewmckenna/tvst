import json
import os
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

    def test_got_film_with_same_name(self):
        """Test that we recognise when we get a film instead of a show"""
        show = tracker.Show(title='Fargo')
        with self.assertRaises(tracker.FoundFilmError):
            show.populate_seasons()


class ShowDBTestCase(unittest.TestCase):
    """Test case for ShowDatabase class"""
    @classmethod
    def setUpClass(cls):
        cls.testdir = os.path.join(os.path.expanduser('~'), 'showtest1')
        cls.show_db = tracker.ShowDatabase(cls.testdir)
        cls.show_db.create_db_from_watchlist('test_watchlist.txt')

    def test_create_database(self):
        """Test database is correctly created as a Database instance"""
        self.assertIsInstance(self.show_db, tracker.ShowDatabase)

    def test_write_database(self):
        """Test database is correctly written to disk"""
        self.show_db.write_db()
        self.assertTrue(os.path.exists(self.show_db.path_to_db))

    def test_get_show_db_entry_show_present(self):
        """Check that we correctly return a TrackedShow instance"""
        entry = tracker.get_show_database_entry(self.show_db, 'game_of_thrones')
        self.assertIsInstance(entry, tracker.Show)

    def test_get_show_db_entry_show_not_present(self):
        """Check that we raise a ShowNotFoundError if the show is not in the db"""
        with self.assertRaises(tracker.ShowNotFoundError):
            tracker.get_show_database_entry(
                self.show_db,
                'mr_robot'
            )

    @classmethod
    def tearDownClass(cls):
        os.remove(os.path.join(cls.testdir, '.showdb.json'))
        os.rmdir(cls.testdir)


class ShowDBLoadTestCase(unittest.TestCase):
    """Test case for loading from a saved ShowDatabase"""
    @classmethod
    def setUpClass(cls):
        cls.testdir = os.path.join(os.path.expanduser('~'), 'showtest1')
        # Protect against a .showdb file already existing in this directory
        if os.path.exists(os.path.join(cls.testdir, '.showdb.json')):
            os.remove(os.path.join(cls.testdir, '.showdb.json'))
        db = tracker.ShowDatabase(cls.testdir)
        db.create_db_from_watchlist('test_watchlist.txt')
        db.write_db()

    def test_load_database(self):
        """Test that we correctly build objects when loading from file"""
        show_db = tracker.load_database(os.path.join(self.testdir, '.showdb.json'))

        self.assertEqual(
            show_db._shows['game_of_thrones']._seasons[5]._episodes[9].title,
            'The Winds of Winter'
        )

    @classmethod
    def tearDownClass(cls):
        os.remove(os.path.join(cls.testdir, '.showdb.json'))
        os.rmdir(cls.testdir)


if __name__ == '__main__':
    unittest.main()
