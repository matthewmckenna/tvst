# import datetime
import json
import os
# from tempfile import NamedTemporaryFile, TemporaryDirectory
import unittest

import tracker
import utils


# TODO: DatabaseTestCase
# TODO: ShowDatabaseTestCase
# TODO: TrackerDatabaseTestCase
# TODO: Separate utils test cases into another test module

# class TrackerTestCase(unittest.TestCase):
#     """Test case for Tracker class"""
#     def setUp(self):
#         pass
#
#     def tearDown(self):
#         pass
#
#     def test_good_init(self):
#         """Test that self.path_to_tracker is correctly initialised"""
#         t = tracker.Tracker('./test.json')
#         self.assertEqual(t.path_to_tracker, './test.json')
#
#     def test_no_file_exists(self):
#         """Test that Tracker correctly raises an IOError"""
#         with self.assertRaises(FileNotFoundError):
#             tracker.Tracker('./does_not_exist.json')
#
#     def test_next_episode_non_verbose(self):
#         """Test that the non-verbose output is as expected."""
#         t = tracker.Tracker('./test.json')
#         expected_msg = 'Next episode for Supernatural: S05 E22'
#         self.assertEqual(t.get_episode_details('supernatural'), expected_msg)
#
#     def test_previous_episode_non_verbose(self):
#         """Test that the non-verbose output is as expected."""
#         t = tracker.Tracker('./test.json')
#         expected_msg = 'Previous episode for Supernatural: S05 E21'
#         self.assertEqual(t.get_episode_details('supernatural', which='previous'), expected_msg)
#
#     def test_next_episode_no_such_show(self):
#         """Test that we raise a ShowNotTrackedError when the show is not being tracked."""
#         t = tracker.Tracker('./test.json')
#         with self.assertRaises(tracker.ShowNotTrackedError):
#             t.get_episode_details('soopernatural')


class GoodEpisodeInitTestCase(unittest.TestCase):
    """Test case for Episode class"""
    def setUp(self):
        with open('got_s01_response.json', 'r') as f:
            response = json.load(f)
        episode_details = utils.extract_episode_details(
            season=1,
            episode_response=response['Episodes'][0],
        )
        self.episode = tracker.Episode(**episode_details)

    def test_good_episode_title(self):
        """Test that we build a good episode object with good input data"""
        self.assertEqual(self.episode.title, 'Winter Is Coming')

    def test_good_episode_number(self):
        """Test that we build an episode with a good episode number"""
        self.assertEqual(self.episode.episode, 1)

    def test_good_season_number(self):
        """Test we build an episode with a good season number"""
        self.assertEqual(self.episode.season, 1)

    def test_good_rating(self):
        """Test we build an episode with a good rating"""
        self.assertEqual(self.episode.ratings['imdb'], 8.9)

    # def test_bad_episode_title(self):
    #     raise NotImplementedError


class SeasonTestCase(unittest.TestCase):
    """Test case for Season class"""
    def setUp(self):
        with open('got_s01_response.json', 'r') as f:
            self.response = json.load(f)

    def test_construct_episode(self):
        """Test that we correctly construct an episode"""
        s = tracker.Season()

        episode_details = utils.extract_episode_details(
            season=1,
            episode_response=self.response['Episodes'][0],
        )

        self.assertIsInstance(
            s.construct_episode(episode_details),
            tracker.Episode,
        )

    def test_add_episode(self):
        """Test that we correctly add an episode."""
        s = tracker.Season()

        episode_details = utils.extract_episode_details(
            season=1,
            episode_response=self.response['Episodes'][0],
        )

        episode = s.construct_episode(episode_details)

        s.add_episode(episode)

        self.assertEqual(s[0], episode)

    def test_build_season(self):
        """Test that the construction of a season works as expected"""
        s = tracker.Season()
        s.build_season(self.response)
        self.assertEqual(s.episodes_this_season, 10)

    def test_get_season_finale(self):
        """Test that indexing into a season returns the correct episode."""
        s = tracker.Season()
        s.build_season(self.response)
        self.assertEqual(s[9].episode, 10)

    def test_season_len(self):
        """Test the __len__ method is implemented correctly"""
        s = tracker.Season()
        s.build_season(self.response)
        self.assertEqual(len(s), 10)


