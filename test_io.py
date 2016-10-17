import json
import os
import shutil
from tempfile import TemporaryDirectory, NamedTemporaryFile
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


class TrackerTestCase(unittest.TestCase):
    """Test case for ShowDatabase class"""
    @classmethod
    def setUpClass(cls):
        watchlist = 'test_watchlist.txt'
        cls.testdir = os.path.join(os.path.expanduser('~'), 'showtest1')
        show_db = tracker.ShowDatabase(cls.testdir)
        show_db.create_db_from_watchlist(watchlist)

        cls.trackerdb = tracker.TrackerDatabase(cls.testdir)
        cls.trackerdb.create_tracker_from_watchlist(watchlist, showdb=show_db)

    def test_create_database(self):
        """Test database is correctly created as a Database instance"""
        self.assertIsInstance(self.trackerdb, tracker.TrackerDatabase)

    def test_write_database(self):
        """Test database is correctly written to disk"""
        self.trackerdb.write_db()
        self.assertTrue(os.path.exists(self.trackerdb.path_to_db))

    def test_show_in_database(self):
        """Check that we correctly return a TrackedShow instance"""
        self.assertTrue('game_of_thrones' in self.trackerdb)

    @classmethod
    def tearDownClass(cls):
        os.remove(os.path.join(cls.testdir, '.tracker.json'))
        os.rmdir(cls.testdir)


class TrackerDBLoadTestCase(unittest.TestCase):
    """Load an existing TrackerDB"""
    @classmethod
    def setUpClass(cls):
        watchlist = 'test_watchlist.txt'
        cls.testdir = os.path.join(os.path.expanduser('~'), 'showtest1')
        # Protect against a .showdb file already existing in this directory
        if os.path.exists(os.path.join(cls.testdir, '.showdb.json')):
            os.remove(os.path.join(cls.testdir, '.showdb.json'))

        # Protect against a .tracker file already existing in this directory
        if os.path.exists(os.path.join(cls.testdir, '.tracker.json')):
            os.remove(os.path.join(cls.testdir, '.tracker.json'))

        showdb = tracker.ShowDatabase(cls.testdir)
        showdb.create_db_from_watchlist(watchlist)
        showdb.write_db()

        trackerdb = tracker.TrackerDatabase(cls.testdir)
        trackerdb.create_tracker_from_watchlist(watchlist)
        trackerdb.write_db()


    def test_load_database_good_next_episode(self):
        """Test that we correctly build objects when loading from file"""
        trackerdb = tracker.load_database(os.path.join(self.testdir, '.tracker.json'))

        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.episode,
            10
        )

    def test_load_database_good_prev_episode(self):
        """Test that we correctly build objects when loading from file"""
        trackerdb = tracker.load_database(os.path.join(self.testdir, '.tracker.json'))

        self.assertEqual(
            trackerdb._shows['game_of_thrones']._prev.episode,
            9
        )

    @classmethod
    def tearDownClass(cls):
        os.remove(os.path.join(cls.testdir, '.tracker.json'))
        os.remove(os.path.join(cls.testdir, '.showdb.json'))
        os.rmdir(cls.testdir)


