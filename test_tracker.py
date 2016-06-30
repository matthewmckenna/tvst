import datetime
import json
import unittest

import tracker


class TrackerTestCase(unittest.TestCase):
    """Test case for Tracker class"""
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_good_init(self):
        """Test that self.path_to_tracker is correctly initialised"""
        t = tracker.Tracker('./test.json')
        self.assertEqual(t.path_to_tracker, './test.json')

    def test_no_file_exists(self):
        """Test that Tracker correctly raises an IOError"""
        with self.assertRaises(FileNotFoundError):
            tracker.Tracker('./does_not_exist.json')

    def test_next_episode_non_verbose(self):
        """Test that the non-verbose output is as expected."""
        t = tracker.Tracker('./test.json')
        expected_msg = 'Next episode for Supernatural: S05 E22'
        self.assertEqual(t.get_episode_details('supernatural'), expected_msg)

    def test_previous_episode_non_verbose(self):
        """Test that the non-verbose output is as expected."""
        t = tracker.Tracker('./test.json')
        expected_msg = 'Previous episode for Supernatural: S05 E21'
        self.assertEqual(t.get_episode_details('supernatural', which='previous'), expected_msg)

    def test_next_episode_no_such_show(self):
        """Test that we raise a ShowNotTrackedError when the show is not being tracked."""
        t = tracker.Tracker('./test.json')
        with self.assertRaises(tracker.ShowNotTrackedError):
            t.get_episode_details('soopernatural')


class ShowTestCase(unittest.TestCase):
    """Test case for Show class and methods"""
    def test_to_dict(self):
        """Test that we convert a Show object to a dict correctly."""
        show = tracker.Show('Supernatural', short_code='SPN')
        expected_dict = {
            'title': 'Supernatural',
            'lunder_title': 'supernatural',
            'short_code': 'SPN',
            'status': None,
            'available_on': None,
            'next': {
                'episode': 1,
                'season': 1,
                'title': None,
                'ratings': {}
            },
            'previous': {
                'episode': 0,
                'season': 0,
                'title': None,
                'ratings': {}
            }
        }
        self.assertDictEqual(show.to_dict(), expected_dict)



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