class ShowDetailsTestCase(unittest.TestCase):
    """Test case for ShowDetails class"""
    def setUp(self):
        self.s = 'Game of Thrones'
        self.show = tracker.Show(self.s, short_code='GOT')

    def test_good_show_title(self):
        self.assertEqual(self.show.title, self.s)

    def test_good_request_title(self):
        self.assertEqual(self.show.request_title, 'game of thrones')

    def test_good_lunder_title(self):
        """Test that we correctly lunderize the title"""
        self.assertEqual(self.show.ltitle, 'game_of_thrones')

    def test_good_short_code_provided(self):
        """Test that the short code is correctly set"""
        self.assertEqual(self.show.short_code, 'GOT')

    def test_good_short_code_not_provided(self):
        """Test that the short code is None if not provided"""
        s = tracker.Show('Game of Thrones')
        self.assertEqual(s.short_code, None)

    def test_show_with_colon_in_title(self):
        """Test that a show with a colon in the is correctly sanitized."""
        show_title = 'American Crime Story: The People v. O.J. Simpson'
        s = tracker.Show(show_title)
        self.assertEqual(s.request_title, 'american crime story')


class ShowTestCase(unittest.TestCase):
    """Test case for Show object and its methods"""
    def test_good_seasons_attribute(self):
        """Test that the _seasons attribute is initially set"""
        show = tracker.Show('Game of Thrones')
        self.assertIsInstance(show._seasons, list)

    def test_add_season(self):
        with open('got_s01_response.json', 'r') as f:
            response = json.load(f)

        show = tracker.Show('Game of Thrones')
        show.add_season(response)
        self.assertIsInstance(show._seasons[0], tracker.Season)


class TrackedShowTestCase(unittest.TestCase):
    """Test case for a Tracked show class"""
    def test_split_season_episode_from_string(self):
        """Test that we correctly extract a season and episode from a string"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S06E10'
        )
        self.assertEqual(
            tracked_show._get_season_episode_from_str(),
            (6, 10),
        )

    def test_split_season_episode_from_string_single_digits(self):
        """Test that we correctly extract a season and episode from a string"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S1E3'
        )
        self.assertEqual(
            tracked_show._get_season_episode_from_str(),
            (1, 3),
        )

    def test_bad_next_episode_string(self):
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='0103'
        )
        with self.assertRaises(tracker.SeasonEpisodeParseError):
            tracked_show._get_season_episode_from_str()

    def test_good_next_init(self):
        """Test that we set up a next attribute"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S06E10'
        )
        self.assertEqual(tracked_show.next, None)

    def test_good_previous_init(self):
        """Test that we set up a previous attribute"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S06E10'
        )
        self.assertEqual(tracked_show.prev, None)