class WatchlistOptionTestCase(unittest.TestCase):
    """Test case for adding shows via --watchlist option"""
    @classmethod
    def setUpClass(cls):
        cls.parser = tracker.process_args()
        cls.database_dir = 'example'
        cls.path_to_tracker = os.path.join(cls.database_dir, '.tracker.json')
        cls.path_to_showdb = os.path.join(cls.database_dir, '.showdb.json')


    def test_create_new_tracker_with_watchlist(self):
        """Test we can create a new trackerdb with a watchlist"""
        with TemporaryDirectory() as dirname:
            watchlist_path = 'test_watchlist.txt'
            args = self.parser.parse_args(
                [
                    '--database-dir={}'.format(dirname),
                    '--watchlist={}'.format(watchlist_path),
                ]
            )
            tracker.tracker(args)
            _, trackerdb = tracker.load_all_dbs(dirname)
            self.assertIsInstance(trackerdb, tracker.TrackerDatabase)

    def test_add_show_in_showdb_to_existing_tracker_with_watchlist(self):
        """Test adding of a show which is in the showdb to an existing tracker"""
        expected_tracked_show = tracker.TrackedShow('House', _next_episode='S08E01')
        with TemporaryDirectory() as dirname:
            # Some setup
            shutil.copy(self.path_to_tracker, dirname)
            shutil.copy(self.path_to_showdb, dirname)

            sdb, tdb = tracker.load_all_dbs(dirname)
            sdb.path_to_db = os.path.join(dirname, '.showdb.json')
            tdb.path_to_db = os.path.join(dirname, '.tracker.json')
            sdb.write_db()
            tdb.write_db()

            with NamedTemporaryFile('w+t') as f:
                f.write('house s08e01')
                f.seek(0)
                watchlist_path = f.name
                args = self.parser.parse_args(
                    [
                        '--database-dir={}'.format(dirname),
                        '--watchlist={}'.format(watchlist_path),
                    ]
                )
                tracker.tracker(args)
            showdb, trackerdb = tracker.load_all_dbs(dirname)
            expected_tracked_show._set_next_prev(showdb)
            self.assertEqual(trackerdb._shows['house'], expected_tracked_show)

    def test_add_show_via_api_request_to_existing_tracker_with_watchlist(self):
        """Test adding of a show which is not in the showdb to an existing tracker"""
        expected_tracked_show = tracker.TrackedShow('Narcos')
        with TemporaryDirectory() as dirname:
            # Some setup
            shutil.copy(self.path_to_tracker, dirname)
            shutil.copy(self.path_to_showdb, dirname)

            sdb, tdb = tracker.load_all_dbs(dirname)
            sdb.path_to_db = os.path.join(dirname, '.showdb.json')
            tdb.path_to_db = os.path.join(dirname, '.tracker.json')
            sdb.write_db()
            tdb.write_db()

            with NamedTemporaryFile('w+t') as f:
                f.write('narcos S01E01')
                f.seek(0)
                watchlist_path = f.name
                args = self.parser.parse_args(
                    [
                        '--database-dir={}'.format(dirname),
                        '--watchlist={}'.format(watchlist_path),
                    ]
                )
                tracker.tracker(args)
            showdb, trackerdb = tracker.load_all_dbs(dirname)
            expected_tracked_show._set_next_prev(showdb)
            self.assertEqual(trackerdb._shows['narcos'], expected_tracked_show)

    def test_note_preserved_update_existing_tracked_show(self):
        """Test that notes are preserved when updating an existing show via watchlist"""
        expected_tracked_show = tracker.TrackedShow(
            title='Person of Interest',
            notes='new season',
            _next_episode='S02E08',
        )
        with TemporaryDirectory() as dirname:
            # Some setup
            shutil.copy(self.path_to_tracker, dirname)
            shutil.copy(self.path_to_showdb, dirname)

            sdb, tdb = tracker.load_all_dbs(dirname)
            sdb.path_to_db = os.path.join(dirname, '.showdb.json')
            tdb.path_to_db = os.path.join(dirname, '.tracker.json')
            sdb.write_db()
            tdb.write_db()

            with NamedTemporaryFile('w+t') as f:
                f.write('person of interest s02e08')
                f.seek(0)
                watchlist_path = f.name
                args = self.parser.parse_args(
                    [
                        '--database-dir={}'.format(dirname),
                        '--watchlist={}'.format(watchlist_path),
                    ]
                )
                tracker.tracker(args)
            showdb, trackerdb = tracker.load_all_dbs(dirname)
            expected_tracked_show._set_next_prev(showdb)
            self.assertEqual(trackerdb._shows['person_of_interest'], expected_tracked_show)


if __name__ == '__main__':
    unittest.main()
