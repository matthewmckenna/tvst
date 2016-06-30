#!/usr/env/python
"""
Utility to keep track of TV shows
"""
# import argparse
import json
# import logging
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
        print('Call _traverse_dict with: {}'.format(self.__dict__))
        return self._traverse_dict(self.__dict__)

    def _traverse_dict(self, instance_dict):
        output = {}
        for key, value in instance_dict.items():
            print('key={} value={}'.format(key, value))
            output[key] = self._traverse(key, value)
        return output

    def _traverse(self, key, value):
        print('In _traverse:')
        if isinstance(value, ToDictMixin):
            print('isinstance ToDictMixin')
            return value.to_dict()
        elif isinstance(value, dict):
            print('isinstance dict')
            return self._traverse_dict(value)
        elif isinstance(value, list):
            print('isinstance list')
            return [self._traverse(key, i) for i in value]
        elif hasattr(value, '__dict__'):
            print('hasattr __dict__')
            return self._traverse_dict(value.__dict__)
        else:
            print('else return value: {}'.format(value))
            return value


class JSONMixin:
    @classmethod
    def from_json(cls, data):
        print('cls={} data={}'.format(cls, data))
        kwargs = json.loads(data)
        print('kwargs={}'.format(kwargs))
        return cls(**kwargs)

    def to_json(self, indent=4, sort_keys=True):
        return json.dumps(self.to_dict(), indent=indent, sort_keys=sort_keys)


class ShowNotTrackedError(TrackerError):
    pass


class Season:
    """Represent a season of a TV show"""
    def __init__(self, episodes):
        self.episodes = []
        self.episodes_this_season = len(episodes)


class Episode:
    def __init__(self, episode=1, season=1, title=None, ratings=None):
        if ratings is None:
            ratings = {}
        self.episode = episode
        self.season = season
        self.title = None
        self.ratings = ratings


class Show(ToDictMixin, JSONMixin):
    """Represent various details of a show.

    Available attributes:
        next
    """
    def __init__(self, title, short_code=None, **episode_details):
        self.title = title
        self.lunder_title = lunderise(title)
        self.next = Episode()
        self.previous = Episode()
        self.short_code = short_code
        self.available_on = None
        self.status = None

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
    testing()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
