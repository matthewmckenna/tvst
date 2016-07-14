# import datetime
import json
# import os
# from tempfile import NamedTemporaryFile, TemporaryDirectory
import unittest

import tracker
import utils


# TODO: TrackedShowTestCase
# TODO: More tests for ShowTestCase
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

    @unittest.skip('Not implemented yet')
    def test_bad_episode_title(self):
        raise NotImplementedError


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


# TODO: Move title and short code checks to a ShowDetailsTestCase
class GoodInitShowTestCase(unittest.TestCase):
    """Test case for Show class"""
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

    def test_good_seasons_attribute(self):
        """Test that the _seasons attribute is initially set"""
        self.assertIsInstance(self.show._seasons, list)

    # TODO: Move these tests to that of a TrackedShow
    # def test_good_next(self):
    #     """Test that we set up a next attribute"""
    #     self.assertEqual(self.show.next, None)
    #
    # def test_good_previous(self):
    #     """Test that we set up a previous attribute"""
    #     self.assertEqual(self.show.previous, None)

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
    def test_add_season(self):
        with open('got_s01_response.json', 'r') as f:
            response = json.load(f)

        show = tracker.Show('Game of Thrones')
        show.add_season(response)
        self.assertIsInstance(show._seasons[0], tracker.Season)


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

    # TODO: Remove get_season_episode_from_str
    def test_split_season_episode_from_string(self):
        """Test that we correctly extract a season and episode from a string"""
        s = 'S06E10'
        self.assertEqual(
            utils.get_season_episode_from_str(s),
            (6, 10),
        )

    def test_split_season_episode_from_string_single_digits(self):
        """Test that we correctly extract a season and episode from a string"""
        s = 'S1E3'
        self.assertEqual(
            utils.get_season_episode_from_str(s),
            (1, 3),
        )


class ProcessWatchlistTestCase(unittest.TestCase):
    """Test case for the ProcessWatchlist class"""

    def setUp(self):
        line = 'game of thrones s01e10 (finale!)'
        self.watchlist = utils.ProcessWatchlist()
        self.NextEpisode = self.watchlist.split_line(line)

    def test_split_line_show_title_correct(self):
        """Test that the show field of the named tuple is set correctly"""
        self.assertEqual(self.NextEpisode.show, 'game of thrones')

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
        self.assertEqual(NextEpisode.show, 'house')

    def test_read_watchlist_show_titles_from_file(self):
        """Test that we read multiple show titles from a file"""
        watchlist = utils.ProcessWatchlist('./test_watchlist.txt')
        expected_output = ['Game of Thrones', 'Person of Interest']
        for show, expected in zip(watchlist, expected_output):
            self.assertEqual(show.show, expected)

    def test_read_watchlist_episode_string_from_file(self):
        """Test that we read multiple show titles from a file"""
        watchlist = utils.ProcessWatchlist('./test_watchlist.txt')
        expected_output = ['S06E10', 'S05E01']
        for show, expected in zip(watchlist, expected_output):
            self.assertEqual(show.next_episode, expected)

    def test_read_watchlist_notes_from_file(self):
        """Test that we read multiple show titles from a file"""
        watchlist = utils.ProcessWatchlist('./test_watchlist.txt')
        expected_output = [None, 'new season']
        for show, expected in zip(watchlist, expected_output):
            self.assertEqual(show.notes, expected)


# class ShowTestCase(unittest.TestCase):
#     """Test case for Show class and methods"""
#     def test_to_dict(self):
#         """Test that we convert a Show object to a dict correctly."""
#         show = tracker.Show('Supernatural', short_code='SPN')
#         expected_dict = {
#             'title': 'Supernatural',
#             'lunder_title': 'supernatural',
#             'short_code': 'SPN',
#             'status': None,
#             'available_on': None,
#             'next': {
#                 'episode': 1,
#                 'season': 1,
#                 'title': None,
#                 'ratings': {}
#             },
#             'previous': {
#                 'episode': 0,
#                 'season': 0,
#                 'title': None,
#                 'ratings': {}
#             }
#         }
#         self.assertDictEqual(show.to_dict(), expected_dict)


if __name__ == '__main__':
    # create_good_file()
    unittest.main()
