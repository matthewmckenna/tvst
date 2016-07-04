#!/usr/env/python
"""
Utility to keep track of TV shows
"""
# import argparse
import json
# import logging
import os
import re
import sys

import requests

# from utils import ToDictMixin, JSONMixin  # TODO: Move these classes
from exceptions import (
    SeasonEpisodeParseError,
    ShowNotFoundError,
    ShowNotTrackedError,
)
from utils import titleize, lunderize, sanitize_title

# TODO: Add command line arguments
# TODO: Add logging
# TODO: Should a show be an object?
# TODO: Retrieve IMDB ratings
# TODO: Retrieve IGN ratings
# TODO: Retrieve episode synopsis


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


class ShowDetails:
    """Provide basic information about a show.

    Provide access to various title formats and the short_code of
    a Show.
    """
    def __init__(self, title=None, short_code=None):
        self.title = title
        self.request_title = sanitize_title(title)
        self.ltitle = lunderize(title)
        self.short_code = short_code


class TrackedShow(ShowDetails):
    """Keep track of next and previous episodes of a tracked show.

    Available methods:
        inc_episode
    """
    def __init__(self, title=None, next_episode=None, short_code=None, notes=None):
        super().__init__(title, short_code)
        self.next = None
        self.notes = notes
        self.previous = None
        self._next_episode = next_episode

    def _get_season_episode_from_str(self):
        """Extract a season and episode from a string."""
        pattern = r'\w{1}(\d{1,2})'*2
        m = re.search(pattern, self._next_episode)

        if not m:
            raise SeasonEpisodeParseError

        season = int(m.group(1))
        episode = int(m.group(2))
        return season, episode

    def inc_episode(self):
        raise NotImplementedError


class Show(ShowDetails):
    """Represent various details of a show.

    Available attributes:
        next
    """
    def __init__(self, title=None, short_code=None):
        super().__init__(title, short_code)
        self._seasons = []

    def request_show_info(self, season=None):
        """Make API request with season information"""
        if season:
            payload = {'t': self.request_title, 'season': season}
        else:
            payload = {'t': self.request_title}

        with requests.Session() as s:
            response = s.get('http://www.omdbapi.com', params=payload)

        response.raise_for_status()

        # TODO: Add error checking to response object
        return response.json()

    def populate_seasons(self, update_title=True):
        # IO
        show_details = self.request_show_info()

        # Response value is returned as a string
        if show_details['Response'] == 'False':
            raise ShowNotFoundError

        total_seasons = int(show_details['totalSeasons'])

        # IO
        for season in range(1, total_seasons+1):
            season_details = self.request_show_info(season=season)
            self.add_season(season_details)

        # TODO: Wrong place to do this
        # Update the show title
        if update_title:
            self.title = season_details['Title']

    def add_season(self, season_details):
        s = Season()
        s.build_season(season_details)
        self._seasons.append(s)


class ShowDatabase(ToDictMixin, JSONMixin):
    def __init__(self):
        self._shows = {}

    def add_show(self, show):
        show.populate_seasons()
        self._shows[show.ltitle] = show

    def create_database_from_file(self, path_to_file='./watchlist.txt'):
        """Create a show database."""
        tracked_shows = parse_watch_list(path_to_file)
        for show in tracked_shows:
            # TODO: Refactor to just pass show to add_show()
            self.add_show(Show(show))

    def write_database(self, path_to_database=None):
        """Write a ShowDatabse to disk"""
        if path_to_database is None:
            path_to_database = os.path.join(
                os.path.expanduser('~'),
                '.showdb'
            )
        # TODO: Tidy this up
        with open(os.path.join(path_to_database, '.showdb.json'), 'w') as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)


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


# def create_database_from_file(path_to_file='./watchlist.txt'):
#     """Create a show database."""
#     show_db = ShowDatabase()
#     tracked_shows = parse_watch_list(path_to_file)
#     for show in tracked_shows:
#         # TODO: Refactor to just pass show to add_show()
#         show_db.add_show(Show(show))
#
#     return show_db




def create_tracker(path_to_file):
    """Create a Tracker object."""
    tracker = Tracker()
    for show in tracked_shows:
        tracker.add(
            TrackedShow(
                title=show.title,
                next_episode=show.next_episode,
                notes=show.notes,
            )
        )
    return tracker


def update_tracker_title(tracker, database):
    """Update the title attribute in the tracker with those from
    the ShowDatabase.
    """
    for show in tracker:
        show.title = database[show.ltitle]['title']


def add_next_prev_episode(tracker, database):
    """Add the next and previous episodes for the tracked show"""
    for show in tracker:
        season, episode = show._get_season_episode_from_str(show._next_episode)
        season = database[show.ltitle][season-1][episode-1]
        try:
            season = database[show.ltitle][season-1]
        except IndexError:
            print('Season out of bounds')

        try:
            episode = season[episode-1]
        except:
            episode = x


class Database:
    """Provide base method for different types of databases"""
    def __init__(self, path_to_database=None):
        self._path_to_database = path_to_database
        self.shows = {}


class Tracker:
    """Provided methods to read current tracker information.

    Available methods:
        next_episode:
    """
    def __init__(self, database=None, path_to_tracker='.tracker.json'):
        # self._database_exists = False
        self._tracker_exists = False
        self._tracker_dir = os.path.join(
            os.path.expanduser('~'),
            '.showtracker'
        )
        self.path_to_tracker = os.path.join(self._tracker_dir, path_to_tracker)
        # self.path_to_database = os.path.join(self._tracker_dir, '.showdb.json')
        self.shows = {}
        # self.last_modified = None

        # Create a directory for the databases to live
        try:
            os.mkdir(self._tracker_dir)
        except OSError:
            # print('Directory already exists')
            pass

        if os.path.exists(self.path_to_tracker):
            # Perhaps we should do the load in init?
            self.load_tracker()
        else:
            self.create_tracker()

    def create_tracker(self):
        """Create a tracker if it does not already exist"""
        raise NotImplementedError

    def load_database(self):
        """Return an existing database"""
        if self._database_exists:
            with open(self.path_to_database, 'r') as db:
                return json.load(db)

    def load_tracker(self):
        """Load an existing tracker"""
        with open(self.path_to_tracker, 'r') as t:
            self.shows = json.load(t)

    def populate_tracker(self):
        self.shows

def tracker_main():
    """Main function for the module"""
    tracker = Tracker(database)
    # WARNING: This can only be consumed once!
    tracked_shows = tracker.get_tracked_shows_from_file()
    if tracker.database_exists:
        database = tracker.load_database()
    else:
        database = create_database()

    if tracker.tracker_exists:
        tracker.load_tracker()
    else:
        tracker.create_tracker()

        # FIXME: I don't like doing a read in init
        try:
            with open(self.path_to_database, 'r') as f:
                self._showdb = json.load(f)
        except FileNotFoundError:
            pass
        try:
            with open(self.path_to_tracker, 'r') as f:
                self.tracker = json.load(f)
        except FileNotFoundError:
            # TODO: Add some logging
            # print('I/O error(errno={0}): {1}'.format(e.errno, e.strerror))
            pass

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
                titleize(show.split()),
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

    def __iter__(self):
        return iter(self._shows)

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
