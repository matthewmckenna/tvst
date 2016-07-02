import datetime
import json
import unittest

import tracker


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
        self.episode = tracker.Episode(
            season=1,
            episode_details=response['Episodes'][0],
        )

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

    def test_bad_episode_title(self):
        pass


class SeasonTestCase(unittest.TestCase):
    """Test case for Season class"""
    def setUp(self):
        with open('got_s01_response.json', 'r') as f:
            self.response = json.load(f)

    def construct_episode(self):
        """Test that we correctly construct an episode"""
        s = tracker.Season()

        episode_details = self.response['Episodes'][0]

        self.assertIsInstance(
            s.construct_episode(season=1, episode_details=episode_details),
            tracker.Episode,
        )

    def test_add_episode(self):
        """Test that we correctly add an episode."""
        s = tracker.Season()

        episode_details = self.response['Episodes'][0]

        episode = s.construct_episode(
            season=1,
            episode_details=episode_details
        )

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


class GoodInitShowTestCase(unittest.TestCase):
    """Test case for Show class"""
    def setUp(self):
        s = 'Game of Thrones'
        self.show = tracker.Show(s, short_code='GOT')

    def test_good_show_title(self):
        self.assertEqual(self.show.title, 'Game of Thrones')

    def test_good_lunder_title(self):
        """Test that we correctly lunderize the title"""
        self.assertEqual(self.show.ltitle, 'game_of_thrones')

    def test_good_seasons_attribute(self):
        """Test that the _seasons attribute is initially set"""
        self.assertIsInstance(self.show._seasons, list)

    def test_good_next(self):
        """Test that we set up a next attribute"""
        self.assertEqual(self.show.next, None)

    def test_good_previous(self):
        """Test that we set up a previous attribute"""
        self.assertEqual(self.show.previous, None)

    def test_good_short_code_provided(self):
        """Test that the short code is correctly set"""
        self.assertEqual(self.show.short_code, 'GOT')

    def test_good_short_code_not_provided(self):
        """Test that the short code is None if not provided"""
        s = tracker.Show('Game of Thrones')
        self.assertEqual(s.short_code, None)


class ShowTestCase(unittest.TestCase):
    """Test case for Show object and its methods"""
    def test_add_season(self):
        with open('got_s01_response.json', 'r') as f:
            response = json.load(f)

        show = tracker.Show('Game of Thrones')
        show.add_season(response)
        self.assertIsInstance(show._seasons[0], tracker.Season)



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


def create_good_file():
    """Create a valid JSON file."""
    # print('Starting data dump {}'.format(datetime.datetime.now().strftime("%A %B %d, %Y %H:%M:%S")))
    # datestring = '{}'.format(datetime.datetime.now().strftime("%A %B %d, %Y %H:%M:%S"))
    sample_tracker = {
        'last_modified': 'Tuesday June 28, 2016 15:08:11',
        'shows': {
            'supernatural': {
                'next': {
                    'episode': 22,
                    'season': 5,
                    'title': 'Swan Song',
                    'ratings': {
                        'imdb': 9.7,
                        'ign': 9.0,
                    }
                },
                'previous': {
                    'episode': 21,
                    'season': 5,
                    'title': 'Two Minutes to Midnight',
                    'ratings': {
                        'imdb': 9.4,
                        'ign': 9.1,
                    }
                },
                'status': 'season_ended',
                'short_code': 'spn',
                'available_on': [
                    'download',
                ]
            },
            'game_of_thrones': {
                'next': {
                    'episode': 9,
                    'season': 3,
                    'title': 'The Rains of Castamere',
                    'ratings': {
                        'imdb': 9.7,
                        'ign': 9.9,
                    }
                },
                'previous': {
                    'episode': 8,
                    'season': 3,
                    'title': 'Second Sons',
                    'ratings': {
                        'imdb': 8.9,
                        'ign': 9.0,
                    }
                },
                'status': 'season_ended',
                'short_code': 'got',
                'available_on': [
                    'download',
                    'sky',
                ]
            }
        }
    }

    with open('test.json', 'w') as f:
        json.dump(sample_tracker, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    #create_good_file()
    unittest.main()
