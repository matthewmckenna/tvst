#!/usr/env/python
"""
Utility to keep track of TV shows
"""
# import argparse
import datetime
import json
# import logging
import os
import re
import sys

import requests

from exceptions import (
    DatabaseNotFoundError,
    EpisodeOutOfBoundsError,
    FoundFilmError,
    SeasonEpisodeParseError,
    SeasonOutOfBoundsError,
    ShowNotFoundError,
    ShowNotTrackedError,
    # WatchlistNotFoundError,
)
from utils import (
    check_season_bounds,
    Deserializer,
    EncodeShow,
    extract_episode_details,
    lunderize,
    ProcessWatchlist,
    RegisteredSerializable,
    sanitize_title,
    titleize,
)

# TODO: Add command line arguments
# TODO: Add logging
# TODO: Should a show be an object?
# TODO: Retrieve IMDB ratings
# TODO: Retrieve IGN ratings
# TODO: Retrieve episode synopsis


class Season(RegisteredSerializable):
    """Represent a season of a TV show"""
    def __init__(self, episodes_this_season=0, _episodes=None):
        self._episodes = [] if _episodes is None else _episodes
        self.episodes_this_season = 0 if episodes_this_season is None else len(self._episodes)

    def add_episode(self, episode):
        """Add an episode object to self._episodes"""
        self._episodes.append(episode)

    def construct_episode(self, episode_details):
        return Episode(**episode_details)

    def build_season(self, details):
        """Build a season of episodes"""
        season = int(details['Season'])
        for episode in details['Episodes']:
            # ep = self.construct_episode(season, episode)
            episode_details = extract_episode_details(season, episode)
            self.add_episode(self.construct_episode(episode_details))

        # Update the number of episodes this season
        self.episodes_this_season = len(self._episodes)

    def __getitem__(self, index):
        return self._episodes[index]

    def __iter__(self):
        return iter(self._episodes)

    def __len__(self):
        return len(self._episodes)


class Episode(RegisteredSerializable):
    def __init__(self, episode, season, title, ratings):
        self.episode = episode
        self.season = season
        self.title = title
        self.ratings = ratings

    def __repr__(self):
        return '< {self.title} (S{self.season:02d}E{self.episode:02d}) >'.format(
            self=self
        )


class ShowDetails(RegisteredSerializable):
    """Provide basic information about a show.

    Provide access to various title formats and the short_code of
    a Show.
    """
    def __init__(self, title=None, ltitle=None, request_title=None, short_code=None):
        self.title = title
        self.request_title = sanitize_title(title)
        self.ltitle = lunderize(title)
        self.short_code = short_code


class TrackedShow(ShowDetails):
    """Keep track of next and previous episodes of a tracked show.

    Available methods:
        inc_episode
    """
    def __init__(
        self,
        title=None,
        ltitle=None,
        request_title=None,
        next_episode=None,
        notes=None,
        short_code=None,
    ):
        super().__init__(title, ltitle, request_title, short_code)
        self.next = None
        self.notes = notes
        self.previous = None
        self._next_episode = next_episode

        # TODO: Watch out for first episode of a series, prev should be None
        # TODO: I need access to the show_db. Probably better to not set up
        # in init after all
        # if not (self.next and self.prev):
        # if not self.next:
        #     self.set_next_prev()

    def _get_season_episode_from_str(self):
        """Extract a season and episode from a string."""
        pattern = r'[sS](\d{1,2})[eE](\d{1,2})'
        m = re.search(pattern, self._next_episode)

        if not m:
            raise SeasonEpisodeParseError

        season = int(m.group(1))
        episode = int(m.group(2))
        return season, episode

    def _set_next_prev(self, show_database):
        """Set up the next and previous episodes of a TrackedShow"""
        # TODO: Find out the type of show_database[ltitle]._seasons[x-1]._episodes[x-1]
        # If it is a list or a dict then I would be safer making a copy, as opposed
        # to just setting a reference
        print('In _set_next_prev')
        print('type(show_database)={}'.format(type(show_database)))
        print('type(show_database._shows[self.ltitle])={}'.format(type(show_database._shows[self.ltitle])))
        print('type(show_database._shows[self.ltitle]._seasons[season-1])={}'.format(type(show_database._shows[self.ltitle]._seasons[season-1])))
        print('type(show_database._shows[self.ltitle]._seasons[season-1]._episodes[episode-1])={}'.format(type(show_database._shows[self.ltitle]._seasons[season-1]._episodes[episode-1])))
        print('')
        # self.next = show_database._shows[self.ltitle]._seasons[season-1]._episodes[episode-1]



    def inc_episode(self):
        raise NotImplementedError


class Show(ShowDetails):
    """Represent various details of a show.

    Available attributes:
        next
    """
    def __init__(
        self,
        title=None,
        ltitle=None,
        request_title=None,
        short_code=None,
        _seasons=None
    ):
        super().__init__(title, ltitle, request_title, short_code)
        self._seasons = [] if _seasons is None else _seasons

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

        # We got a film of the same name
        if show_details['Type'] == 'movie':
            raise FoundFilmError

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


