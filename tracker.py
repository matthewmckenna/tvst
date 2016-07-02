#!/usr/env/python
"""
Utility to keep track of TV shows
"""
# import argparse
import json
# import logging
import requests
import sys


# from utils import ToDictMixin, JSONMixin  # TODO: Move these classes
from parse_next_episode import titleise, lunderise  # TODO: Place this in a utils package

# TODO: Add command line arguments
# TODO: Add logging
# TODO: Should a show be an object?
# TODO: Retrieve IMDB ratings
# TODO: Retrieve IGN ratings
# TODO: Retrieve episode synopsis

# TODO: Move exceptions into another module
class TrackerError(Exception):
    pass

# Taken from https://github.com/bslatkin/effectivepython
class ToDictMixin:
    def to_dict(self):
        # print('Call _traverse_dict with: {}'.format(self.__dict__))
        return self._traverse_dict(self.__dict__)

    def _traverse_dict(self, instance_dict):
        output = {}
        for key, value in instance_dict.items():
            # print('key={} value={}'.format(key, value))
            output[key] = self._traverse(key, value)
        return output

    def _traverse(self, key, value):
        # print('In _traverse:')
        if isinstance(value, ToDictMixin):
            # print('isinstance ToDictMixin')
            return value.to_dict()
        elif isinstance(value, dict):
            # print('isinstance dict')
            return self._traverse_dict(value)
        elif isinstance(value, list):
            # print('isinstance list')
            return [self._traverse(key, i) for i in value]
        elif hasattr(value, '__dict__'):
            # print('hasattr __dict__')
            return self._traverse_dict(value.__dict__)
        else:
            # print('else return value: {}'.format(value))
            return value


class JSONMixin:
    @classmethod
    def from_json(cls, data):
        # print('cls={} data={}'.format(cls, data))
        kwargs = json.loads(data)
        # print('kwargs={}'.format(kwargs))
        return cls(**kwargs)

    def to_json(self, indent=4, sort_keys=True):
        return json.dumps(self.to_dict(), indent=indent, sort_keys=sort_keys)


class ShowNotTrackedError(TrackerError):
    pass


class Season:
    """Represent a season of a TV show"""
    def __init__(self):
        self._episodes = []
        self.episodes_this_season = 0

    def add_episode(self, episode):
        """Add an episode object to self._episodes"""
        self._episodes.append(episode)

    def construct_episode(self, season, episode_details):
        return Episode(season, episode_details)

    def build_season(self, details):
        """Build a season of episodes"""
        season = int(details['Season'])
        for episode in details['Episodes']:
            # ep = self.construct_episode(season, episode)
            self.add_episode(self.construct_episode(season, episode))

        # Update the number of episodes this season
        self.episodes_this_season = len(self._episodes)

    def __getitem__(self, index):
        return self._episodes[index]

    def __iter__(self):
        return iter(self._episodes)

    def __len__(self):
        return len(self._episodes)


class Episode:
    def __init__(self, season, episode_details):
        self.episode = int(episode_details['Episode'])
        self.title = episode_details['Title']
        self.season = season
        try:
            rating = float(episode_details['imdbRating'])
        except ValueError:
            # Rating may come through as 'N/A' if episode has not aired
            rating = None

        self.ratings = {'imdb': rating}


class Show:
    """Represent various details of a show.

    Available attributes:
        next
    """
    def __init__(self, title=None, short_code=None):
        self.title = title
        self.ltitle = lunderise(title)
        self._seasons = []
        self.next = None
        self.previous = None
        self.short_code = short_code

    def get_season_details(self, season):
        """Make API request with season information"""
        payload = {'t': self.title, 'season': season}
        with requests.Session() as s:
            response = s.get('http://www.omdbapi.com', params=payload)

        # TODO: Add error checking to response object
        return response.json()

    def populate_seasons(self, update_title=False):
        # Get first season information so that we have the total number of
        # seasons available
        # IO
        season_details = self.get_season_details(season=1)
        total_seasons = int(season_details['totalSeasons'])
        self.add_season(season_details)

        # IO
        if total_seasons > 1:
            for season in range(2, total_seasons+1):
                season_details = self.get_season_details(season=season)
                self.add_season(season_details)

        # TODO: Wrong place to do this
        # Update the show title
        if update_title:
            self.title = season_details['Title']

    def add_season(self, season_details):
        s = Season()
        s.build_season(season_details)
        self._seasons.append(s)

    # def __getitem__(self, index):
    #     return self._seasons[index]


class ShowDatabase(ToDictMixin, JSONMixin):
    def __init__(self):
        self._shows = {}

    def add_show(self, show):
        show.populate_seasons()
        self._shows[show.ltitle] = show

# supernatural._seasons[0]._episodes[0].rating['imdb']
# supernatural.next.
    # def update(self, from_file=True):
    #     if from_file:
    #         self.next['season'], self.next['episode'] = show_update()


# read next_episode.txt
# compile a list of shows
# for show in shows: show should be lunderised
# init

# game_of_thrones = Show('Game of Thrones')
# query = 'game of thrones'
# show = getattr(sys.modules[__name__], query)
def test_update_database():
    shows = ['Game of Thrones', 'Silicon Valley']
    show_db = ShowDatabase()
    for show in shows:
        show_db.add_show(Show(show))

    with open('db_test.json', 'w') as f:
        json.dump(show_db.to_dict(), f, indent=2, sort_keys=True)

class Tracker:
    """Provided methods to read current tracker information.

    Available methods:
        next_episode:
    """
    def __init__(self, path_to_tracker):
        self.path_to_tracker = path_to_tracker
        # FIXME: I don't like doing a read in init
        try:
            with open(self.path_to_tracker, 'r') as f:
                self.tracker = json.load(f)
        except FileNotFoundError:
            # TODO: Add some logging
            # print('I/O error(errno={0}): {1}'.format(e.errno, e.strerror))
            raise

    # TODO: Make this function work for next and previous episode
    def get_episode_details(self, show, verbose=False, which='next'):
        """Return the next episode for the show provided."""
        try:
            details = self.tracker['shows'][show]
        except KeyError:
            raise ShowNotTrackedError

        try:
            details = details[which]
        except KeyError:
            return 'No {} episode information available'.format(which)

        if verbose:
            msg = ''.join('{}: {}\n'.format(key.capitalize(), value) for key, value in details.items())
        else:
            msg = '{} episode for {}: S{:02d} E{:02d}'.format(
                which.capitalize(),
                titleise(show.split()),
                details['season'],
                details['episode'],
            )

        return msg

    def inc_episode(self, show):
        """Increment the current episode number."""
        try:
            details = self.tracker['shows'][show]
        except KeyError:
            raise ShowNotTrackedError

        for which in ('next', 'previous'):
            details[which]['episode'] += 1

        # TODO: Validate episodes


    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.path_to_tracker)


def process_args():
    """Process command line arguments."""
    pass


def testing():
    """Test function to incrementally build utility."""
    t = Tracker('sample.json')
    print(t.next_episode('supernatural'))
    print(t.next_episode('supernatural', verbose=True))
    print(t)


def main(args):
    """Main entry point for this utility"""
    # testing()
    test_update_database()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