class TrackedShowPrevNextEpisodeTestCase(unittest.TestCase):
    """Test case for .prev and .next attributes of a Tracked Show"""
    @classmethod
    def setUpClass(cls):
        # cls.testdir = os.path.join(os.path.expanduser('~'), 'showtest1')
        # cls.database = tracker.ShowDatabase(cls.testdir, watchlist_path='test_watchlist.txt')
        # cls.database = tracker.load_database(os.path.join('.', '.test_showdb.json'))
        cls.database = tracker.load_database('example/.showdb.json')

    def setUp(self):
        self.tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S06E09'
        )
        self.tracked_show._set_next_prev(self.database)

    def test_inc_episode_good_episode_number(self):
        """Make sure we set the next episode number"""
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.episode, 10)

    def test_inc_episode_good_season_number(self):
        """Make sure we set the next episode season number"""
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.season, 6)

    def test_inc_episode_good_episode_title(self):
        """Make sure we set the next episode title"""
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.title, 'The Winds of Winter')

    def test_inc_episode_good_episode_rating(self):
        """Make sure we set the next episode rating"""
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.ratings['imdb'], 9.9)

    def test_inc_episode_good_prev_episode_number(self):
        """Make sure we set the previous episode number"""
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.prev.episode, 9)

    def test_inc_episode_good_prev_episode_title(self):
        """Make sure we set the previous episode title"""
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.prev.title, 'Battle of the Bastards')

    def test_inc_episode_good_prev_episode_rating(self):
        """Make sure we set the previous episode rating"""
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.prev.ratings['imdb'], 9.9)

    def test_inc_episode_season_finale_next_episode(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.episode, 1)

    def test_inc_episode_season_finale_next_season(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.season, 7)

    def test_inc_episode_season_finale_next_title(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.title, 'Episode #7.1')

    def test_inc_episode_season_finale_next_rating(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.next.ratings['imdb'], None)

    def test_inc_episode_season_finale_prev_episode(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.prev.episode, 10)

    def test_inc_episode_season_finale_prev_season(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.prev.season, 6)

    def test_inc_episode_season_finale_prev_title(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.prev.title, 'The Winds of Winter')

    def test_inc_episode_season_finale_prev_rating(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database)
        self.tracked_show.inc_episode(self.database)
        self.assertEqual(self.tracked_show.prev.ratings['imdb'], 9.9)

    def test_inc_episode_season_finale_prev_title_by_equals_two(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.inc_episode(self.database, by=2)
        self.assertEqual(self.tracked_show.prev.title, 'The Winds of Winter')

    def test_inc_untracked_show(self):
        """Test that we detect trying to increment a show which doesn't exist"""
        tracked_show = tracker.TrackedShow(
            title='The Adventures of Moonboy and Patchface',
            _next_episode='S01E01'
        )
        with self.assertRaises(tracker.ShowNotFoundError):
            tracked_show._set_next_prev(self.database)

    def test_inc_season_out_of_bounds(self):
        """Test that we detect an invalid season"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S08E01'
        )
        with self.assertRaises(tracker.SeasonOutOfBoundsError):
            tracked_show._set_next_prev(self.database)

    def test_inc_episode_out_of_bounds(self):
        """Test that we detect an invalid episode"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S06E11'
        )
        with self.assertRaises(tracker.EpisodeOutOfBoundsError):
            tracked_show._set_next_prev(self.database)

    def test_dec_episode_season_finale_next_rating(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.dec_episode(self.database)
        self.tracked_show.dec_episode(self.database)
        self.assertEqual(self.tracked_show.next.ratings['imdb'], 8.6)

    def test_dec_episode_season_finale_prev_episode(self):
        """Make sure we handle the season boundary transition correctly"""
        self.tracked_show.dec_episode(self.database)
        self.tracked_show.dec_episode(self.database)
        self.assertEqual(self.tracked_show.prev.episode, 6)

    def test_dec_episode_by_7_prev_episode_across_season_boundary(self):
        """Decrement past season boundary, validate good episode"""
        self.tracked_show.dec_episode(self.database, by=8)
        self.assertEqual(self.tracked_show.prev.episode, 10)

    def test_dec_episode_initial_season_premiere_prev_none(self):
        """Decrement past initial season premiere, check prev still None"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S01E01'
        )
        tracked_show._set_next_prev(self.database)
        tracked_show.dec_episode(self.database)
        self.assertEqual(tracked_show.prev, None)

    def test_dec_episode_initial_season_premiere_good_next_episode(self):
        """Decrement past initial season premiere, check valid next episode"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S01E01'
        )
        tracked_show._set_next_prev(self.database)
        tracked_show.dec_episode(self.database)
        self.assertEqual(tracked_show.next.episode, 1)

    def test_dec_episode_by_3_past_initial_season_premiere(self):
        """Decrement past the initial season premiere"""
        tracked_show = tracker.TrackedShow(
            title='Game of Thrones',
            _next_episode='S01E03'
        )
        tracked_show._set_next_prev(self.database)
        tracked_show.dec_episode(self.database, by=3)
        self.assertEqual(tracked_show.next.episode, 1)


