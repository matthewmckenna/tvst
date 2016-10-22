# import json
import os
from contextlib import redirect_stdout
import io
import shutil
from tempfile import TemporaryDirectory
import unittest

import tracker
from exceptions import (
    FoundFilmError,
    InvalidUsageError,
    SeasonOutOfBoundsError,
    ShowAlreadyTrackedError,
    ShowNotFoundError,
    ShowNotTrackedError,
)
import utils


class CommandLineArgsTestCase(unittest.TestCase):
    """Base class to test command line arguments"""
    @classmethod
    def setUpClass(cls):
        cls.parser = tracker.process_args()


class TempTrackerSetupTestCase(unittest.TestCase):
    """Base class to setup environment for tests which modify the tracker"""
    @classmethod
    def setUpClass(cls):
        cls.parser = tracker.process_args()
        cls.database_dir = 'example'
        cls.path_to_tracker = os.path.join(cls.database_dir, '.tracker.json')
        cls.path_to_backup_tracker = os.path.join(cls.database_dir, '.tracker.json.bak')

    def setUp(self):
        shutil.copyfile(self.path_to_tracker, self.path_to_backup_tracker)

    def tearDown(self):
        os.rename(self.path_to_backup_tracker, self.path_to_tracker)


class AddShowTestCase(TempTrackerSetupTestCase):
    """Test case for adding shows"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path_to_showdb = os.path.join(cls.database_dir, '.showdb.json')
        cls.path_to_backup_showdb = os.path.join(cls.database_dir, '.showdb.json.bak')
        cls.path_to_master_showdb = os.path.join('.showdbmaster', '.showdb.json')
        shutil.copyfile(cls.path_to_showdb, cls.path_to_backup_showdb)
        shutil.copyfile(cls.path_to_master_showdb, cls.path_to_showdb)

    @classmethod
    def tearDownClass(cls):
        os.rename(cls.path_to_backup_showdb, cls.path_to_showdb)

    def test_add_show(self):
        """Test that we correctly add a show"""
        show = 'house'
        args = self.parser.parse_args(['--database-dir=example', 'add', show])
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertTrue(show in trackerdb)

    def test_add_show_set_next_episode(self):
        """Test that we can add a show and set the next episode at the same time correctly"""
        show = 'house s07e21'
        args = self.parser.parse_args(['--database-dir=example', 'add', show])
        expected_tracked_show = tracker.TrackedShow(
            title='House',
            _next_episode='S07E21',
        )
        tracker.tracker(args)
        showdb, trackerdb = tracker.load_all_dbs(self.database_dir)
        expected_tracked_show._set_next_prev(showdb)
        self.assertEqual(expected_tracked_show, trackerdb._shows['house'])

    def test_add_show_bad_season_episode_code(self):
        """Test that we raise an OutofBoundsError for a bad season-episode code"""
        show = 'house s99e99'
        args = self.parser.parse_args(['--database-dir=example', 'add', show])
        with self.assertRaises(SeasonOutOfBoundsError):
            tracker.tracker(args)

    def test_add_show_and_short_code(self):
        """Test adding a show and short-code at the same time"""
        show = 'supernatural'
        args = self.parser.parse_args(['--database-dir=example', 'add', show, '--short-code=spn'])
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(trackerdb._shows[show].short_code, 'SPN')

    def test_add_show_and_note(self):
        """Test adding a show and note at the same time"""
        show = 'supernatural'
        note = 'returns 14/10/2016'
        args = self.parser.parse_args(['--database-dir=example', 'add', show, '--note', note])
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(trackerdb._shows[show].notes, note)

    def test_add_show_short_code_and_note(self):
        """Test adding a show, short-code and note at the same time"""
        show = 'Supernatural'
        note = 'returns 14/10/2016'
        expected_tracked_show = tracker.TrackedShow(
            title=show,
            short_code='SPN',
            notes=note,
        )
        args = self.parser.parse_args(
            [
                '--database-dir=example',
                'add',
                show,
                '--short-code=spn',
                '--note',
                note,
            ]
        )
        tracker.tracker(args)
        showdb, trackerdb = tracker.load_all_dbs(self.database_dir)
        expected_tracked_show._set_next_prev(showdb)
        self.assertEqual(expected_tracked_show, trackerdb._shows['supernatural'])

    def test_add_short_code_using_short_option(self):
        """Test that the short-option works for adding a short-code"""
        show = 'supernatural'
        args = self.parser.parse_args(['--database-dir=example', 'add', show, '-c', 'spn'])
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(trackerdb._shows[show].short_code, 'SPN')

    def test_add_short_code_existing_show(self):
        """Test adding a short-code to an existing show"""
        show = 'game of thrones'
        lshow = utils.lunderize(show)
        args = self.parser.parse_args(['--database-dir=example', 'add', show, '-c', 'got'])
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(trackerdb._shows[lshow].short_code, 'GOT')

    def test_add_note_existing_show(self):
        """Test adding a note to an existing show"""
        show = 'game of thrones'
        lshow = utils.lunderize(show)
        note = 'returns Summer 2017'
        args = self.parser.parse_args(
            [
                '--database-dir=example',
                'add',
                show,
                '--note',
                note,
            ]
        )
        tracker.tracker(args)
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        self.assertEqual(trackerdb._shows[lshow].notes, note)

    def test_add_existing_show(self):
        """Test trying to add an existing show to the tracker"""
        show = 'game of thrones'
        args = self.parser.parse_args(['--database-dir=example', 'add', show,])
        with self.assertRaises(ShowAlreadyTrackedError):
            tracker.tracker(args)

    def test_add_non_existent_show(self):
        """Test we catch attempting to add a non-existent show"""
        show = 'The Adventures of Moonboy and Patchface'
        args = self.parser.parse_args(['--database-dir=example', 'add', show])
        with self.assertRaises(ShowNotFoundError):
            tracker.tracker(args)

    def test_add_show_same_title_as_film(self):
        """Test we handle the case of getting a response for a film"""
        show = 'fargo'
        args = self.parser.parse_args(['--database-dir=example', 'add', show])
        with self.assertRaises(FoundFilmError):
            tracker.tracker(args)


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
        with self.assertRaises(InvalidUsageError):
            args = self.parser.parse_args(['--list', '--database-dir=does-not-exist'])
            tracker.tracker(args)

# Test subcommands
class DecArgumentTestCase(TempTrackerSetupTestCase):
    """Test case for Dec argument"""

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


class IncArgumentTestCase(TempTrackerSetupTestCase):
    """Test case for Inc argument"""

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


class IncDecShortCodeTestCase(TempTrackerSetupTestCase):
    def setUp(self):
        super().setUp()
        _, trackerdb = tracker.load_all_dbs(self.database_dir)
        trackerdb._shows['game_of_thrones'].short_code = 'GOT'
        trackerdb.write_db()

    def test_inc_using_short_code(self):
        """Test that the tracker can be incremented using a short-code"""
        args = self.parser.parse_args(['--database-dir=example', 'inc', 'got'])
        show = 'Game of Thrones'
        expected_tracked_show = tracker.TrackedShow(
            title=show,
            _next_episode='S07E01',
            short_code='GOT',
        )
        tracker.tracker(args)
        showdb, trackerdb = tracker.load_all_dbs(self.database_dir)
        expected_tracked_show._set_next_prev(showdb)
        self.assertEqual(trackerdb._shows['game_of_thrones'], expected_tracked_show)

    def test_dec_using_short_code(self):
        """Test that the tracker can be decremented using a short-code"""
        args = self.parser.parse_args(['--database-dir=example', 'dec', 'got'])
        show = 'Game of Thrones'
        expected_tracked_show = tracker.TrackedShow(
            title=show,
            _next_episode='S06E09',
            short_code='GOT',
        )
        tracker.tracker(args)
        showdb, trackerdb = tracker.load_all_dbs(self.database_dir)
        expected_tracked_show._set_next_prev(showdb)
        self.assertEqual(trackerdb._shows['game_of_thrones'], expected_tracked_show)


class RemoveShowTestCase(unittest.TestCase):
    """Test case for removing shows and details."""
    @classmethod
    def setUpClass(cls):
        cls.parser = tracker.process_args()
        cls.database_dir = 'example'
        cls.path_to_tracker = os.path.join(cls.database_dir, '.tracker.json')
        cls.path_to_showdb = os.path.join(cls.database_dir, '.showdb.json')

    def test_remove_show(self):
        """Test that we correctly remove a show from the tracker"""
        show = 'game_of_thrones'
        with TemporaryDirectory() as dirname:
            # Some setup
            shutil.copy(self.path_to_tracker, dirname)
            shutil.copy(self.path_to_showdb, dirname)

            sdb, tdb = tracker.load_all_dbs(dirname)
            sdb.path_to_db = os.path.join(dirname, '.showdb.json')
            tdb.path_to_db = os.path.join(dirname, '.tracker.json')
            sdb.write_db()
            tdb.write_db()

            args = self.parser.parse_args(
                [
                    '--database-dir={}'.format(dirname),
                    'rm',
                    show,
                ]
            )
            tracker.tracker(args)
            _, trackerdb = tracker.load_all_dbs(dirname)
            self.assertTrue(show not in trackerdb)

    def test_remove_untracked_show(self):
        """Test that we raise an exception if we try to remove a show that is not tracked"""
        show = 'supernatural'
        with TemporaryDirectory() as dirname:
            # Some setup
            shutil.copy(self.path_to_tracker, dirname)
            shutil.copy(self.path_to_showdb, dirname)

            sdb, tdb = tracker.load_all_dbs(dirname)
            sdb.path_to_db = os.path.join(dirname, '.showdb.json')
            tdb.path_to_db = os.path.join(dirname, '.tracker.json')
            sdb.write_db()
            tdb.write_db()

            args = self.parser.parse_args(
                [
                    '--database-dir={}'.format(dirname),
                    'rm',
                    show,
                ]
            )
            with self.assertRaises(ShowNotTrackedError):
                tracker.tracker(args)

    def test_remove_short_code(self):
        """Test removing a short-code from a show works as expected."""
        show = 'game_of_thrones'
        with TemporaryDirectory() as dirname:
            # Some setup
            shutil.copy(self.path_to_tracker, dirname)
            shutil.copy(self.path_to_showdb, dirname)

            sdb, tdb = tracker.load_all_dbs(dirname)
            sdb.path_to_db = os.path.join(dirname, '.showdb.json')
            tdb.path_to_db = os.path.join(dirname, '.tracker.json')
            # Add a short-code
            tdb._shows[show].short_code = 'GOT'
            sdb.write_db()
            tdb.write_db()

            args = self.parser.parse_args(
                [
                    '--database-dir={}'.format(dirname),
                    'rm',
                    show,
                    '--short-code',
                ]
            )
            tracker.tracker(args)
            _, trackerdb = tracker.load_all_dbs(dirname)
            self.assertIsNone(trackerdb._shows[show].short_code)

    def test_remove_notes(self):
        """Test removing notes from a show works as expected."""
        show = 'game_of_thrones'
        with TemporaryDirectory() as dirname:
            # Some setup
            shutil.copy(self.path_to_tracker, dirname)
            shutil.copy(self.path_to_showdb, dirname)

            sdb, tdb = tracker.load_all_dbs(dirname)
            sdb.path_to_db = os.path.join(dirname, '.showdb.json')
            tdb.path_to_db = os.path.join(dirname, '.tracker.json')
            # Add a note
            tdb._shows[show].notes = 'download light of the seven theme'
            sdb.write_db()
            tdb.write_db()

            args = self.parser.parse_args(
                [
                    '--database-dir={}'.format(dirname),
                    'rm',
                    show,
                    '--note',
                ]
            )
            tracker.tracker(args)
            _, trackerdb = tracker.load_all_dbs(dirname)
            self.assertIsNone(trackerdb._shows[show].notes)


if __name__ == '__main__':
    unittest.main()
