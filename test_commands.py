# import json
import os
from contextlib import redirect_stdout
import io
import shutil
import unittest

import tracker
# from exceptions import InvalidUsageError
# import utils


class CommandLineArgsTestCase(unittest.TestCase):
    """Base class to test command line arguments"""
    @classmethod
    def setUpClass(cls):
        cls.parser = tracker.process_args()


class ListOptionTestCase(CommandLineArgsTestCase):
    """Test case for list option"""

    def test_list_option(self):
        """Test that the output is as expected"""
        expected_output = (
    	"Show                 Next episode   Rating   Title                 \n"
        "-------------------  -------------  -------  --------------------  \n"
        "Game of Thrones      S06E10         9.9      The Winds of Winter   \n"
        "Person of Interest   S05E01         9.5      B.S.O.D.              \n"
        )
        args = self.parser.parse_args(['--list', '--database-dir=example'])
        f = io.StringIO()
        with redirect_stdout(f):
            tracker.tracker(args)
        s = f.getvalue()
        self.assertEqual(s, expected_output)

    def test_list_fails_no_tracker(self):
        """Test that --list fails when no .tracker.json is present"""
        with self.assertRaises(tracker.InvalidUsageError):
            args = self.parser.parse_args(['--list'])
            tracker.tracker(args)

# Test subcommands
class DecArgumentTestCase(CommandLineArgsTestCase):
    """Test case for Dec argument"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.database_dir = 'example'
        cls.path_to_tracker = os.path.join(cls.database_dir, '.tracker.json')
        cls.path_to_backup_tracker = os.path.join(cls.database_dir, '.tracker.json.bak')

    def setUp(self):
        shutil.copyfile(self.path_to_tracker, self.path_to_backup_tracker)

    def test_dec_command(self):
        """Test that the dec command works as expected"""
        args = self.parser.parse_args(['--database-dir=example', 'dec', 'game of thrones'])
        expected_next_episode = 9
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.episode,
            expected_next_episode
        )

    def test_dec_by_five(self):
        """Test that we decrement by five episodes correctly"""
        args = self.parser.parse_args(['--database-dir=example', 'dec', 'game of thrones', '--by=5'])
        expected_next_episode = 5
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.episode,
            expected_next_episode
        )

    def test_dec_by_ten_correct_episode(self):
        """Test we decrement past a season boundry correctly"""
        args = self.parser.parse_args(['--database-dir=example', 'dec', 'game of thrones', '--by=10'])
        expected_next_episode = 10
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.episode,
            expected_next_episode
        )

    def test_dec_by_ten_correct_season(self):
        """Test we decrement past a season boundry correctly"""
        args = self.parser.parse_args(['--database-dir=example', 'dec', 'game of thrones', '--by=10'])
        expected_next_season = 5
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.season,
            expected_next_season
        )

    @unittest.skip('No short-code added')
    def test_dec_using_short_code(self):
        """Test that the tracker can be decremented using a short-code"""
        args = self.parser.parse_args(['--database-dir=example', 'dec', 'got'])
        expected_next_episode = 9
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.season,
            expected_next_episode
        )


    def tearDown(self):
        os.rename(self.path_to_backup_tracker, self.path_to_tracker)


class IncArgumentTestCase(CommandLineArgsTestCase):
    """Test case for Inc argument"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.database_dir = 'example'
        cls.path_to_tracker = os.path.join(cls.database_dir, '.tracker.json')
        cls.path_to_backup_tracker = os.path.join(cls.database_dir, '.tracker.json.bak')

    def setUp(self):
        shutil.copyfile(self.path_to_tracker, self.path_to_backup_tracker)

    def test_inc_command(self):
        """Test that the inc command works as expected"""
        args = self.parser.parse_args(['--database-dir=example', 'inc', 'game of thrones'])
        expected_next_episode = 1
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.episode,
            expected_next_episode
        )

    def test_inc_by_five(self):
        """Test that we increment by five episodes correctly"""
        args = self.parser.parse_args(['--database-dir=example', 'inc', 'game of thrones', '--by=5'])
        expected_next_episode = 5
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.episode,
            expected_next_episode
        )

    def test_inc_by_seven_correct_episode(self):
        """Test we increment past a season boundry correctly"""
        args = self.parser.parse_args(['--database-dir=example', 'inc', 'game of thrones', '--by=7'])
        expected_next_episode = 7
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.episode,
            expected_next_episode
        )

    def test_inc_by_ten_correct_season(self):
        """Test we increment past a season boundry correctly"""
        args = self.parser.parse_args(['--database-dir=example', 'inc', 'game of thrones', '--by=7'])
        expected_next_season = 7
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.season,
            expected_next_season
        )

    @unittest.skip('No short-code added')
    def test_inc_using_short_code(self):
        """Test that the tracker can be incremented using a short-code"""
        args = self.parser.parse_args(['--database-dir=example', 'inc', 'got'])
        expected_next_episode = 9
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(
            trackerdb._shows['game_of_thrones']._next.season,
            expected_next_episode
        )


    def tearDown(self):
        os.rename(self.path_to_backup_tracker, self.path_to_tracker)


if __name__ == '__main__':
    unittest.main()