class Database(RegisteredSerializable):
    """Provide base method for different types of databases"""
    def __init__(self, database_dir=None, watchlist_path=None):
        if database_dir is None:
            database_dir = os.path.join(os.path.expanduser('~'), '.showtracker')
        self.database_dir = database_dir

        self.watchlist_path = watchlist_path

        # TODO: Bad idea to do this in the init
        # self.watchlist = self.read_watchlist()
        # print(type(self.watchlist))

        # Create a directory for the databases to live
        try:
            os.mkdir(self.database_dir)
        except OSError:
            pass  # TODO: Log that the directory already exists

    def write_database(self):
        """Write a ShowDatabase to disk"""
        date_format = '%A %B %d, %Y %H:%M:%S'
        self.last_modified = datetime.datetime.now().strftime(date_format)

        with open(self.path_to_database, 'w', encoding='utf-8') as f:
            # json.dump(self, f, cls=EncodeShow, indent=2, sort_keys=True)
            json.dump(self, f, cls=EncodeShow, sort_keys=True)

    def read_watchlist(self):
        """Read and process a watchlist.

        Read a watchlist and split into show_title, next_episode
        and any notes associated.

        Returns:
            a ProcessWatchlist instance which is an iterator

        Raises:
            WatchlistNotFoundError if a watchlist does not exist
        """
        return ProcessWatchlist(self._watchlist_path)


class ShowDatabase(Database):
    def __init__(
        self,
        database_dir=None,
        path_to_database=None,
        watchlist_path=None,
        _shows=None,
        last_modified=None,
    ):
        super().__init__(database_dir, watchlist_path)
        self._shows = {} if _shows is None else _shows
        self.last_modified = last_modified

        if path_to_database is None:
            path_to_database = os.path.join(self.database_dir, '.showdb.json')

        self.path_to_database = path_to_database

        if not os.path.exists(self.path_to_database):
            self.create_database()

    # TODO: Refactor this method
    def add_show(self, show_title):
        # TODO
        show = Show(show_title)
        # FIXME: Hidden IO
        try:
            show.populate_seasons()
        except FoundFilmError:
            # TODO: Handle this properly
            # Current idea is to go to imdb.com, do a search with request_title
            # Then scrape the response page for *SHOW* (TV Series).
            # Extract the IMDB ID and then perform another search on
            # omdbapi.com with the direct ID
            print('Film found with the same name. Try adding a year with request.')
        else:
            self._shows[show.ltitle] = show

    def create_database(self):
        """Create a show database."""
        watchlist = ProcessWatchlist(self.watchlist_path)
        for show in watchlist:
            # TODO: Refactor to just pass show to add_show()
            self.add_show(show.show_title)


def load_database(path_to_database):
    """Return an existing database"""
    try:
        with open(path_to_database, 'r') as db:
            deserialized_data = json.load(db)
    except FileNotFoundError:
        raise DatabaseNotFoundError
    else:
        deserializer = Deserializer(deserialized_data)
        database = deserializer.deserialize()

    return database


def update_database():
    """Update an existing ShowDatabase.
    """
    # TODO: Locate the database

    # TODO: Rename the database

    # TODO: Get list of existing shows in database

    # TODO: Read watchlist

    # TODO: Combine two lists of shows

    # TODO: Create database

    # TODO: Test database is valid

    # TODO: Write database, and exit


# def update(self, from_file=True):
#     if from_file:
#         self.next['season'], self.next['episode'] = show_update()


# game_of_thrones = Show('Game of Thrones')
# query = 'game of thrones'
# show = getattr(sys.modules[__name__], query)
def test_update_database():
    shows = ['Game of Thrones', 'Silicon Valley']
    show_db = ShowDatabase()
    for show in shows:
        show_db.add_show(Show(show))

    with open('db_test.json', 'w') as f:
        json.dump(show_db, f, cls=EncodeShow, indent=2, sort_keys=True)


def create_tracker(path_to_file):
    """Create a Tracker object."""
    tracker = TrackerDatabase()
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


class TrackerDatabase(Database):
    """Provided methods to read current tracker information.

    Available methods:
        next_episode:
    """
    def __init__(self, database_dir=None):
        super.__init__(database_dir)
        self.path_to_database = os.path.join(self._database_dir, '.tracker.json')
        self._shows = {}

        if os.path.exists(self.path_to_database):
            # Perhaps we should do the load in init?
            self._db = self.load_database()
            self.construct_tracker()
        else:
            self.create_tracker()

    def create_tracker(self):
        """Create a tracker if it does not already exist"""
        watchlist = ProcessWatchlist(self._watchlist)
        for show in watchlist:
            self.add(show)

    def add(self, show):
        tracked_show = TrackedShow(
            title=show.title,
            next_episode=show.next_episode,
            notes=show.notes,
        )
        self._shows[tracked_show.ltitle] = tracked_show

    def _add_next_prev_episode(self, database):
        """Add the next and previous episodes for the tracked show"""
        for show in self._shows:
            season, episode = show._get_season_episode_from_str()

            try:
                show_db = database._shows[show.ltitle]
            except IndexError:
                raise ShowNotFoundError

            if not check_season_bounds(season, episode):
                raise

            try:
                season = show_db._seasons[season-1]
            except IndexError:
                raise SeasonOutOfBoundsError

            try:
                episode = season._episodes[episode-1]
            except IndexError:
                raise EpisodeOutOfBoundsError
            else:
                show._set_next_prev(database)

            # season = database._shows[show.ltitle][season-1][episode-1]
            # database._shows['game_of_thrones']._seasons[1]._episodes[1].title
            # database._shows['game_of_thrones']['_seasons'][1]['_episodes'][1]


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


def main(args):
    """Main entry point for this utility"""
    # test_update_database()
    watchlist = ProcessWatchlist()
    show_database = ShowDatabase()
    tracker = TrackerDatabase()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