class UtilsTestCase(unittest.TestCase):
    """Test case for utility functions"""
    def test_sanitize_multi_word_title(self):
        """Test that we correcly return a lowercase version of the title"""
        title = 'Game of Thrones'
        self.assertEqual(
            utils.sanitize_title(title),
            'game of thrones',
        )

    def test_sanitize_with_colon_in_title(self):
        """Test that we return a title without a colon"""
        title = 'American Horror Story: Hotel'
        self.assertEqual(
            utils.sanitize_title(title),
            'american horror story',
        )

    def test_titleize_multi_word_title(self):
        """Test that we correctly capitalize a multiword title"""
        title = 'game of thrones'
        self.assertEqual(
            utils.titleize(title),
            'Game of Thrones',
        )

    def test_extract_episode_details(self):
        """Test that we correctly form an episode_details dict"""
        with open('got_s01_response.json', 'r') as f:
            response = json.load(f)

        expected_output = {
            'title': 'Winter Is Coming',
            'episode': 1,
            'season': 1,
            'ratings': {'imdb': 8.9}
        }

        episode_details = utils.extract_episode_details(
            season=1,
            episode_response=response['Episodes'][0],
        )

        self.assertDictEqual(expected_output, episode_details)

    def test_extract_episode_details_no_rating(self):
        """Test that we correctly set the rating to None if it is not present"""
        # This episode has not aired at the time of writing this test
        response = {
            "Title": "Episode #7.1",
            "Released": "2017-04-01",
            "Episode": "1",
            "imdbRating": "N/A",
            "imdbID": "tt5654088"
        }

        episode_details = utils.extract_episode_details(
            season=1,
            episode_response=response,
        )

        self.assertEqual(episode_details['ratings']['imdb'], None)


class ProcessWatchlistTestCase(unittest.TestCase):
    """Test case for the ProcessWatchlist class"""

    def setUp(self):
        line = 'game of thrones s01e10 (finale!)'
        self.watchlist = utils.ProcessWatchlist()
        self.NextEpisode = self.watchlist.split_line(line)

    def test_split_line_show_title_correct(self):
        """Test that the show field of the named tuple is set correctly"""
        self.assertEqual(self.NextEpisode.show_title, 'game of thrones')

    def test_split_line_next_episode_correct(self):
        """Test that the next episode string is returned correctly"""
        self.assertEqual(self.NextEpisode.next_episode, 's01e10')

    def test_split_line_notes_correct(self):
        """Test that the notes for the episode are returned correctly"""
        self.assertEqual(self.NextEpisode.notes, 'finale!')

    def test_split_line_no_notes_present(self):
        """Test that we set the notes attribute as None if not provided"""
        line = 'game of thrones s01e10'
        NextEpisode = self.watchlist.split_line(line)
        self.assertEqual(NextEpisode.notes, None)

    def test_split_line_single_title_show(self):
        """Test that the show field is set correctly for a single word title"""
        line = 'house s01e10'
        NextEpisode = self.watchlist.split_line(line)
        self.assertEqual(NextEpisode.show_title, 'house')

    def test_read_watchlist_show_titles_from_file(self):
        """Test that we read multiple show titles from a file"""
        watchlist = utils.ProcessWatchlist('test_watchlist.txt')
        expected_output = ['Game of Thrones', 'Person of Interest']
        for show, expected in zip(watchlist, expected_output):
            self.assertEqual(show.show_title, expected)

    def test_read_watchlist_episode_string_from_file(self):
        """Test that we read multiple show titles from a file"""
        watchlist = utils.ProcessWatchlist('test_watchlist.txt')
        expected_output = ['S06E10', 'S05E01']
        for show, expected in zip(watchlist, expected_output):
            self.assertEqual(show.next_episode, expected)

    def test_read_watchlist_notes_from_file(self):
        """Test that we read multiple show titles from a file"""
        watchlist = utils.ProcessWatchlist('test_watchlist.txt')
        expected_output = [None, 'new season']
        for show, expected in zip(watchlist, expected_output):
            self.assertEqual(show.notes, expected)


if __name__ == '__main__':
    unittest.main()
